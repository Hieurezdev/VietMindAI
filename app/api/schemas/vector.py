"""Pydantic schemas for vector store API endpoints."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChunkCreate(BaseModel):
    """Schema for creating a new knowledge chunk."""

    content: str = Field(..., description="Main content of the knowledge chunk")
    headers: List[str] = Field(default_factory=list, description="List of headers or metadata")
    summary: str = Field(default="", description="Brief summary of the content")
    keywords: List[str] = Field(default_factory=list, description="List of keywords")
    type: str = Field(default="", description="Type/category of the chunk")


class ChunkUpdate(BaseModel):
    """Schema for updating an existing knowledge chunk."""

    content: Optional[str] = Field(None, description="New content")
    headers: Optional[List[str]] = Field(None, description="New headers")
    summary: Optional[str] = Field(None, description="New summary")
    keywords: Optional[List[str]] = Field(None, description="New keywords")
    type: Optional[str] = Field(None, description="New type/category")


class ChunkResponse(BaseModel):
    """Schema for knowledge chunk response."""

    uuid: UUID = Field(..., description="Unique identifier")
    headers: List[str] = Field(..., description="Headers or metadata")
    content: str = Field(..., description="Main content")
    summary: str = Field(..., description="Summary")
    keywords: List[str] = Field(..., description="Keywords")
    type: str = Field(..., description="Type/category")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}

    @classmethod
    def from_db_model(cls, chunk: "KnowledgeChunk") -> "ChunkResponse":
        """Convert database model to response schema.

        Args:
            chunk: KnowledgeChunk database model.

        Returns:
            ChunkResponse: Pydantic response model.
        """
        return cls(
            uuid=chunk.uuid,
            headers=chunk.headers.split(",") if chunk.headers else [],
            content=chunk.content,
            summary=chunk.summary,
            keywords=chunk.keywords or [],
            type=chunk.type,
            created_at=chunk.created_at,
            updated_at=chunk.updated_at,
        )


class ChunkSearchQuery(BaseModel):
    """Schema for searching knowledge chunks."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(default=5, ge=1, le=100, description="Maximum number of results")
    type: Optional[str] = Field(None, description="Filter by chunk type")
    similarity_threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0-1)",
    )


class ChunkSearchResult(BaseModel):
    """Schema for search result with similarity score."""

    chunk: ChunkResponse = Field(..., description="Knowledge chunk data")
    similarity: float = Field(..., description="Similarity score (0-1)")


class ChunkListQuery(BaseModel):
    """Schema for listing knowledge chunks."""

    type: Optional[str] = Field(None, description="Filter by chunk type")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")


class ChunkListResponse(BaseModel):
    """Schema for list of knowledge chunks."""

    chunks: List[ChunkResponse] = Field(..., description="List of knowledge chunks")
    total: int = Field(..., description="Total number of chunks matching filter")
    limit: int = Field(..., description="Limit applied")
    offset: int = Field(..., description="Offset applied")


class ChunkBatchCreate(BaseModel):
    """Schema for batch creating knowledge chunks."""

    chunks: List[ChunkCreate] = Field(
        ..., min_length=1, max_length=100, description="List of chunks to create (max 100)"
    )


class ChunkBatchResponse(BaseModel):
    """Schema for batch creation response."""

    chunks: List[ChunkResponse] = Field(..., description="Created knowledge chunks")
    count: int = Field(..., description="Number of chunks created")
