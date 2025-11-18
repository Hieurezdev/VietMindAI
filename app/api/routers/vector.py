"""API endpoints for vector store operations."""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.vector import (
    ChunkBatchCreate,
    ChunkBatchResponse,
    ChunkCreate,
    ChunkListQuery,
    ChunkListResponse,
    ChunkResponse,
    ChunkSearchQuery,
    ChunkSearchResult,
    ChunkUpdate,
)
from app.infra.db.session import get_session
from app.services.vector_store import get_vector_store_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vector", tags=["vector"])


@router.post(
    "/chunks",
    response_model=ChunkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new knowledge chunk",
)
async def create_chunk(
    chunk_data: ChunkCreate,
    session: AsyncSession = Depends(get_session),
) -> ChunkResponse:
    """Create a new knowledge chunk with embedding.

    Args:
        chunk_data: Chunk creation data.
        session: Database session.

    Returns:
        Created knowledge chunk.

    Raises:
        HTTPException: If creation fails.
    """
    try:
        vector_service = get_vector_store_service()
        chunk = await vector_service.add_chunk(
            session=session,
            content=chunk_data.content,
            headers=chunk_data.headers,
            summary=chunk_data.summary,
            keywords=chunk_data.keywords,
            chunk_type=chunk_data.type,
        )
        await session.commit()
        return ChunkResponse.from_db_model(chunk)

    except Exception as e:
        logger.error(f"Failed to create chunk: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chunk: {str(e)}",
        )


@router.post(
    "/chunks/batch",
    response_model=ChunkBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple knowledge chunks in batch",
)
async def create_chunks_batch(
    batch_data: ChunkBatchCreate,
    session: AsyncSession = Depends(get_session),
) -> ChunkBatchResponse:
    """Create multiple knowledge chunks in batch.

    Args:
        batch_data: Batch creation data.
        session: Database session.

    Returns:
        Created knowledge chunks.

    Raises:
        HTTPException: If batch creation fails.
    """
    try:
        vector_service = get_vector_store_service()

        # Convert Pydantic models to dict
        chunks_data = [chunk.model_dump() for chunk in batch_data.chunks]

        chunks = await vector_service.add_chunks_batch(
            session=session,
            chunks_data=chunks_data,
        )
        await session.commit()

        return ChunkBatchResponse(
            chunks=[ChunkResponse.from_db_model(chunk) for chunk in chunks],
            count=len(chunks),
        )

    except Exception as e:
        logger.error(f"Failed to create chunks in batch: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chunks in batch: {str(e)}",
        )


@router.post(
    "/chunks/search",
    response_model=List[ChunkSearchResult],
    summary="Search for similar knowledge chunks",
)
async def search_chunks(
    search_query: ChunkSearchQuery,
    session: AsyncSession = Depends(get_session),
) -> List[ChunkSearchResult]:
    """Search for similar knowledge chunks using semantic similarity.

    Args:
        search_query: Search query parameters.
        session: Database session.

    Returns:
        List of search results with similarity scores.

    Raises:
        HTTPException: If search fails.
    """
    try:
        vector_service = get_vector_store_service()
        results = await vector_service.search_similar(
            session=session,
            query=search_query.query,
            limit=search_query.limit,
            chunk_type=search_query.type,
            similarity_threshold=search_query.similarity_threshold,
        )

        return [
            ChunkSearchResult(
                chunk=ChunkResponse.from_db_model(chunk),
                similarity=similarity,
            )
            for chunk, similarity in results
        ]

    except Exception as e:
        logger.error(f"Failed to search chunks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search chunks: {str(e)}",
        )


@router.get(
    "/chunks/{chunk_uuid}",
    response_model=ChunkResponse,
    summary="Get a knowledge chunk by UUID",
)
async def get_chunk(
    chunk_uuid: UUID,
    session: AsyncSession = Depends(get_session),
) -> ChunkResponse:
    """Get a knowledge chunk by UUID.

    Args:
        chunk_uuid: UUID of the chunk.
        session: Database session.

    Returns:
        Knowledge chunk.

    Raises:
        HTTPException: If chunk not found or retrieval fails.
    """
    try:
        vector_service = get_vector_store_service()
        chunk = await vector_service.get_chunk_by_uuid(session, chunk_uuid)

        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chunk not found: {chunk_uuid}",
            )

        return ChunkResponse.from_db_model(chunk)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chunk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chunk: {str(e)}",
        )


@router.patch(
    "/chunks/{chunk_uuid}",
    response_model=ChunkResponse,
    summary="Update a knowledge chunk",
)
async def update_chunk(
    chunk_uuid: UUID,
    update_data: ChunkUpdate,
    session: AsyncSession = Depends(get_session),
) -> ChunkResponse:
    """Update a knowledge chunk.

    If content is updated, a new embedding will be generated.

    Args:
        chunk_uuid: UUID of the chunk to update.
        update_data: Update data.
        session: Database session.

    Returns:
        Updated knowledge chunk.

    Raises:
        HTTPException: If chunk not found or update fails.
    """
    try:
        vector_service = get_vector_store_service()
        chunk = await vector_service.update_chunk(
            session=session,
            chunk_uuid=chunk_uuid,
            content=update_data.content,
            headers=update_data.headers,
            summary=update_data.summary,
            keywords=update_data.keywords,
            chunk_type=update_data.type,
        )

        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chunk not found: {chunk_uuid}",
            )

        await session.commit()
        return ChunkResponse.from_db_model(chunk)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update chunk: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update chunk: {str(e)}",
        )


@router.delete(
    "/chunks/{chunk_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a knowledge chunk",
)
async def delete_chunk(
    chunk_uuid: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a knowledge chunk.

    Args:
        chunk_uuid: UUID of the chunk to delete.
        session: Database session.

    Raises:
        HTTPException: If chunk not found or deletion fails.
    """
    try:
        vector_service = get_vector_store_service()
        deleted = await vector_service.delete_chunk(session, chunk_uuid)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chunk not found: {chunk_uuid}",
            )

        await session.commit()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete chunk: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chunk: {str(e)}",
        )


@router.get(
    "/chunks",
    response_model=ChunkListResponse,
    summary="List knowledge chunks",
)
async def list_chunks(
    type: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> ChunkListResponse:
    """List knowledge chunks with optional filtering.

    Args:
        type: Filter by chunk type (optional).
        limit: Maximum number of results (default: 100).
        offset: Number of results to skip (default: 0).
        session: Database session.

    Returns:
        List of knowledge chunks with pagination info.

    Raises:
        HTTPException: If listing fails.
    """
    try:
        vector_service = get_vector_store_service()

        chunks = await vector_service.list_chunks(
            session=session,
            chunk_type=type,
            limit=limit,
            offset=offset,
        )

        total = await vector_service.count_chunks(session=session, chunk_type=type)

        return ChunkListResponse(
            chunks=[ChunkResponse.from_db_model(chunk) for chunk in chunks],
            total=total,
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error(f"Failed to list chunks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list chunks: {str(e)}",
        )
