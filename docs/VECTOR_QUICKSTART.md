# Vector Database Quick Start Guide

Get started with the vector database in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ with `uv` package manager
- Google Gemini API key

## Setup Steps

### 1. Start PostgreSQL with pgvector

```bash
# Start database container
make db-up

# Verify it's running
make db-logs
```

### 2. Configure Environment

Create or update `.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://mindai_user:mindai_password@localhost:5432/mindai_adk

# Gemini API (for embeddings)
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Run Database Migrations

```bash
# Create vector database tables
make db-migrate
```

### 4. Start the API Server

```bash
# Start FastAPI server
make run

# Open Swagger docs
open http://localhost:2003/docs
```

## Test It Out

### Using API (Swagger UI)

1. Go to http://localhost:2003/docs
2. Try **POST /api/v1/vector/chunks** to create a chunk:

```json
{
  "content": "Meditation helps reduce stress and anxiety by promoting mindfulness and relaxation.",
  "keywords": ["meditation", "stress", "anxiety", "mindfulness"],
  "type": "kiến thức"
}
```

3. Try **POST /api/v1/vector/chunks/search** to search:

```json
{
  "query": "How to reduce stress?",
  "limit": 5
}
```

### Using cURL

```bash
# Create a chunk
curl -X POST "http://localhost:2003/api/v1/vector/chunks" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Deep breathing exercises can calm the nervous system",
    "keywords": ["breathing", "relaxation"],
    "type": "kiến thức"
  }'

# Search for similar chunks
curl -X POST "http://localhost:2003/api/v1/vector/chunks/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "relaxation techniques",
    "limit": 3
  }'
```

### Using Python

```python
import asyncio
from app.services.vector_store import get_vector_store_service
from app.infra.db.session import get_session

async def demo():
    vector_service = get_vector_store_service()

    async for session in get_session():
        # Add a chunk
        chunk = await vector_service.add_chunk(
            session=session,
            content="Mindfulness meditation reduces anxiety",
            keywords=["mindfulness", "meditation", "anxiety"]
        )

        # Search
        results = await vector_service.search_similar(
            session=session,
            query="anxiety relief techniques",
            limit=3
        )

        for chunk, similarity in results:
            print(f"{similarity:.2f}: {chunk.content}")

        await session.commit()

asyncio.run(demo())
```

## Common Commands

```bash
# Database management
make db-up          # Start database
make db-down        # Stop database
make db-restart     # Restart database
make db-logs        # View logs
make db-backup      # Create backup
make db-migrate     # Run migrations
make db-reset       # Reset database (deletes all data)

# Development
make run            # Start API server
make test           # Run tests
make format         # Format code
make lint           # Lint code
```

## What's Next?

- Read the full [Vector Database Documentation](docs/VECTOR_DATABASE.md)
- Check the [Docker PostgreSQL Setup](docker/postgres/README.md)
- Explore the [API endpoints](http://localhost:2003/docs)
- View [test examples](tests/integration/test_vector_api.py)

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                FastAPI Server                    │
│              (port 2003)                         │
└───────────────────┬─────────────────────────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
┌───────▼──────────┐    ┌────────▼────────┐
│  Vector Router   │    │  Vector Service │
│  (API Layer)     │───▶│  (Business Logic)│
└──────────────────┘    └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │ Embedding Svc   │
                        │ (Gemini 768-dim)│
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │   PostgreSQL    │
                        │   + pgvector    │
                        │  (Docker)       │
                        └─────────────────┘
```

## Data Flow

1. **Create**: Text → Gemini Embedding → PostgreSQL with vector
2. **Search**: Query → Gemini Embedding → Cosine similarity search → Results

## Troubleshooting

### Database won't start
```bash
# Check if port 5432 is in use
lsof -i :5432

# View detailed logs
docker logs vietmindai-postgres
```

### Migration fails
```bash
# Check database connection
docker exec -it vietmindai-postgres psql -U mindai_user -d mindai_adk

# Check pgvector extension
docker exec -it vietmindai-postgres psql -U mindai_user -d mindai_adk -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### API returns 500 error
```bash
# Check DATABASE_URL in .env
# Check GOOGLE_API_KEY is set
# View API logs
make run
```

## Support

- GitHub Issues: [Create an issue](https://github.com/yourusername/VietMindAI-ADK/issues)
- Documentation: `docs/VECTOR_DATABASE.md`
- Docker Setup: `docker/postgres/README.md`
