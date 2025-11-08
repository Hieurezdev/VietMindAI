"""Domain entities for the mental health AI system.

Entities are objects with identity that persist over time.
They represent the core business concepts.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    """Crisis severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SessionStatus(str, Enum):
    """Chat session status."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ESCALATED = "escalated"


class User(BaseModel):
    """User entity representing a system user."""

    id: UUID = Field(default_factory=uuid4)
    email: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        from_attributes = True


class Conversation(BaseModel):
    """Conversation entity representing a chat session."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    title: str | None = None
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        from_attributes = True


class Message(BaseModel):
    """Message entity representing a single message in a conversation."""

    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    agent_name: str | None = None  # Which agent handled this message
    tokens_used: int | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        from_attributes = True


class CrisisEvent(BaseModel):
    """Crisis event entity for tracking critical situations."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    conversation_id: UUID | None = None
    message_id: UUID | None = None
    severity: SeverityLevel
    description: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    escalated: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        from_attributes = True


class Document(BaseModel):
    """Document entity for knowledge base."""

    id: UUID = Field(default_factory=uuid4)
    title: str
    content: str
    source: str | None = None
    category: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    embedding: list[float] | None = None  # 768-dim for gemini-embedding-001
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        from_attributes = True


class CBTExercise(BaseModel):
    """CBT exercise entity for therapeutic interventions."""

    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    exercise_type: str  # e.g., "thought_record", "behavioral_activation"
    instructions: str
    estimated_duration_minutes: int
    difficulty_level: str  # "beginner", "intermediate", "advanced"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        from_attributes = True


class UserProgress(BaseModel):
    """User progress tracking entity."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    exercise_id: UUID | None = None
    activity_type: str  # "exercise", "conversation", "mindfulness"
    progress_data: dict[str, str] = Field(default_factory=dict)
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    notes: str | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True
