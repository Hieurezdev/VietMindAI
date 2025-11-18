"""Pydantic schemas for memory API endpoints."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for chat request with optional user_id."""

    content: str = Field(..., min_length=1, description="User message content")
    user_id: Optional[UUID] = Field(None, description="User ID (None creates new user)")
    session_id: Optional[UUID] = Field(None, description="Session ID for conversation continuity")


class MemoryContext(BaseModel):
    """Schema for memory context response."""

    content: str = Field(..., description="Memory content")
    role: Optional[str] = Field(None, description="Role (for short-term memories)")
    turn: Optional[int] = Field(None, description="Turn number (for short-term memories)")
    type: Optional[str] = Field(None, description="Memory type (for long-term memories)")
    importance: Optional[float] = Field(None, description="Importance score (for long-term memories)")
    similarity: Optional[float] = Field(None, description="Similarity score (for searches)")


class ChatResponse(BaseModel):
    """Schema for chat response with user state and context."""

    user_id: UUID = Field(..., description="User ID (newly created or existing)")
    session_id: UUID = Field(..., description="Session ID")
    is_new_user: bool = Field(..., description="Whether this is a new user")
    short_term_memories: List[MemoryContext] = Field(..., description="Recent conversation context")
    long_term_memories: List[MemoryContext] = Field(..., description="Relevant long-term context")
    message: str = Field(..., description="Response message")


class ShortTermMemoryCreate(BaseModel):
    """Schema for creating short-term memory."""

    user_id: UUID = Field(..., description="User ID")
    content: str = Field(..., min_length=1, description="Memory content")
    role: str = Field(default="user", description="Role: user, assistant, or system")
    session_id: Optional[UUID] = Field(None, description="Session ID")
    turn_number: int = Field(default=0, ge=0, description="Turn number in conversation")
    expires_in_hours: Optional[int] = Field(24, ge=1, le=168, description="Hours until expiry (max 7 days)")


class ShortTermMemoryResponse(BaseModel):
    """Schema for short-term memory response (ChatHistory)."""

    message_id: UUID = Field(..., description="Message ID")
    user_id: UUID = Field(..., description="User ID")
    session_id: UUID = Field(..., description="Session ID")
    content: str = Field(..., description="Memory content")
    role: str = Field(..., description="Role")
    turn_number: int = Field(..., description="Turn number")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")

    model_config = {"from_attributes": True}


class LongTermMemoryCreate(BaseModel):
    """Schema for creating long-term memory."""

    user_id: UUID = Field(..., description="User ID")
    content: str = Field(..., min_length=1, description="Memory content")
    memory_type: str = Field(default="general", description="Type: preference, fact, context, goal, etc.")
    summary: str = Field(default="", description="Brief summary")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score (0.0 to 1.0)")


class LongTermMemoryResponse(BaseModel):
    """Schema for long-term memory response (VectorMemory)."""

    memory_id: UUID = Field(..., description="Memory ID")
    user_id: UUID = Field(..., description="User ID")
    content: str = Field(..., description="Memory content")
    memory_type: str = Field(..., description="Memory type")
    summary: str = Field(..., description="Summary")
    importance: float = Field(..., description="Importance score")
    access_count: int = Field(..., description="Number of times accessed")
    last_accessed: Optional[datetime] = Field(None, description="Last access timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class MemorySearchQuery(BaseModel):
    """Schema for memory search."""

    user_id: UUID = Field(..., description="User ID")
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=5, ge=1, le=50, description="Maximum results")


class MemorySearchResult(BaseModel):
    """Schema for memory search result."""

    memory: MemoryContext = Field(..., description="Memory data")
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similarity score")


class UserResponse(BaseModel):
    """Schema for user response."""

    user_id: UUID = Field(..., description="User ID")
    name: Optional[str] = Field(None, description="User name")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_interaction: datetime = Field(..., description="Last interaction timestamp")
    short_term_count: int = Field(..., description="Number of short-term memories")
    long_term_count: int = Field(..., description="Number of long-term memories")


class ConversationContextResponse(BaseModel):
    """Schema for full conversation context."""

    user_id: UUID = Field(..., description="User ID")
    short_term: List[MemoryContext] = Field(..., description="Recent conversation history")
    long_term: List[MemoryContext] = Field(..., description="Relevant long-term context")
