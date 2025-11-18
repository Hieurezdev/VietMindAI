"""Integration tests for vector store API endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def mock_vector_service() -> MagicMock:
    """Create a mock vector store service."""
    from app.infra.db.models import KnowledgeChunk

    service = MagicMock()

    # Mock add_chunk
    async def mock_add_chunk(*args, **kwargs):  # type: ignore[no-untyped-def]
        return KnowledgeChunk(
            uuid=uuid.uuid4(),
            content=kwargs.get("content", "Test content"),
            headers=",".join(kwargs.get("headers", [])),
            summary=kwargs.get("summary", ""),
            keywords=kwargs.get("keywords", []),
            type=kwargs.get("chunk_type", "kiến thức"),
            embedding=[0.1] * 768,
        )

    service.add_chunk = AsyncMock(side_effect=mock_add_chunk)

    # Mock add_chunks_batch
    async def mock_add_chunks_batch(*args, **kwargs):  # type: ignore[no-untyped-def]
        chunks_data = kwargs.get("chunks_data", [])
        return [
            KnowledgeChunk(
                uuid=uuid.uuid4(),
                content=chunk["content"],
                headers=",".join(chunk.get("headers", [])),
                summary=chunk.get("summary", ""),
                keywords=chunk.get("keywords", []),
                type=chunk.get("type", "kiến thức"),
                embedding=[0.1] * 768,
            )
            for chunk in chunks_data
        ]

    service.add_chunks_batch = AsyncMock(side_effect=mock_add_chunks_batch)

    # Mock search_similar
    async def mock_search_similar(*args, **kwargs):  # type: ignore[no-untyped-def]
        chunk = KnowledgeChunk(
            uuid=uuid.uuid4(),
            content="Similar content",
            headers="",
            summary="",
            keywords=[],
            type="",
            embedding=[0.1] * 768,
        )
        return [(chunk, 0.95)]

    service.search_similar = AsyncMock(side_effect=mock_search_similar)

    # Mock get_chunk_by_uuid
    async def mock_get_chunk(*args, **kwargs):  # type: ignore[no-untyped-def]
        return KnowledgeChunk(
            uuid=kwargs.get("chunk_uuid", uuid.uuid4()),
            content="Test content",
            headers="header1",
            summary="Summary",
            keywords=["keyword1"],
            type="kiến thức",
            embedding=[0.1] * 768,
        )

    service.get_chunk_by_uuid = AsyncMock(side_effect=mock_get_chunk)

    # Mock update_chunk
    async def mock_update_chunk(*args, **kwargs):  # type: ignore[no-untyped-def]
        return KnowledgeChunk(
            uuid=kwargs.get("chunk_uuid", uuid.uuid4()),
            content=kwargs.get("content", "Updated content"),
            headers=",".join(kwargs.get("headers", [])) if kwargs.get("headers") else "header1",
            summary=kwargs.get("summary", "Summary"),
            keywords=kwargs.get("keywords", ["keyword1"]),
            type=kwargs.get("chunk_type", "kiến thức"),
            embedding=[0.1] * 768,
        )

    service.update_chunk = AsyncMock(side_effect=mock_update_chunk)

    # Mock delete_chunk
    service.delete_chunk = AsyncMock(return_value=True)

    # Mock list_chunks
    async def mock_list_chunks(*args, **kwargs):  # type: ignore[no-untyped-def]
        return [
            KnowledgeChunk(
                uuid=uuid.uuid4(),
                content=f"Content {i}",
                headers="",
                summary="",
                keywords=[],
                type="kiến thức",
                embedding=[0.1] * 768,
            )
            for i in range(2)
        ]

    service.list_chunks = AsyncMock(side_effect=mock_list_chunks)

    # Mock count_chunks
    service.count_chunks = AsyncMock(return_value=2)

    return service


@pytest.fixture
def client(mock_vector_service: MagicMock) -> TestClient:
    """Create test client with mocked vector service."""
    with patch("app.api.routers.vector.get_vector_store_service", return_value=mock_vector_service):
        app = create_app()
        return TestClient(app)


class TestVectorAPI:
    """Test suite for vector store API endpoints."""

    def test_create_chunk(self, client: TestClient) -> None:
        """Test creating a new knowledge chunk."""
        # Arrange
        payload = {
            "content": "Test mental health content",
            "headers": ["header1", "header2"],
            "summary": "Test summary",
            "keywords": ["keyword1", "keyword2"],
            "type": "kiến thức",
        }

        # Act
        response = client.post("/api/v1/vector/chunks", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == payload["content"]
        assert data["type"] == payload["type"]
        assert "uuid" in data
        assert "created_at" in data

    def test_create_chunk_minimal(self, client: TestClient) -> None:
        """Test creating a chunk with minimal data."""
        # Arrange
        payload = {"content": "Minimal content"}

        # Act
        response = client.post("/api/v1/vector/chunks", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == payload["content"]

    def test_create_chunks_batch(self, client: TestClient) -> None:
        """Test batch creating knowledge chunks."""
        # Arrange
        payload = {
            "chunks": [
                {
                    "content": "Content 1",
                    "summary": "Summary 1",
                    "type": "kiến thức",
                },
                {
                    "content": "Content 2",
                    "summary": "Summary 2",
                    "type": "thông tin",
                },
            ]
        }

        # Act
        response = client.post("/api/v1/vector/chunks/batch", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["count"] == 2
        assert len(data["chunks"]) == 2

    def test_search_chunks(self, client: TestClient) -> None:
        """Test searching for similar chunks."""
        # Arrange
        payload = {
            "query": "mental health support",
            "limit": 5,
            "similarity_threshold": 0.7,
        }

        # Act
        response = client.post("/api/v1/vector/chunks/search", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "chunk" in data[0]
        assert "similarity" in data[0]
        assert 0 <= data[0]["similarity"] <= 1

    def test_get_chunk(self, client: TestClient) -> None:
        """Test getting a chunk by UUID."""
        # Arrange
        test_uuid = uuid.uuid4()

        # Act
        response = client.get(f"/api/v1/vector/chunks/{test_uuid}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "uuid" in data
        assert "content" in data

    def test_update_chunk(self, client: TestClient) -> None:
        """Test updating a chunk."""
        # Arrange
        test_uuid = uuid.uuid4()
        payload = {
            "content": "Updated content",
            "keywords": ["new1", "new2"],
        }

        # Act
        response = client.patch(f"/api/v1/vector/chunks/{test_uuid}", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "uuid" in data

    def test_delete_chunk(self, client: TestClient) -> None:
        """Test deleting a chunk."""
        # Arrange
        test_uuid = uuid.uuid4()

        # Act
        response = client.delete(f"/api/v1/vector/chunks/{test_uuid}")

        # Assert
        assert response.status_code == 204

    def test_list_chunks(self, client: TestClient) -> None:
        """Test listing chunks."""
        # Act
        response = client.get("/api/v1/vector/chunks?limit=10&offset=0")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "chunks" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["chunks"], list)

    def test_list_chunks_with_type_filter(self, client: TestClient) -> None:
        """Test listing chunks with type filter."""
        # Act
        response = client.get("/api/v1/vector/chunks?type=kiến thức")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "chunks" in data
