"""Use cases for document and knowledge base management."""

import logging
from uuid import UUID

from app.core.domain.entities import Document
from app.core.domain.value_objects import EmbeddingVector, RetrievedDocument, SearchQuery
from app.core.ports.repositories import IDocumentRepository
from app.core.ports.services import IEmbeddingService

logger = logging.getLogger(__name__)


class DocumentUseCases:
    """Use cases for document and RAG operations."""

    def __init__(
        self,
        document_repo: IDocumentRepository,
        embedding_service: IEmbeddingService,
    ) -> None:
        """Initialize document use cases.

        Args:
            document_repo: Repository for documents.
            embedding_service: Embedding service.
        """
        self.document_repo = document_repo
        self.embedding_service = embedding_service

    async def create_document(
        self,
        title: str,
        content: str,
        source: str | None = None,
        category: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Document:
        """Create a new document with embedding.

        Args:
            title: Document title.
            content: Document content.
            source: Optional source reference.
            category: Optional category.
            metadata: Optional metadata.

        Returns:
            Document: Created document with embedding.
        """
        # Generate embedding for document
        embedding_values = await self.embedding_service.embed_document_async(content)

        document = Document(
            title=title,
            content=content,
            source=source,
            category=category,
            embedding=embedding_values,
            metadata=metadata or {},
        )

        created = await self.document_repo.create(document)
        logger.info(f"Created document {created.id}: {title}")
        return created

    async def search_documents(
        self,
        query: str,
        top_k: int = 5,
        min_relevance_score: float = 0.7,
        category: str | None = None,
    ) -> list[RetrievedDocument]:
        """Search documents using semantic search.

        Args:
            query: Search query.
            top_k: Number of results to return.
            min_relevance_score: Minimum relevance score (0-1).
            category: Optional category filter.

        Returns:
            list[RetrievedDocument]: Retrieved documents with relevance scores.
        """
        # Generate embedding for query
        query_embedding_values = await self.embedding_service.embed_query_async(query)
        query_embedding = EmbeddingVector(values=query_embedding_values)

        # Build search query
        filters = {}
        if category:
            filters["category"] = category

        search_query = SearchQuery(
            query_text=query,
            embedding=query_embedding,
            top_k=top_k,
            filters=filters,
            min_relevance_score=min_relevance_score,
        )

        # Search documents
        documents = await self.document_repo.search_by_embedding(search_query, query_embedding)

        # Convert to retrieved documents (in real implementation, would include similarity scores)
        retrieved = [
            RetrievedDocument(
                document_id=str(doc.id),
                content=doc.content,
                title=doc.title,
                relevance_score=0.85,  # Placeholder - actual implementation would compute this
                source=doc.source,
                metadata=doc.metadata,
            )
            for doc in documents[:top_k]
        ]

        logger.info(f"Retrieved {len(retrieved)} documents for query: {query[:50]}...")
        return retrieved

    async def search_documents_by_text(self, query_text: str, limit: int = 10) -> list[Document]:
        """Search documents using full-text search.

        Args:
            query_text: Text query.
            limit: Maximum number of results.

        Returns:
            list[Document]: Matching documents.
        """
        documents = await self.document_repo.search_by_text(query_text, limit)
        logger.info(f"Found {len(documents)} documents for text search: {query_text[:50]}...")
        return documents

    async def get_document(self, document_id: UUID) -> Document | None:
        """Get a document by ID.

        Args:
            document_id: Document ID.

        Returns:
            Document | None: Document if found.
        """
        return await self.document_repo.get_by_id(document_id)

    async def update_document(
        self,
        document_id: UUID,
        title: str | None = None,
        content: str | None = None,
        source: str | None = None,
        category: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Document:
        """Update a document.

        Args:
            document_id: Document ID.
            title: Optional new title.
            content: Optional new content.
            source: Optional new source.
            category: Optional new category.
            metadata: Optional new metadata.

        Returns:
            Document: Updated document.

        Raises:
            ValueError: If document not found.
        """
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Update fields
        if title is not None:
            document.title = title
        if content is not None:
            document.content = content
            # Regenerate embedding if content changed
            embedding_values = await self.embedding_service.embed_document_async(content)
            document.embedding = embedding_values
        if source is not None:
            document.source = source
        if category is not None:
            document.category = category
        if metadata is not None:
            document.metadata = metadata

        updated = await self.document_repo.update(document)
        logger.info(f"Updated document {document_id}")
        return updated

    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document.

        Args:
            document_id: Document ID.

        Returns:
            bool: True if deleted successfully.
        """
        deleted = await self.document_repo.delete(document_id)
        if deleted:
            logger.info(f"Deleted document {document_id}")
        return deleted
