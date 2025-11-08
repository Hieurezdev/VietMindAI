"""Embedding service using Google Gemini Embedding API with ADK integration."""

import logging

from google import genai

from app.config.config import get_settings
from app.infra.clients.client import Client

from typing import List
logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Google Gemini.

    Uses gemini-embedding-001 model for consistent 768-dimensional embeddings.
    """

    def __init__(self) -> None:
        """Initialize the embedding service with Gemini configuration."""
        settings = get_settings()

        if not settings.gemini_api_key:
            raise ValueError("GOOGLE_API_KEY not configured. Please set it in your .env file.")

        self._client = Client(api_key=settings.gemini_api_key).get_client()
        self._model_name = settings.embedding_model
        logger.info(f"Embedding service initialized with model: {self._model_name}")

    def embed_text(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """Generate embedding for a single text synchronously.

        Args:
            text: The text to embed.
            task_type: Task type for embedding. Options:
                - "RETRIEVAL_DOCUMENT": For documents to be retrieved
                - "RETRIEVAL_QUERY": For search queries
                - "SEMANTIC_SIMILARITY": For similarity comparison
                - "CLASSIFICATION": For text classification
                - "CLUSTERING": For text clustering

        Returns:
            List[float]: Embedding vector (768 dimensions).

        Raises:
            Exception: If embedding generation fails.
        """
        try:
            response = self._client.models.embed_content(
                model=self._model_name,
                contents=text,
                config={"task_type": task_type},
            )

            if not response.embeddings or len(response.embeddings) == 0:
                raise ValueError("Empty embedding response from Gemini API")

            embedding = response.embeddings[0].values
            if embedding is None:
                raise ValueError("Embedding values are None")

            result: List[float] = List(embedding)
            logger.debug(f"Generated embedding with dimension: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def embed_text_async(
        self, text: str, task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[float]:
        """Generate embedding for a single text asynchronously.

        Args:
            text: The text to embed.
            task_type: Task type for embedding (see embed_text for options).

        Returns:
            List[float]: Embedding vector (768 dimensions).

        Raises:
            Exception: If embedding generation fails.
        """
        try:
            response = await self._client.aio.models.embed_content(
                model=self._model_name,
                contents=text,
                config={"task_type": task_type},
            )

            if not response.embeddings or len(response.embeddings) == 0:
                raise ValueError("Empty embedding response from Gemini API")

            embedding = response.embeddings[0].values
            if embedding is None:
                raise ValueError("Embedding values are None")

            result: List[float] = List(embedding)
            logger.debug(f"Generated embedding with dimension: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def embed_texts(
        self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts in batch synchronously.

        Args:
            texts: List of texts to embed.
            task_type: Task type for embedding (see embed_text for options).

        Returns:
            List[List[float]]: List of embedding vectors.

        Raises:
            Exception: If embedding generation fails.
        """
        try:
            embeddings: List[List[float]] = []

            # Process each text (Gemini API handles batching internally)
            for text in texts:
                embedding = self.embed_text(text, task_type=task_type)
                embeddings.append(embedding)

            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise

    async def embed_texts_async(
        self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts in batch asynchronously.

        Args:
            texts: List of texts to embed.
            task_type: Task type for embedding (see embed_text for options).

        Returns:
            List[List[float]]: List of embedding vectors.

        Raises:
            Exception: If embedding generation fails.
        """
        try:
            embeddings: List[List[float]] = []

            # Process each text asynchronously
            for text in texts:
                embedding = await self.embed_text_async(text, task_type=task_type)
                embeddings.append(embedding)

            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding specifically for a search query.

        Args:
            query: The search query to embed.

        Returns:
            List[float]: Embedding vector optimized for retrieval.

        Raises:
            Exception: If embedding generation fails.
        """
        return self.embed_text(query, task_type="RETRIEVAL_QUERY")

    async def embed_query_async(self, query: str) -> List[float]:
        """Generate embedding for a search query asynchronously.

        Args:
            query: The search query to embed.

        Returns:
            List[float]: Embedding vector optimized for retrieval.

        Raises:
            Exception: If embedding generation fails.
        """
        return await self.embed_text_async(query, task_type="RETRIEVAL_QUERY")

    def embed_document(self, document: str) -> List[float]:
        """Generate embedding specifically for a document.

        Args:
            document: The document text to embed.

        Returns:
            List[float]: Embedding vector optimized for document storage.

        Raises:
            Exception: If embedding generation fails.
        """
        return self.embed_text(document, task_type="RETRIEVAL_DOCUMENT")

    async def embed_document_async(self, document: str) -> List[float]:
        """Generate embedding for a document asynchronously.

        Args:
            document: The document text to embed.

        Returns:
            List[float]: Embedding vector optimized for document storage.

        Raises:
            Exception: If embedding generation fails.
        """
        return await self.embed_text_async(document, task_type="RETRIEVAL_DOCUMENT")

    def get_client(self) -> genai.Client:
        """Get the underlying Gemini client.

        Returns:
            genai.Client: Gemini client instance.
        """
        return self._client

    def get_model_name(self) -> str:
        """Get the current embedding model name.

        Returns:
            str: Embedding model name being used.
        """
        return self._model_name

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model.

        Returns:
            int: Embedding dimension (768 for gemini-embedding-001).
        """
        return 768


# Global embedding service instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance.

    Returns:
        EmbeddingService: Global embedding service instance.
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
