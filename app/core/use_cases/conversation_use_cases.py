"""Use cases for conversation management."""

import logging
from datetime import datetime
from uuid import UUID

from app.core.domain.entities import Conversation, Message, SessionStatus
from app.core.domain.value_objects import AgentResponse, ChatContext
from app.core.ports.repositories import (
    IConversationRepository,
    ICrisisEventRepository,
    IMessageRepository,
)
from app.core.ports.services import IAgentOrchestrationService, ICrisisDetectionService

logger = logging.getLogger(__name__)


class ConversationUseCases:
    """Use cases for conversation management."""

    def __init__(
        self,
        conversation_repo: IConversationRepository,
        message_repo: IMessageRepository,
        crisis_event_repo: ICrisisEventRepository,
        agent_service: IAgentOrchestrationService,
        crisis_detection_service: ICrisisDetectionService,
    ) -> None:
        """Initialize conversation use cases.

        Args:
            conversation_repo: Repository for conversations.
            message_repo: Repository for messages.
            crisis_event_repo: Repository for crisis events.
            agent_service: Agent orchestration service.
            crisis_detection_service: Crisis detection service.
        """
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.crisis_event_repo = crisis_event_repo
        self.agent_service = agent_service
        self.crisis_detection_service = crisis_detection_service

    async def start_conversation(self, user_id: UUID, title: str | None = None) -> Conversation:
        """Start a new conversation.

        Args:
            user_id: User ID.
            title: Optional conversation title.

        Returns:
            Conversation: Created conversation.
        """
        conversation = Conversation(
            user_id=user_id,
            title=title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            status=SessionStatus.ACTIVE,
        )

        created = await self.conversation_repo.create(conversation)
        logger.info(f"Started conversation {created.id} for user {user_id}")
        return created

    async def send_message(
        self, conversation_id: UUID, user_id: UUID, content: str
    ) -> tuple[Message, AgentResponse]:
        """Send a message in a conversation and get agent response.

        Args:
            conversation_id: Conversation ID.
            user_id: User ID.
            content: Message content.

        Returns:
            tuple[Message, AgentResponse]: User message and agent response.

        Raises:
            ValueError: If conversation not found or not active.
        """
        # Verify conversation exists and is active
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if conversation.status != SessionStatus.ACTIVE:
            raise ValueError(f"Conversation {conversation_id} is not active")

        # Save user message
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )
        await self.message_repo.create(user_message)

        # Get conversation context
        recent_messages = await self.message_repo.get_by_conversation_id(
            conversation_id, skip=0, limit=10
        )
        context = ChatContext(
            recent_messages=[msg.content for msg in recent_messages[-5:]],
            detected_topics=[],
            crisis_indicators=[],
        )

        # Check for crisis indicators
        crisis_indicators = await self.crisis_detection_service.analyze_message(content, context)

        if crisis_indicators.is_crisis:
            logger.warning(
                f"Crisis detected in conversation {conversation_id}: "
                f"severity={crisis_indicators.severity_score}"
            )
            # Handle crisis (will be implemented in crisis use cases)
            context = ChatContext(
                recent_messages=context.recent_messages,
                detected_topics=context.detected_topics,
                crisis_indicators=[
                    ind
                    for ind, val in crisis_indicators.dict().items()
                    if val is True and ind != "confidence_score"
                ],
            )

        # Get agent response
        agent_response = await self.agent_service.route_message(content, context, str(user_id))

        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=agent_response.content,
            agent_name=agent_response.agent_name,
            tokens_used=agent_response.tokens_used,
            metadata=agent_response.metadata,
        )
        await self.message_repo.create(assistant_message)

        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        await self.conversation_repo.update(conversation)

        logger.info(
            f"Message processed in conversation {conversation_id} "
            f"by agent {agent_response.agent_name}"
        )

        return user_message, agent_response

    async def get_conversation_history(
        self, conversation_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[Message]:
        """Get conversation history.

        Args:
            conversation_id: Conversation ID.
            skip: Number of messages to skip.
            limit: Maximum number of messages to return.

        Returns:
            list[Message]: List of messages.
        """
        return await self.message_repo.get_by_conversation_id(conversation_id, skip, limit)

    async def end_conversation(self, conversation_id: UUID) -> Conversation:
        """End a conversation.

        Args:
            conversation_id: Conversation ID.

        Returns:
            Conversation: Updated conversation.

        Raises:
            ValueError: If conversation not found.
        """
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        conversation.status = SessionStatus.COMPLETED
        conversation.completed_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()

        updated = await self.conversation_repo.update(conversation)
        logger.info(f"Ended conversation {conversation_id}")
        return updated

    async def get_user_conversations(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> list[Conversation]:
        """Get all conversations for a user.

        Args:
            user_id: User ID.
            skip: Number of conversations to skip.
            limit: Maximum number of conversations to return.

        Returns:
            list[Conversation]: List of conversations.
        """
        return await self.conversation_repo.get_by_user_id(user_id, skip, limit)
