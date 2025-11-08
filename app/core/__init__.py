"""Core domain layer.

This layer contains:
- Domain entities and value objects
- Use cases (application business logic)
- Repository and service interfaces (ports)

The core is independent of infrastructure and frameworks.
"""

from app.core.domain import (
    AgentResponse,
    CBTExercise,
    ChatContext,
    Conversation,
    CrisisEvent,
    CrisisIndicators,
    Document,
    EmbeddingVector,
    MentalHealthAssessment,
    Message,
    RetrievedDocument,
    SearchQuery,
    SessionStatus,
    SeverityLevel,
    TherapeuticGoal,
    ThoughtRecord,
    User,
    UserProgress,
)
from app.core.ports import (
    IAgentOrchestrationService,
    ICBTExerciseRepository,
    IConversationRepository,
    ICrisisDetectionService,
    ICrisisEventRepository,
    IDocumentRepository,
    IEmbeddingService,
    ILLMService,
    IMessageRepository,
    IUserProgressRepository,
    IUserRepository,
)

__all__ = [
    # Domain entities
    "User",
    "Conversation",
    "Message",
    "CrisisEvent",
    "Document",
    "CBTExercise",
    "UserProgress",
    # Enums
    "SeverityLevel",
    "SessionStatus",
    # Value objects
    "EmbeddingVector",
    "ChatContext",
    "TherapeuticGoal",
    "CrisisIndicators",
    "AgentResponse",
    "SearchQuery",
    "RetrievedDocument",
    "MentalHealthAssessment",
    "ThoughtRecord",
    # Repository ports
    "IUserRepository",
    "IConversationRepository",
    "IMessageRepository",
    "ICrisisEventRepository",
    "IDocumentRepository",
    "ICBTExerciseRepository",
    "IUserProgressRepository",
    # Service ports
    "ILLMService",
    "IEmbeddingService",
    "ICrisisDetectionService",
    "IAgentOrchestrationService",
]
