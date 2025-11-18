"""Database models for 2-tier memory system: Chat History and Vector Memories."""

import uuid
from datetime import datetime, timezone
from typing import List

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class User(Base):
    """User model for tracking conversation participants."""

    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    last_interaction: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_users_created_at", "created_at"),
        Index("ix_users_last_interaction", "last_interaction"),
    )

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id})>"


# ============================================================================
# TABLE A: CHAT_HISTORY (Short-term Memory)
# ============================================================================
class ChatHistory(Base):
    """Bảng A: Lưu đoạn hội thoại gần đây (hot conversation).

    Mục đích:
    - Query để lấy context cho câu trả lời tiếp theo
    - Lưu trữ ngắn hạn (session-based hoặc time-limited)
    - Truy xuất nhanh theo user_id và session_id
    """

    __tablename__ = "chat_history"

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="User ID",
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Session ID to group conversation turns",
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Role: user, assistant, system",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message content",
    )

    turn_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Turn number in conversation",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Auto-expire after 24 hours (configurable)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When this chat history should expire",
    )

    __table_args__ = (
        Index("ix_chat_history_user_session", "user_id", "session_id"),
        Index("ix_chat_history_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ChatHistory(user={self.user_id}, session={self.session_id}, turn={self.turn_number})>"


# ============================================================================
# TABLE B: VECTOR_MEMORIES (Long-term Episodic Memory)
# ============================================================================
class VectorMemory(Base):
    """Bảng C: Lưu kiến thức cũ và đoạn chat lịch sử đã được tóm tắt.

    Mục đích:
    - Lưu trữ các episode/sự kiện trong quá khứ
    - Semantic search để tìm kiếm theo ngữ nghĩa
    - Lưu trữ lâu dài các insights và patterns từ conversation

    Examples:
    - "User mentioned feeling stressed about work deadlines on 2024-01-15"
    - "User found deep breathing helpful during panic attack"
    - "Conversation about coping with social anxiety at work"
    """

    __tablename__ = "vector_memories"

    memory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="User ID",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Summarized content or insight from conversation",
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="Brief summary (5-20 words)",
    )

    memory_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="episodic",
        comment="Type: episodic, insight, pattern, event, etc.",
    )

    # Tags for quick filtering (comma-separated)
    tags: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="Comma-separated tags (e.g., 'work,stress,anxiety')",
    )

    # Importance score for prioritization
    importance: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
        comment="Importance score (0.0 to 1.0)",
    )

    # Embedding for semantic search
    embedding: Mapped[List[float]] = mapped_column(
        Vector(768),
        nullable=False,
        comment="768-dimensional embedding from Gemini",
    )

    # Context metadata
    source_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Original session ID if created from chat consolidation",
    )

    event_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the event/episode occurred (if applicable)",
    )

    # Access tracking
    access_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of times this memory was accessed",
    )

    last_accessed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time this memory was accessed",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_vector_memories_user_id", "user_id"),
        Index("ix_vector_memories_memory_type", "memory_type"),
        Index("ix_vector_memories_importance", "importance"),
        Index("ix_vector_memories_created_at", "created_at"),
        Index("ix_vector_memories_event_date", "event_date"),
        # Vector similarity search index
        Index(
            "ix_vector_memories_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<VectorMemory(user={self.user_id}, type={self.memory_type}, importance={self.importance})>"


# ============================================================================
# Keep KnowledgeChunk for general knowledge base (not user-specific)
# ============================================================================
class KnowledgeChunk(Base):
    """General knowledge base (mental health information, not user-specific)."""

    __tablename__ = "knowledge_chunks"

    uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    headers: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="Comma-separated headers or metadata",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Main content of the knowledge chunk",
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="Summary of the content",
    )

    keywords: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
        comment="Array of keywords",
    )

    type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
        comment="Type/category of the knowledge chunk",
    )

    embedding: Mapped[List[float]] = mapped_column(
        Vector(768),
        nullable=False,
        comment="768-dimensional embedding vector from Gemini",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_knowledge_chunks_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("ix_knowledge_chunks_type", "type"),
        Index("ix_knowledge_chunks_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<KnowledgeChunk(uuid={self.uuid}, type={self.type})>"
