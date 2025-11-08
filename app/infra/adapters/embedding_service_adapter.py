"""Adapter for embedding service implementing core port interface."""

import logging

from app.core.ports.services import IEmbeddingService
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class EmbeddingServiceAdapter(IEmbeddingService):
    """Adapter that implements IEmbeddingService using the existing EmbeddingService."""

    def __init__(self) -> None:
        """Initialize the adapter."""
        self._embedding_service = get_embedding_service()
        logger.info("EmbeddingServiceAdapter initialized")

    async def embed_text_async(
        self, text: str, task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> list[float]:
        """Generate embedding for text.

        Args:
            text: Text to embed.
            task_type: Task type for embedding.

        Returns:
            list[float]: Embedding vector.
        """
        return await self._embedding_service.embed_text_async(text, task_type)

    async def embed_query_async(self, query: str) -> list[float]:
        """Generate embedding for search query.

        Args:
            query: Search query.

        Returns:
            list[float]: Embedding vector optimized for queries.
        """
        return await self._embedding_service.embed_query_async(query)

    async def embed_document_async(self, document: str) -> list[float]:
        """Generate embedding for document.

        Args:
            document: Document text.

        Returns:
            list[float]: Embedding vector optimized for documents.
        """
        return await self._embedding_service.embed_document_async(document)
