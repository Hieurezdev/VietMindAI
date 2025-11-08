"""Service interfaces (ports) for external dependencies.

These define contracts for services that the core domain needs from the infrastructure layer.
"""

from abc import ABC, abstractmethod

from app.core.domain.value_objects import AgentResponse, ChatContext, CrisisIndicators


class ILLMService(ABC):
    """Interface for LLM service."""

    @abstractmethod
    async def generate_text(
        self,
        content: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system_instruction: str | None = None,
    ) -> str:
        """Generate text completion."""
        ...

    @abstractmethod
    async def generate_with_thinking_model(
        self,
        content: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_instruction: str | None = None,
    ) -> str:
        """Generate text with thinking model for complex reasoning."""
        ...


class IEmbeddingService(ABC):
    """Interface for embedding service."""

    @abstractmethod
    async def embed_text_async(
        self, text: str, task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> list[float]:
        """Generate embedding for text."""
        ...

    @abstractmethod
    async def embed_query_async(self, query: str) -> list[float]:
        """Generate embedding for search query."""
        ...

    @abstractmethod
    async def embed_document_async(self, document: str) -> list[float]:
        """Generate embedding for document."""
        ...


class ICrisisDetectionService(ABC):
    """Interface for crisis detection service."""

    @abstractmethod
    async def analyze_message(self, message: str, context: ChatContext) -> CrisisIndicators:
        """Analyze message for crisis indicators."""
        ...

    @abstractmethod
    async def assess_severity(self, indicators: CrisisIndicators) -> str:
        """Assess severity level from indicators."""
        ...


class IAgentOrchestrationService(ABC):
    """Interface for agent orchestration service."""

    @abstractmethod
    async def route_message(
        self, message: str, context: ChatContext, user_id: str
    ) -> AgentResponse:
        """Route message to appropriate agent and get response."""
        ...

    @abstractmethod
    async def get_agent_by_name(self, agent_name: str) -> object:
        """Get specific agent instance by name."""
        ...
