```markdown
# Memory System Documentation

Complete guide to the user memory system with short-term and long-term memory support.

## Overview

The memory system provides:
- **Automatic User State Management**: Creates new user if `user_id` is None
- **Short-Term Memory (STM)**: Session-based conversation context
- **Long-Term Memory (LTM)**: Persistent user knowledge across sessions
- **Semantic Search**: Find relevant memories using embeddings
- **Automatic Cleanup**: Expired short-term memories are removable

## Architecture

```
User Input: {content, user_id}
           ↓
    ┌──────────────┐
    │ user_id=None?│
    └──────┬───────┘
           ├─ Yes → Create New User
           └─ No  → Get Existing User
           ↓
    ┌──────────────────────┐
    │  Memory Retrieval     │
    ├──────────────────────┤
    │ • Recent STM (5-10)   │
    │ • Relevant LTM (3-5)  │
    └───────────┬──────────┘
                ↓
    ┌──────────────────────┐
    │   Store New STM      │
    │  (user's message)    │
    └──────────────────────┘
```

## Data Models

### User
```python
{
    "user_id": UUID,              # Unique identifier
    "name": str | None,           # Optional display name
    "preferences": str,           # User preferences
    "created_at": datetime,       # Creation timestamp
    "last_interaction": datetime  # Last activity
}
```

### Short-Term Memory
```python
{
    "memory_id": UUID,
    "user_id": UUID,
    "session_id": UUID,           # Groups conversation turns
    "content": str,               # Message content
    "role": "user" | "assistant" | "system",
    "embedding": float[768],      # Semantic embedding
    "turn_number": int,           # Conversation turn
    "created_at": datetime,
    "expires_at": datetime | None # Auto-cleanup time
}
```

### Long-Term Memory
```python
{
    "memory_id": UUID,
    "user_id": UUID,
    "content": str,               # Memory content
    "memory_type": str,           # Type: preference, fact, context, goal, etc.
    "summary": str,               # Brief summary
    "importance": float,          # 0.0 to 1.0
    "embedding": float[768],
    "access_count": int,          # Usage tracking
    "last_accessed": datetime,
    "verified": bool,             # User-confirmed
    "created_at": datetime,
    "updated_at": datetime
}
```

## API Usage

### 1. Simple Chat (Main Endpoint)

**Endpoint**: `POST /api/v1/memory/chat`

**Request**:
```json
{
  "content": "I'm feeling anxious today",
  "user_id": null  // Creates new user if null
}
```

**Response**:
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "session_id": "987fcdeb-51a2-43f7-9876-543210fedcba",
  "is_new_user": true,
  "short_term_memories": [],
  "long_term_memories": [],
  "message": "Processed message from new user"
}
```

### 2. Existing User Chat

**Request**:
```json
{
  "content": "Can you remind me of my coping strategies?",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "session_id": "987fcdeb-51a2-43f7-9876-543210fedcba"
}
```

**Response**:
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "session_id": "987fcdeb-51a2-43f7-9876-543210fedcba",
  "is_new_user": false,
  "short_term_memories": [
    {
      "content": "I'm feeling anxious today",
      "role": "user",
      "turn": 1
    }
  ],
  "long_term_memories": [
    {
      "content": "User prefers deep breathing for anxiety",
      "type": "preference",
      "importance": 0.9,
      "similarity": 0.87
    }
  ],
  "message": "Processed message from existing user"
}
```

### 3. Create Long-Term Memory

**Endpoint**: `POST /api/v1/memory/long-term`

```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "content": "User mentioned they have a fear of public speaking",
  "memory_type": "fact",
  "summary": "Fear of public speaking",
  "importance": 0.8
}
```

### 4. Search Memories

**Endpoint**: `POST /api/v1/memory/search/long-term`

```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "query": "What are my anxiety triggers?",
  "limit": 5
}
```

**Response**:
```json
[
  {
    "memory": {
      "content": "User mentioned they have a fear of public speaking",
      "type": "fact",
      "importance": 0.8
    },
    "similarity": 0.91
  }
]
```

### 5. Get Conversation Context

**Endpoint**: `GET /api/v1/memory/context/{user_id}?query=...&session_id=...`

Returns both short-term and long-term memories relevant to the query.

### 6. Get User Info

**Endpoint**: `GET /api/v1/memory/user/{user_id}`

```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "name": null,
  "created_at": "2025-11-18T10:00:00Z",
  "last_interaction": "2025-11-18T12:30:00Z",
  "short_term_count": 15,
  "long_term_count": 8
}
```

### 7. Cleanup Expired Memories

**Endpoint**: `POST /api/v1/memory/cleanup`

```json
{
  "deleted_count": 42,
  "message": "Cleaned up 42 expired memories"
}
```

## Integration Example

### Python Integration

```python
import asyncio
import uuid
from app.services.memory_service import get_memory_service
from app.infra.db.session import get_session

async def handle_user_message(content: str, user_id: uuid.UUID | None = None):
    """Handle a user message with memory management."""
    memory_service = get_memory_service()

    async for session in get_session():
        # Get or create user
        user = await memory_service.get_or_create_user(
            session=session,
            user_id=user_id
        )

        # Get conversation context
        context = await memory_service.get_conversation_context(
            session=session,
            user_id=user.user_id,
            query=content,
            short_term_limit=5,
            long_term_limit=3
        )

        # Add user message to short-term memory
        await memory_service.add_short_term_memory(
            session=session,
            user_id=user.user_id,
            content=content,
            role="user"
        )

        # Process with your AI agent using context
        response = await process_with_agent(content, context)

        # Store assistant response
        await memory_service.add_short_term_memory(
            session=session,
            user_id=user.user_id,
            content=response,
            role="assistant"
        )

        await session.commit()

        return {
            "user_id": user.user_id,
            "response": response,
            "context": context
        }
```

### Creating Long-Term Memories from Conversation

```python
async def extract_and_store_ltm(user_id: uuid.UUID, content: str):
    """Extract important information and store as long-term memory."""
    memory_service = get_memory_service()

    async for session in get_session():
        # Example: User mentioned a preference
        if "I prefer" in content or "I like" in content:
            await memory_service.add_long_term_memory(
                session=session,
                user_id=user_id,
                content=content,
                memory_type="preference",
                importance=0.7
            )

        # Example: User shared a trigger
        elif "triggers my anxiety" in content:
            await memory_service.add_long_term_memory(
                session=session,
                user_id=user_id,
                content=content,
                memory_type="trigger",
                importance=0.9
            )

        await session.commit()
```

## Memory Types

### Short-Term Memory Use Cases
- Recent conversation history (last 5-10 turns)
- Current session context
- Temporary user state
- Real-time conversation flow

**Expires**: Typically 24 hours (configurable)

### Long-Term Memory Types

| Type | Description | Importance | Example |
|------|-------------|------------|---------|
| `preference` | User preferences | 0.7-0.9 | "Prefers morning therapy sessions" |
| `fact` | Factual information about user | 0.6-0.9 | "Works as a software engineer" |
| `context` | Background context | 0.5-0.7 | "Lives in urban area" |
| `goal` | User goals | 0.8-1.0 | "Wants to reduce social anxiety" |
| `trigger` | Anxiety/stress triggers | 0.9-1.0 | "Crowded spaces cause panic" |
| `coping` | Coping strategies that work | 0.8-0.9 | "Deep breathing helps during panic" |
| `general` | General information | 0.3-0.6 | "Likes reading books" |

## Best Practices

### 1. User State Management

```python
# ✅ Good: Let the system handle user creation
user = await memory_service.get_or_create_user(
    session=session,
    user_id=request.user_id  # Can be None
)

# ❌ Avoid: Manually checking if user exists
if user_id is None:
    # Manual user creation logic...
```

### 2. Memory Importance Scoring

```python
# High importance (0.8-1.0): Critical information
await memory_service.add_long_term_memory(
    content="User has severe social anxiety disorder",
    memory_type="fact",
    importance=0.95
)

# Medium importance (0.5-0.7): Useful context
await memory_service.add_long_term_memory(
    content="User enjoys hiking on weekends",
    memory_type="context",
    importance=0.6
)

# Low importance (0.3-0.5): General information
await memory_service.add_long_term_memory(
    content="User mentioned liking coffee",
    memory_type="general",
    importance=0.4
)
```

### 3. Session Management

```python
# Maintain session_id across conversation turns
session_id = uuid.uuid4()

for turn_number, user_message in enumerate(conversation):
    await memory_service.add_short_term_memory(
        session=session,
        user_id=user_id,
        content=user_message,
        session_id=session_id,  # Same session
        turn_number=turn_number
    )
```

### 4. Context Retrieval

```python
# Get relevant context for current query
context = await memory_service.get_conversation_context(
    session=session,
    user_id=user_id,
    query="How can I deal with work stress?",
    short_term_limit=5,   # Recent conversation
    long_term_limit=3     # Most relevant LTM
)

# Use context in your AI prompt
prompt = f"""
Recent conversation:
{format_short_term(context['short_term'])}

Relevant user information:
{format_long_term(context['long_term'])}

Current question: {query}
"""
```

## Database Migrations

```bash
# Run migrations to create memory tables
make db-migrate

# or
uv run alembic upgrade head
```

## Performance Considerations

### Indexing
- All embeddings use IVFFLAT indexes for fast similarity search
- User queries are indexed for fast lookups
- Session and timestamp indexes for efficient filtering

### Memory Cleanup

Set up a cron job or scheduled task:

```python
# Run daily
async def cleanup_job():
    memory_service = get_memory_service()
    async for session in get_session():
        deleted = await memory_service.cleanup_expired_memories(session)
        await session.commit()
        print(f"Cleaned up {deleted} expired memories")
```

Or use the API endpoint:
```bash
curl -X POST http://localhost:2003/api/v1/memory/cleanup
```

## Testing

```bash
# Run memory system tests
uv run pytest tests/unit/test_memory_service.py -v
uv run pytest tests/integration/test_memory_api.py -v
```

## Troubleshooting

### User Not Found
**Issue**: `404 User not found`
**Solution**: Use `/memory/chat` endpoint which auto-creates users

### Memory Search Returns Empty
**Issue**: Search returns no results
**Solution**:
- Check if memories exist for that user
- Lower similarity threshold
- Verify embeddings are generated correctly

### Expired Memories Not Cleaned
**Issue**: Old short-term memories remain
**Solution**: Run cleanup endpoint or set up automated cleanup job

## Advanced Usage

### Custom Memory Verification

```python
# Mark memory as verified after user confirmation
stmt = update(LongTermMemory).where(
    LongTermMemory.memory_id == memory_id
).values(verified=True)
await session.execute(stmt)
```

### Memory Importance Decay

```python
# Decrease importance of old, unused memories
from datetime import datetime, timedelta

old_threshold = datetime.utcnow() - timedelta(days=90)

stmt = update(LongTermMemory).where(
    LongTermMemory.last_accessed < old_threshold,
    LongTermMemory.access_count < 5
).values(importance=LongTermMemory.importance * 0.8)
```

## Security Notes

- User IDs are UUIDs (not predictable)
- All memories are user-scoped
- Cascade delete: Deleting user removes all memories
- No cross-user memory access

## Resources

- [Vector Database Docs](VECTOR_DATABASE.md)
- [API Documentation](http://localhost:2003/docs)
- [Database Schema](../app/infra/db/models.py)
```
