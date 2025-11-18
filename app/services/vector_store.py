"""Vector store service for knowledge chunk operations with pgvector."""

import logging
import uuid
from typing import List, Optional

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models import KnowledgeChunk
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing knowledge chunks with vector embeddings.

    Provides CRUD operations and semantic search capabilities using pgvector.
    """

    def __init__(self) -> None:
        """Initialize vector store service."""
        self._embedding_service = get_embedding_service()
        logger.info("Vector store service initialized")

    async def add_chunk(
        self,
        session: AsyncSession,
        content: str,
        headers: Optional[List[str]] = None,
        summary: str = "",
        keywords: Optional[List[str]] = None,
        chunk_type: str = "ki�n th�c",
    ) -> KnowledgeChunk:
        """Add a new knowledge chunk to the vector store.

        Args:
            session: Database session.
            content: Main content of the chunk.
            headers: List of headers/metadata (optional).
            summary: Summary of the content (optional).
            keywords: List of keywords (optional).
            chunk_type: Type/category of the chunk (default: "ki�n th�c").

        Returns:
            KnowledgeChunk: Created knowledge chunk with embedding.

        Raises:
            Exception: If chunk creation or embedding generation fails.
        """
        try:
            # Generate embedding for the content
            embedding = await self._embedding_service.embed_document_async(content)

            # Convert lists to comma-separated strings
            headers_str = ",".join(headers) if headers else ""

            # Create chunk
            chunk = KnowledgeChunk(
                uuid=uuid.uuid4(),
                headers=headers_str,
                content=content,
                summary=summary,
                keywords=keywords or [],
                type=chunk_type,
                embedding=embedding,
            )

            session.add(chunk)
            await session.flush()
            logger.info(f"Added knowledge chunk: {chunk.uuid}")

            return chunk

        except Exception as e:
            logger.error(f"Failed to add knowledge chunk: {e}")
            raise

    async def add_chunks_batch(
        self,
        session: AsyncSession,
        chunks_data: List[dict],
    ) -> List[KnowledgeChunk]:
        """Add multiple knowledge chunks in batch.

        Args:
            session: Database session.
            chunks_data: List of chunk data dictionaries with keys:
                - content (required)
                - headers (optional)
                - summary (optional)
                - keywords (optional)
                - type (optional)

        Returns:
            List[KnowledgeChunk]: Created knowledge chunks.

        Raises:
            Exception: If batch creation fails.
        """
        try:
            # Extract all content for batch embedding
            contents = [chunk["content"] for chunk in chunks_data]

            # Generate embeddings in batch
            embeddings = await self._embedding_service.embed_texts_async(
                contents, task_type="RETRIEVAL_DOCUMENT"
            )

            # Create chunks
            chunks: List[KnowledgeChunk] = []
            for chunk_data, embedding in zip(chunks_data, embeddings):
                headers_str = (
                    ",".join(chunk_data.get("headers", []))
                    if chunk_data.get("headers")
                    else ""
                )

                chunk = KnowledgeChunk(
                    uuid=uuid.uuid4(),
                    headers=headers_str,
                    content=chunk_data["content"],
                    summary=chunk_data.get("summary", ""),
                    keywords=chunk_data.get("keywords", []),
                    type=chunk_data.get("type", "ki�n th�c"),
                    embedding=embedding,
                )
                chunks.append(chunk)

            session.add_all(chunks)
            await session.flush()
            logger.info(f"Added {len(chunks)} knowledge chunks in batch")

            return chunks

        except Exception as e:
            logger.error(f"Failed to add chunks in batch: {e}")
            raise

    async def search_similar(
        self,
        session: AsyncSession,
        query: str,
        limit: int = 5,
        chunk_type: Optional[str] = None,
        similarity_threshold: float = 0.0,
    ) -> List[tuple[KnowledgeChunk, float]]:
        """Search for similar knowledge chunks using semantic similarity.

        Args:
            session: Database session.
            query: Search query text.
            limit: Maximum number of results (default: 5).
            chunk_type: Filter by chunk type (optional).
            similarity_threshold: Minimum similarity score (0-1, default: 0.0).

        Returns:
            List of tuples (KnowledgeChunk, similarity_score) sorted by similarity.

        Raises:
            Exception: If search fails.
        """
        try:
            # Generate query embedding
            query_embedding = await self._embedding_service.embed_query_async(query)

            # Build similarity search query using cosine similarity
            # Note: pgvector cosine distance is 1 - cosine_similarity
            # So we convert it back: similarity = 1 - distance
            similarity_expr = text(
                "1 - (embedding <=> CAST(:query_embedding AS vector))"
            )

            stmt = select(
                KnowledgeChunk, similarity_expr.label("similarity")
            ).where(similarity_expr >= similarity_threshold)

            # Filter by type if specified
            if chunk_type:
                stmt = stmt.where(KnowledgeChunk.type == chunk_type)

            # Order by similarity descending
            stmt = (
                stmt.order_by(text("similarity DESC"))
                .limit(limit)
                .params(query_embedding=str(query_embedding))
            )

            result = await session.execute(stmt)
            rows = result.all()

            # Convert to list of tuples
            results: List[tuple[KnowledgeChunk, float]] = [
                (row[0], float(row[1])) for row in rows
            ]

            logger.info(f"Found {len(results)} similar chunks for query")
            return results

        except Exception as e:
            logger.error(f"Failed to search similar chunks: {e}")
            raise

    async def get_chunk_by_uuid(
        self, session: AsyncSession, chunk_uuid: uuid.UUID
    ) -> Optional[KnowledgeChunk]:
        """Get a knowledge chunk by UUID.

        Args:
            session: Database session.
            chunk_uuid: UUID of the chunk.

        Returns:
            KnowledgeChunk if found, None otherwise.

        Raises:
            Exception: If retrieval fails.
        """
        try:
            stmt = select(KnowledgeChunk).where(KnowledgeChunk.uuid == chunk_uuid)
            result = await session.execute(stmt)
            chunk = result.scalar_one_or_none()

            if chunk:
                logger.debug(f"Retrieved chunk: {chunk_uuid}")
            else:
                logger.debug(f"Chunk not found: {chunk_uuid}")

            return chunk

        except Exception as e:
            logger.error(f"Failed to get chunk by UUID: {e}")
            raise

    async def update_chunk(
        self,
        session: AsyncSession,
        chunk_uuid: uuid.UUID,
        content: Optional[str] = None,
        headers: Optional[List[str]] = None,
        summary: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        chunk_type: Optional[str] = None,
    ) -> Optional[KnowledgeChunk]:
        """Update an existing knowledge chunk.

        If content is updated, a new embedding will be generated.

        Args:
            session: Database session.
            chunk_uuid: UUID of the chunk to update.
            content: New content (optional).
            headers: New headers (optional).
            summary: New summary (optional).
            keywords: New keywords (optional).
            chunk_type: New type (optional).

        Returns:
            Updated KnowledgeChunk if found, None otherwise.

        Raises:
            Exception: If update fails.
        """
        try:
            chunk = await self.get_chunk_by_uuid(session, chunk_uuid)
            if not chunk:
                return None

            # Update fields
            if content is not None:
                chunk.content = content
                # Regenerate embedding if content changed
                chunk.embedding = await self._embedding_service.embed_document_async(
                    content
                )

            if headers is not None:
                chunk.headers = ",".join(headers)

            if summary is not None:
                chunk.summary = summary

            if keywords is not None:
                chunk.keywords = keywords

            if chunk_type is not None:
                chunk.type = chunk_type

            await session.flush()
            logger.info(f"Updated chunk: {chunk_uuid}")

            return chunk

        except Exception as e:
            logger.error(f"Failed to update chunk: {e}")
            raise

    async def delete_chunk(
        self, session: AsyncSession, chunk_uuid: uuid.UUID
    ) -> bool:
        """Delete a knowledge chunk by UUID.

        Args:
            session: Database session.
            chunk_uuid: UUID of the chunk to delete.

        Returns:
            True if deleted, False if not found.

        Raises:
            Exception: If deletion fails.
        """
        try:
            stmt = delete(KnowledgeChunk).where(KnowledgeChunk.uuid == chunk_uuid)
            result = await session.execute(stmt)

            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted chunk: {chunk_uuid}")
            else:
                logger.debug(f"Chunk not found for deletion: {chunk_uuid}")

            return deleted

        except Exception as e:
            logger.error(f"Failed to delete chunk: {e}")
            raise

    async def list_chunks(
        self,
        session: AsyncSession,
        chunk_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[KnowledgeChunk]:
        """List knowledge chunks with optional filtering.

        Args:
            session: Database session.
            chunk_type: Filter by chunk type (optional).
            limit: Maximum number of results (default: 100).
            offset: Number of results to skip (default: 0).

        Returns:
            List of KnowledgeChunk objects.

        Raises:
            Exception: If listing fails.
        """
        try:
            stmt = select(KnowledgeChunk)

            if chunk_type:
                stmt = stmt.where(KnowledgeChunk.type == chunk_type)

            stmt = stmt.order_by(KnowledgeChunk.created_at.desc()).limit(limit).offset(offset)

            result = await session.execute(stmt)
            chunks = list(result.scalars().all())

            logger.info(f"Listed {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Failed to list chunks: {e}")
            raise

    async def count_chunks(
        self, session: AsyncSession, chunk_type: Optional[str] = None
    ) -> int:
        """Count total number of knowledge chunks.

        Args:
            session: Database session.
            chunk_type: Filter by chunk type (optional).

        Returns:
            Total count of chunks.

        Raises:
            Exception: If count fails.
        """
        try:
            stmt = select(KnowledgeChunk)

            if chunk_type:
                stmt = stmt.where(KnowledgeChunk.type == chunk_type)

            result = await session.execute(stmt)
            count = len(result.scalars().all())

            logger.debug(f"Total chunks: {count}")
            return count

        except Exception as e:
            logger.error(f"Failed to count chunks: {e}")
            raise


# Global vector store service instance
_vector_store_service: VectorStoreService | None = None


def get_vector_store_service() -> VectorStoreService:
    """Get or create the global vector store service instance.

    Returns:
        VectorStoreService: Global vector store service instance.
    """
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service
