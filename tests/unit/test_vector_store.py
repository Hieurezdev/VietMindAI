"""Unit tests for vector store service."""

import uuid
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models import KnowledgeChunk
from app.services.vector_store import VectorStoreService, get_vector_store_service


@pytest.fixture
def mock_embedding_service() -> MagicMock:
    """Create a mock embedding service."""
    mock_service = MagicMock()
    mock_service.embed_document_async = AsyncMock(
        return_value=[0.1] * 768  # 768-dimensional vector
    )
    mock_service.embed_query_async = AsyncMock(
        return_value=[0.1] * 768
    )
    mock_service.embed_texts_async = AsyncMock(
        return_value=[[0.1] * 768, [0.2] * 768]  # Multiple vectors
    )
    return mock_service


@pytest.fixture
def vector_service(mock_embedding_service: MagicMock) -> VectorStoreService:
    """Create a vector store service with mocked embedding service."""
    with patch("app.services.vector_store.get_embedding_service", return_value=mock_embedding_service):
        service = VectorStoreService()
    return service


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock async session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


class TestVectorStoreService:
    """Test suite for VectorStoreService."""

    @pytest.mark.asyncio
    async def test_add_chunk(
        self,
        vector_service: VectorStoreService,
        mock_session: AsyncMock,
    ) -> None:
        """Test adding a single knowledge chunk."""
        # Arrange
        content = "Test content for mental health support"
        headers = ["header1", "header2"]
        keywords = ["keyword1", "keyword2"]
        summary = "Test summary"
        chunk_type = "kiến thức"

        # Act
        chunk = await vector_service.add_chunk(
            session=mock_session,
            content=content,
            headers=headers,
            summary=summary,
            keywords=keywords,
            chunk_type=chunk_type,
        )

        # Assert
        assert chunk is not None
        assert chunk.content == content
        assert chunk.headers == "header1,header2"
        assert chunk.keywords == ["keyword1", "keyword2"]
        assert chunk.summary == summary
        assert chunk.type == chunk_type
        assert len(chunk.embedding) == 768
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_chunk_with_defaults(
        self,
        vector_service: VectorStoreService,
        mock_session: AsyncMock,
    ) -> None:
        """Test adding a chunk with default values."""
        # Arrange
        content = "Test content"

        # Act
        chunk = await vector_service.add_chunk(
            session=mock_session,
            content=content,
        )

        # Assert
        assert chunk.content == content
        assert chunk.headers == ""
        assert chunk.keywords == []
        assert chunk.summary == ""
        assert chunk.type == "kiến thức"

    @pytest.mark.asyncio
    async def test_add_chunks_batch(
        self,
        vector_service: VectorStoreService,
        mock_session: AsyncMock,
    ) -> None:
        """Test adding multiple chunks in batch."""
        # Arrange
        chunks_data = [
            {
                "content": "Content 1",
                "headers": ["h1"],
                "summary": "Summary 1",
                "keywords": ["k1"],
                "type": "kiến thức",
            },
            {
                "content": "Content 2",
                "headers": ["h2"],
                "summary": "Summary 2",
                "keywords": ["k2"],
                "type": "thông tin",
            },
        ]

        # Act
        chunks = await vector_service.add_chunks_batch(
            session=mock_session,
            chunks_data=chunks_data,
        )

        # Assert
        assert len(chunks) == 2
        assert chunks[0].content == "Content 1"
        assert chunks[1].content == "Content 2"
        mock_session.add_all.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_chunk_by_uuid(
        self,
        vector_service: VectorStoreService,
        mock_session: AsyncMock,
    ) -> None:
        """Test getting a chunk by UUID."""
        # Arrange
        test_uuid = uuid.uuid4()
        mock_chunk = KnowledgeChunk(
            uuid=test_uuid,
            content="Test content",
            headers="",
            summary="",
            keywords="",
            type="kiến thức",
            embedding=[0.1] * 768,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_chunk
        mock_session.execute.return_value = mock_result

        # Act
        chunk = await vector_service.get_chunk_by_uuid(mock_session, test_uuid)

        # Assert
        assert chunk is not None
        assert chunk.uuid == test_uuid
        assert chunk.content == "Test content"

    @pytest.mark.asyncio
    async def test_get_chunk_by_uuid_not_found(
        self,
        vector_service: VectorStoreService,
        mock_session: AsyncMock,
    ) -> None:
        """Test getting a non-existent chunk."""
        # Arrange
        test_uuid = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        chunk = await vector_service.get_chunk_by_uuid(mock_session, test_uuid)

        # Assert
        assert chunk is None

    @pytest.mark.asyncio
    async def test_update_chunk(
        self,
        vector_service: VectorStoreService,
        mock_session: AsyncMock,
    ) -> None:
        """Test updating a chunk."""
        # Arrange
        test_uuid = uuid.uuid4()
        mock_chunk = KnowledgeChunk(
            uuid=test_uuid,
            content="Old content",
            headers="old",
            summary="old summary",
            keywords=["old"],
            type="kiến thức",
            embedding=[0.1] * 768,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_chunk
        mock_session.execute.return_value = mock_result

        new_content = "New content"
        new_keywords = ["new1", "new2"]

        # Act
        updated_chunk = await vector_service.update_chunk(
            session=mock_session,
            chunk_uuid=test_uuid,
            content=new_content,
            keywords=new_keywords,
        )

        # Assert
        assert updated_chunk is not None
        assert updated_chunk.content == new_content
        assert updated_chunk.keywords == ["new1", "new2"]
        mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_delete_chunk(
        self,
        vector_service: VectorStoreService,
        mock_session: AsyncMock,
    ) -> None:
        """Test deleting a chunk."""
        # Arrange
        test_uuid = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # Act
        deleted = await vector_service.delete_chunk(mock_session, test_uuid)

        # Assert
        assert deleted is True

    @pytest.mark.asyncio
    async def test_delete_chunk_not_found(
        self,
        vector_service: VectorStoreService,
        mock_session: AsyncMock,
    ) -> None:
        """Test deleting a non-existent chunk."""
        # Arrange
        test_uuid = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        # Act
        deleted = await vector_service.delete_chunk(mock_session, test_uuid)

        # Assert
        assert deleted is False

    @pytest.mark.asyncio
    async def test_list_chunks(
        self,
        vector_service: VectorStoreService,
        mock_session: AsyncMock,
    ) -> None:
        """Test listing chunks."""
        # Arrange
        mock_chunks = [
            KnowledgeChunk(
                uuid=uuid.uuid4(),
                content=f"Content {i}",
                headers="",
                summary="",
                keywords="",
                type="kiến thức",
                embedding=[0.1] * 768,
            )
            for i in range(3)
        ]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_chunks
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Act
        chunks = await vector_service.list_chunks(
            session=mock_session,
            limit=10,
            offset=0,
        )

        # Assert
        assert len(chunks) == 3

    def test_get_vector_store_service_singleton(self) -> None:
        """Test that get_vector_store_service returns singleton."""
        # Act
        service1 = get_vector_store_service()
        service2 = get_vector_store_service()

        # Assert
        assert service1 is service2
