"""Use cases for crisis management."""

import logging
from datetime import datetime
from uuid import UUID

from app.core.domain.entities import CrisisEvent, SeverityLevel
from app.core.domain.value_objects import ChatContext
from app.core.ports.repositories import ICrisisEventRepository
from app.core.ports.services import ICrisisDetectionService

logger = logging.getLogger(__name__)


class CrisisUseCases:
    """Use cases for crisis detection and management."""

    def __init__(
        self,
        crisis_event_repo: ICrisisEventRepository,
        crisis_detection_service: ICrisisDetectionService,
    ) -> None:
        """Initialize crisis use cases.

        Args:
            crisis_event_repo: Repository for crisis events.
            crisis_detection_service: Crisis detection service.
        """
        self.crisis_event_repo = crisis_event_repo
        self.crisis_detection_service = crisis_detection_service

    async def detect_crisis(
        self,
        user_id: UUID,
        message: str,
        context: ChatContext,
        conversation_id: UUID | None = None,
        message_id: UUID | None = None,
    ) -> tuple[bool, CrisisEvent | None]:
        """Detect crisis in a message.

        Args:
            user_id: User ID.
            message: Message content.
            context: Chat context.
            conversation_id: Optional conversation ID.
            message_id: Optional message ID.

        Returns:
            tuple[bool, CrisisEvent | None]: Whether crisis detected and event if created.
        """
        # Analyze message for crisis indicators
        indicators = await self.crisis_detection_service.analyze_message(message, context)

        if not indicators.is_crisis:
            return False, None

        # Determine severity level
        severity_str = await self.crisis_detection_service.assess_severity(indicators)
        severity = SeverityLevel(severity_str)

        # Create crisis event
        crisis_event = CrisisEvent(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            severity=severity,
            description=f"Crisis detected: {', '.join(context.crisis_indicators)}",
            escalated=severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL],
        )

        created_event = await self.crisis_event_repo.create(crisis_event)

        logger.warning(
            f"Crisis event {created_event.id} created for user {user_id} "
            f"with severity {severity.value}"
        )

        return True, created_event

    async def resolve_crisis(
        self, event_id: UUID, resolved_by: str, notes: str | None = None
    ) -> CrisisEvent:
        """Mark a crisis event as resolved.

        Args:
            event_id: Crisis event ID.
            resolved_by: Who resolved the crisis (e.g., "system", "human_operator").
            notes: Optional resolution notes.

        Returns:
            CrisisEvent: Updated crisis event.

        Raises:
            ValueError: If crisis event not found.
        """
        event = await self.crisis_event_repo.get_by_id(event_id)
        if not event:
            raise ValueError(f"Crisis event {event_id} not found")

        event.resolved_at = datetime.utcnow()
        event.resolved_by = resolved_by

        if notes:
            event.metadata["resolution_notes"] = notes

        updated_event = await self.crisis_event_repo.update(event)
        logger.info(f"Crisis event {event_id} resolved by {resolved_by}")

        return updated_event

    async def escalate_crisis(self, event_id: UUID, escalation_notes: str) -> CrisisEvent:
        """Escalate a crisis event.

        Args:
            event_id: Crisis event ID.
            escalation_notes: Notes about escalation.

        Returns:
            CrisisEvent: Updated crisis event.

        Raises:
            ValueError: If crisis event not found.
        """
        event = await self.crisis_event_repo.get_by_id(event_id)
        if not event:
            raise ValueError(f"Crisis event {event_id} not found")

        event.escalated = True
        event.metadata["escalation_notes"] = escalation_notes
        event.metadata["escalated_at"] = datetime.utcnow().isoformat()

        updated_event = await self.crisis_event_repo.update(event)
        logger.warning(f"Crisis event {event_id} escalated")

        return updated_event

    async def get_user_crisis_history(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> list[CrisisEvent]:
        """Get crisis history for a user.

        Args:
            user_id: User ID.
            skip: Number of events to skip.
            limit: Maximum number of events to return.

        Returns:
            list[CrisisEvent]: List of crisis events.
        """
        return await self.crisis_event_repo.get_by_user_id(user_id, skip, limit)

    async def get_unresolved_crises(self, skip: int = 0, limit: int = 50) -> list[CrisisEvent]:
        """Get all unresolved crisis events.

        Args:
            skip: Number of events to skip.
            limit: Maximum number of events to return.

        Returns:
            list[CrisisEvent]: List of unresolved crisis events.
        """
        return await self.crisis_event_repo.get_unresolved(skip, limit)
