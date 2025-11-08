"""Document search tool for RAG agent using core domain."""

import logging
from typing import Any

# Note: FunctionDeclaration import may vary by ADK version
# from google.adk.tools import FunctionDeclaration

from app.core.use_cases.document_use_cases import DocumentUseCases
from app.infra.adapters import EmbeddingServiceAdapter

logger = logging.getLogger(__name__)


# Note: This will be replaced with proper repository implementation
# For now, using a mock repository
class MockDocumentRepository:  # type: ignore
    """Mock document repository for demonstration."""

    async def create(self, document: Any) -> Any:
        """Create document."""
        return document

    async def get_by_id(self, document_id: Any) -> Any:
        """Get document by ID."""
        return None

    async def update(self, document: Any) -> Any:
        """Update document."""
        return document

    async def delete(self, document_id: Any) -> bool:
        """Delete document."""
        return True

    async def search_by_embedding(self, query: Any, embedding: Any) -> list:
        """Search by embedding."""
        return []

    async def search_by_text(self, query_text: str, limit: int = 10) -> list:
        """Search by text."""
        return []


# Initialize services
_embedding_adapter = EmbeddingServiceAdapter()
_mock_repo = MockDocumentRepository()
_document_use_cases = DocumentUseCases(_mock_repo, _embedding_adapter)


async def search_knowledge_base(
    query: str, top_k: int = 5, category: str | None = None
) -> dict[str, Any]:
    """Search the knowledge base for relevant documents.

    Args:
        query: Search query.
        top_k: Number of results to return (default: 5, max: 10).
        category: Optional category filter.

    Returns:
        dict: Search results with relevant documents.
    """
    try:
        # Limit top_k
        top_k = min(top_k, 10)

        # Search documents
        retrieved_docs = await _document_use_cases.search_documents(
            query=query,
            top_k=top_k,
            min_relevance_score=0.7,
            category=category,
        )

        results = {
            "query": query,
            "num_results": len(retrieved_docs),
            "documents": [
                {
                    "id": doc.document_id,
                    "title": doc.title or "Untitled",
                    "content": doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                    "relevance_score": doc.relevance_score,
                    "source": doc.source,
                }
                for doc in retrieved_docs
            ],
        }

        logger.info(f"Knowledge base search completed: {len(retrieved_docs)} documents found")
        return results

    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        return {
            "query": query,
            "num_results": 0,
            "documents": [],
            "error": str(e),
        }


# ADK Function Declaration (to be configured based on ADK version)
# document_search_tool = FunctionDeclaration(...)
# For now, use the function directly
