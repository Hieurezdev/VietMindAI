"""Agent orchestration service using Google ADK agents."""

import logging
import time
from typing import Any

from google.adk.agents import Agent

from app.core.domain.value_objects import AgentResponse, ChatContext
from app.core.ports.services import IAgentOrchestrationService

logger = logging.getLogger(__name__)


class AgentOrchestrationService(IAgentOrchestrationService):
    """Service for orchestrating ADK agents."""

    def __init__(self, root_agent: Agent) -> None:
        """Initialize agent orchestration service.

        Args:
            root_agent: The root ADK agent that routes to sub-agents.
        """
        self._root_agent = root_agent
        self._agents_registry: dict[str, Agent] = {}
        logger.info("AgentOrchestrationService initialized")

    def register_agent(self, name: str, agent: Agent) -> None:
        """Register an agent in the registry.

        Args:
            name: Agent name.
            agent: Agent instance.
        """
        self._agents_registry[name] = agent
        logger.info(f"Registered agent: {name}")

    async def route_message(
        self, message: str, context: ChatContext, user_id: str
    ) -> AgentResponse:
        """Route message to appropriate agent and get response.

        Args:
            message: User message.
            context: Chat context.
            user_id: User ID.

        Returns:
            AgentResponse: Agent's response.
        """
        start_time = time.time()

        try:
            # Create invocation context (ADK API may vary by version)
            # For simplicity, we'll use a dict-like structure that ADK accepts
            context_state: dict[str, Any] = {
                "user_input": message,
                "user_id": user_id,
                "recent_messages": context.recent_messages,
                "crisis_indicators": context.crisis_indicators,
            }

            # Run root agent (it will route to appropriate sub-agent)
            response_content = ""
            agent_name = "root_agent"
            tokens_used = 0

            # Note: ADK API may need adjustment based on version
            # This is a simplified version
            async for event in self._root_agent.run_async(context_state):  # type: ignore
                if hasattr(event, "is_final_response") and event.is_final_response():
                    if hasattr(event, "content") and event.content:
                        if hasattr(event.content, "parts") and event.content.parts:
                            text = event.content.parts[0].text
                            if text:
                                response_content = str(text)
                    # Try to extract agent name from event metadata
                    if hasattr(event, "metadata") and event.metadata:
                        agent_name = event.metadata.get("agent_name", agent_name)

            processing_time_ms = int((time.time() - start_time) * 1000)

            agent_response = AgentResponse(
                content=response_content or "Xin lỗi, tôi không thể xử lý yêu cầu này.",
                agent_name=agent_name,
                confidence=1.0,
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms,
                metadata={"user_id": user_id},
            )

            logger.info(
                f"Message routed through {agent_name}, processing time: {processing_time_ms}ms"
            )

            return agent_response

        except Exception as e:
            logger.error(f"Agent orchestration failed: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Return error response
            return AgentResponse(
                content="Xin lỗi, đã xảy ra lỗi trong quá trình xử lý. Vui lòng thử lại.",
                agent_name="error_handler",
                confidence=0.0,
                tokens_used=0,
                processing_time_ms=processing_time_ms,
                metadata={"error": str(e)},
            )

    async def get_agent_by_name(self, agent_name: str) -> Any:
        """Get specific agent instance by name.

        Args:
            agent_name: Agent name.

        Returns:
            Agent instance or None if not found.
        """
        if agent_name == "root":
            return self._root_agent

        return self._agents_registry.get(agent_name)
