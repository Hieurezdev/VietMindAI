# Vector Database Implementation

This document describes the vector database implementation for VietMindAI-ADK using PostgreSQL with pgvector extension.

## Overview

The vector database stores knowledge chunks with semantic embeddings, enabling:
- **Semantic search**: Find similar content based on meaning, not just keywords
- **RAG (Retrieval-Augmented Generation)**: Enhance AI responses with relevant knowledge
- **Knowledge management**: Store, update, and retrieve mental health information

## Architecture

### Components

1. **Database Model** (`app/infra/db/models.py`)
   - `KnowledgeChunk`: SQLAlchemy model with pgvector support
   - 768-dimensional embeddings from Gemini

2. **Service Layer** (`app/services/vector_store.py`)
   - `VectorStoreService`: Business logic for vector operations
   - CRUD operations with automatic embedding generation

3. **API Layer** (`app/api/routers/vector.py`)
   - REST endpoints for vector database operations
   - Pydantic schemas for validation

4. **Migrations** (`alembic/versions/`)
   - Database schema management
   - pgvector extension setup

## Data Structure

### Knowledge Chunk Schema

```python
{
    "uuid": "string (UUID)",        # Unique identifier
    "headers": ["string"],          # Metadata/headers list
    "content": "string",            # Main content (required)
    "summary": "string",            # Brief summary
    "keywords": ["string"],         # Keywords for filtering
    "type": "string",               # Category (default: "kiến thức")
    "embedding": [float * 768],     # Vector embedding (auto-generated)
    "created_at": "datetime",       # Creation timestamp
    "updated_at": "datetime"        # Last update timestamp
}
```

## Setup

### 1. Database Prerequisites

Ensure PostgreSQL with pgvector extension is installed:

```bash
# Using Docker (recommended)
docker-compose -f docker-compose.postgres.yml up -d

# Or install pgvector manually
# See: https://github.com/pgvector/pgvector
```

### 2. Configure Environment

Set `DATABASE_URL` in your `.env` file:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/vietmindai
```

### 3. Run Migrations

Create the vector database tables:

```bash
# Run migrations
uv run alembic upgrade head

# To rollback
uv run alembic downgrade -1
```

### 4. Verify Installation

Check that the server starts successfully:

```bash
make run
# Visit http://localhost:2003/docs
```

## API Usage

### Endpoints

All endpoints are under `/api/v1/vector/`:

#### 1. Create a Knowledge Chunk

```http
POST /api/v1/vector/chunks
Content-Type: application/json

{
  "content": "Cognitive Behavioral Therapy (CBT) is an evidence-based approach...",
  "headers": ["CBT", "Therapy"],
  "summary": "Overview of CBT techniques",
  "keywords": ["CBT", "cognitive", "therapy"],
  "type": "kiến thức"
}
```

**Response (201 Created):**
```json
{
  "uuid": "123e4567-e89b-12d3-a456-426614174000",
  "content": "Cognitive Behavioral Therapy (CBT)...",
  "headers": ["CBT", "Therapy"],
  "summary": "Overview of CBT techniques",
  "keywords": ["CBT", "cognitive", "therapy"],
  "type": "kiến thức",
  "created_at": "2025-11-18T10:30:00Z",
  "updated_at": "2025-11-18T10:30:00Z"
}
```

#### 2. Batch Create Chunks

```http
POST /api/v1/vector/chunks/batch
Content-Type: application/json

{
  "chunks": [
    {
      "content": "Content 1",
      "type": "kiến thức"
    },
    {
      "content": "Content 2",
      "type": "thông tin"
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "chunks": [...],
  "count": 2
}
```

#### 3. Search Similar Chunks (Semantic Search)

```http
POST /api/v1/vector/chunks/search
Content-Type: application/json

{
  "query": "What are coping strategies for anxiety?",
  "limit": 5,
  "type": "kiến thức",
  "similarity_threshold": 0.7
}
```

**Response (200 OK):**
```json
[
  {
    "chunk": {
      "uuid": "...",
      "content": "Anxiety coping strategies include...",
      ...
    },
    "similarity": 0.95
  },
  ...
]
```

#### 4. Get Chunk by UUID

```http
GET /api/v1/vector/chunks/{uuid}
```

#### 5. Update Chunk

```http
PATCH /api/v1/vector/chunks/{uuid}
Content-Type: application/json

{
  "content": "Updated content",
  "keywords": ["new", "keywords"]
}
```

Note: If `content` is updated, a new embedding is automatically generated.

#### 6. Delete Chunk

```http
DELETE /api/v1/vector/chunks/{uuid}
```

**Response (204 No Content)**

#### 7. List Chunks

```http
GET /api/v1/vector/chunks?type=kiến thức&limit=100&offset=0
```

**Response (200 OK):**
```json
{
  "chunks": [...],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

## Programmatic Usage

### Using the Service Directly

```python
from app.services.vector_store import get_vector_store_service
from app.infra.db.session import get_session

async def add_knowledge():
    vector_service = get_vector_store_service()

    async for session in get_session():
        # Add a chunk
        chunk = await vector_service.add_chunk(
            session=session,
            content="Mental health content",
            headers=["header1"],
            keywords=["keyword1", "keyword2"],
            chunk_type="kiến thức"
        )

        # Search similar chunks
        results = await vector_service.search_similar(
            session=session,
            query="coping strategies",
            limit=5,
            similarity_threshold=0.7
        )

        for chunk, similarity in results:
            print(f"Match: {similarity:.2f} - {chunk.content[:50]}...")
```

### Integration with RAG Agent

```python
# In your RAG agent
from app.services.vector_store import get_vector_store_service

async def retrieve_context(query: str) -> str:
    """Retrieve relevant context for RAG."""
    vector_service = get_vector_store_service()

    async for session in get_session():
        results = await vector_service.search_similar(
            session=session,
            query=query,
            limit=3,
            chunk_type="kiến thức"
        )

        context = "\n\n".join([
            f"[Relevance: {sim:.2f}]\n{chunk.content}"
            for chunk, sim in results
        ])

        return context
```

## Performance Optimization

### Vector Index

The database uses IVFFLAT index for fast similarity search:

```sql
CREATE INDEX ix_knowledge_chunks_embedding
ON knowledge_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### Best Practices

1. **Batch Operations**: Use `/chunks/batch` for creating multiple chunks
2. **Similarity Threshold**: Set appropriate threshold (0.7-0.9) to filter results
3. **Limit Results**: Use reasonable limits (5-10) for search queries
4. **Type Filtering**: Use `type` parameter to narrow search scope
5. **Index Tuning**: Adjust `lists` parameter based on dataset size:
   - Small (<10k chunks): lists = 100
   - Medium (10k-1M): lists = 1000
   - Large (>1M): lists = 10000

## Testing

### Run Unit Tests

```bash
uv run pytest tests/unit/test_vector_store.py -v
```

### Run Integration Tests

```bash
uv run pytest tests/integration/test_vector_api.py -v
```

### Run All Tests

```bash
make test
```

## Troubleshooting

### pgvector Extension Not Found

```bash
# Install pgvector extension
docker exec -it postgres psql -U user -d vietmindai -c "CREATE EXTENSION vector;"
```

### Embedding Dimension Mismatch

Ensure you're using `gemini-embedding-001` which produces 768-dimensional vectors.

### Slow Search Performance

- Check if index exists: `\d+ knowledge_chunks` in psql
- Increase `lists` parameter for larger datasets
- Consider using HNSW index for very large datasets

### Migration Issues

```bash
# Check current migration version
uv run alembic current

# View migration history
uv run alembic history

# Reset database (WARNING: deletes all data)
uv run alembic downgrade base
uv run alembic upgrade head
```

## Future Enhancements

1. **HNSW Index**: Switch to HNSW for better performance on large datasets
2. **Metadata Filtering**: Add more sophisticated filtering options
3. **Hybrid Search**: Combine semantic search with keyword search
4. **Caching**: Add Redis caching for frequently accessed chunks
5. **Analytics**: Track search patterns and relevance feedback

## References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Gemini Embedding API](https://ai.google.dev/docs/embeddings_guide)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
