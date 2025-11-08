"""Repository interfaces (ports) for hexagonal architecture.

These define the contracts that infrastructure adapters must implement.
The core domain depends only on these abstractions, not on concrete implementations.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.entities import (
    CBTExercise,
    Conversation,
    CrisisEvent,
    Document,
    Message,
    User,
    UserProgress,
)
from app.core.domain.value_objects import EmbeddingVector, SearchQuery


class IUserRepository(ABC):
    """Repository interface for User entities."""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user."""
        ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update existing user."""
        ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """Delete user by ID."""
        ...

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """List all users with pagination."""
        ...


class IConversationRepository(ABC):
    """Repository interface for Conversation entities."""

    @abstractmethod
    async def create(self, conversation: Conversation) -> Conversation:
        """Create a new conversation."""
        ...

    @abstractmethod
    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        """Get conversation by ID."""
        ...

    @abstractmethod
    async def get_by_user_id(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Conversation]:
        """Get all conversations for a user."""
        ...

    @abstractmethod
    async def update(self, conversation: Conversation) -> Conversation:
        """Update existing conversation."""
        ...

    @abstractmethod
    async def delete(self, conversation_id: UUID) -> bool:
        """Delete conversation by ID."""
        ...


class IMessageRepository(ABC):
    """Repository interface for Message entities."""

    @abstractmethod
    async def create(self, message: Message) -> Message:
        """Create a new message."""
        ...

    @abstractmethod
    async def get_by_id(self, message_id: UUID) -> Message | None:
        """Get message by ID."""
        ...

    @abstractmethod
    async def get_by_conversation_id(
        self, conversation_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Message]:
        """Get all messages in a conversation."""
        ...

    @abstractmethod
    async def update(self, message: Message) -> Message:
        """Update existing message."""
        ...

    @abstractmethod
    async def delete(self, message_id: UUID) -> bool:
        """Delete message by ID."""
        ...


class ICrisisEventRepository(ABC):
    """Repository interface for CrisisEvent entities."""

    @abstractmethod
    async def create(self, event: CrisisEvent) -> CrisisEvent:
        """Create a new crisis event."""
        ...

    @abstractmethod
    async def get_by_id(self, event_id: UUID) -> CrisisEvent | None:
        """Get crisis event by ID."""
        ...

    @abstractmethod
    async def get_by_user_id(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[CrisisEvent]:
        """Get all crisis events for a user."""
        ...

    @abstractmethod
    async def get_unresolved(self, skip: int = 0, limit: int = 100) -> list[CrisisEvent]:
        """Get all unresolved crisis events."""
        ...

    @abstractmethod
    async def update(self, event: CrisisEvent) -> CrisisEvent:
        """Update existing crisis event."""
        ...


class IDocumentRepository(ABC):
    """Repository interface for Document entities."""

    @abstractmethod
    async def create(self, document: Document) -> Document:
        """Create a new document."""
        ...

    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> Document | None:
        """Get document by ID."""
        ...

    @abstractmethod
    async def update(self, document: Document) -> Document:
        """Update existing document."""
        ...

    @abstractmethod
    async def delete(self, document_id: UUID) -> bool:
        """Delete document by ID."""
        ...

    @abstractmethod
    async def search_by_embedding(
        self, query: SearchQuery, embedding: EmbeddingVector
    ) -> list[Document]:
        """Search documents by embedding similarity."""
        ...

    @abstractmethod
    async def search_by_text(self, query_text: str, limit: int = 10) -> list[Document]:
        """Search documents by text (full-text search)."""
        ...


class ICBTExerciseRepository(ABC):
    """Repository interface for CBTExercise entities."""

    @abstractmethod
    async def create(self, exercise: CBTExercise) -> CBTExercise:
        """Create a new CBT exercise."""
        ...

    @abstractmethod
    async def get_by_id(self, exercise_id: UUID) -> CBTExercise | None:
        """Get CBT exercise by ID."""
        ...

    @abstractmethod
    async def get_by_type(self, exercise_type: str, limit: int = 10) -> list[CBTExercise]:
        """Get CBT exercises by type."""
        ...

    @abstractmethod
    async def get_by_difficulty(self, difficulty: str, limit: int = 10) -> list[CBTExercise]:
        """Get CBT exercises by difficulty level."""
        ...

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> list[CBTExercise]:
        """List all CBT exercises."""
        ...


class IUserProgressRepository(ABC):
    """Repository interface for UserProgress entities."""

    @abstractmethod
    async def create(self, progress: UserProgress) -> UserProgress:
        """Create a new progress record."""
        ...

    @abstractmethod
    async def get_by_id(self, progress_id: UUID) -> UserProgress | None:
        """Get progress record by ID."""
        ...

    @abstractmethod
    async def get_by_user_id(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[UserProgress]:
        """Get all progress records for a user."""
        ...

    @abstractmethod
    async def get_by_exercise_id(self, user_id: UUID, exercise_id: UUID) -> list[UserProgress]:
        """Get progress records for a specific exercise."""
        ...

    @abstractmethod
    async def update(self, progress: UserProgress) -> UserProgress:
        """Update existing progress record."""
        ...
