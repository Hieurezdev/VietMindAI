# Chat Flow Example

## Complete End-to-End Flow

This document demonstrates how user input flows through the VietMindAI system from API to ADK agents and back.

## Architecture Overview

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │ POST /api/v1/chat/
       ▼
┌─────────────────────────────────────┐
│  FastAPI Router                     │
│  app/api/routers/chat.py            │
│  - ChatRequest validation           │
│  - Dependency injection             │
└──────┬──────────────────────────────┘
       │ ChatRequest + current_user
       ▼
┌─────────────────────────────────────┐
│  Build ChatContext                  │
│  - Recent messages history          │
│  - Crisis indicators                │
│  - Detected topics                  │
└──────┬──────────────────────────────┘
       │ ChatContext
       ▼
┌─────────────────────────────────────┐
│  AgentOrchestrationService          │
│  app/infra/adapters/                │
│  - route_message()                  │
│  - Create context_state dict        │
└──────┬──────────────────────────────┘
       │ context_state: dict[str, Any]
       ▼
┌─────────────────────────────────────┐
│  Root Agent (ADK)                   │
│  app/agents/agent.py                │
│  - Analyze user input               │
│  - Route to specialized sub-agent   │
└──────┬──────────────────────────────┘
       │
       ├──► General Agent (mental health chat)
       ├──► Crisis Detection Agent (suicide prevention)
       ├──► RAG Agent (knowledge-based answers)
       ├──► CBT Agent (cognitive therapy)
       └──► Mindfulness Agent (meditation guidance)
       │
       │ Sub-agent processes with tools
       ▼
┌─────────────────────────────────────┐
│  Agent Tools (if needed)            │
│  - crisis_detection_tool            │
│  - document_search_tool             │
└──────┬──────────────────────────────┘
       │ Tool results
       ▼
┌─────────────────────────────────────┐
│  AgentResponse                      │
│  - content (response text)          │
│  - agent_name                       │
│  - processing_time_ms               │
│  - metadata                         │
└──────┬──────────────────────────────┘
       │ AgentResponse value object
       ▼
┌─────────────────────────────────────┐
│  Map to ChatResponseModel           │
│  - response                         │
│  - agent_name                       │
│  - conversation_id                  │
│  - processing_time_ms               │
└──────┬──────────────────────────────┘
       │ JSON response
       ▼
┌─────────────┐
│   User      │
└─────────────┘
```

## Example Request

### 1. General Mental Health Question

**Request:**
```bash
curl -X POST http://localhost:2003/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "message": "Tôi đang cảm thấy lo lắng về công việc",
    "conversation_id": null,
    "history": []
  }'
```

**Expected Response:**
```json
{
  "response": "Tôi hiểu rằng bạn đang cảm thấy lo lắng về công việc. Lo lắng là một cảm xúc bình thường khi chúng ta đối mặt với áp lực...",
  "agent_name": "general_agent",
  "conversation_id": null,
  "processing_time_ms": 1250,
  "metadata": {
    "user_id": "test-user-id"
  }
}
```

**Flow:**
1. FastAPI validates `ChatRequest`
2. `get_current_user()` dependency extracts user from Bearer token
3. `ChatContext` built with empty history
4. `AgentOrchestrationService.route_message()` called
5. Root agent analyzes message, routes to `general_agent`
6. General agent generates empathetic response
7. `AgentResponse` created and returned
8. Mapped to `ChatResponseModel` and sent to user

### 2. Crisis Detection Example

**Request:**
```bash
curl -X POST http://localhost:2003/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "message": "Tôi không còn muốn sống nữa",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "history": [
      "Tôi cảm thấy rất mệt mỏi",
      "Mọi thứ đều vô nghĩa"
    ]
  }'
```

**Expected Response:**
```json
{
  "response": "Tôi rất quan ngại về những gì bạn đang chia sẻ. Bạn không đơn độc và có sự hỗ trợ sẵn có. Hãy gọi ngay đến:\n\n🆘 Đường dây nóng 24/7:\n- Tâm Việt: 1800 599 920\n- Life Center: 0903 194 419\n\nBạn có thể nói chuyện với tôi thêm không?",
  "agent_name": "crisis_detection_agent",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "processing_time_ms": 980,
  "metadata": {
    "user_id": "test-user-id",
    "crisis_detected": "true",
    "severity": "high"
  }
}
```

**Flow:**
1. Root agent detects crisis language pattern
2. Routes to `crisis_detection_agent` (highest priority)
3. Crisis agent uses `crisis_detection_tool` to analyze severity
4. Agent provides immediate crisis resources
5. Response includes hotline numbers and empathetic support

### 3. Knowledge-Based Question (RAG)

**Request:**
```bash
curl -X POST http://localhost:2003/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "message": "CBT là gì và nó hoạt động như thế nào?",
    "conversation_id": null,
    "history": []
  }'
```

**Expected Response:**
```json
{
  "response": "CBT (Cognitive Behavioral Therapy) là Liệu pháp Nhận thức Hành vi, một phương pháp tâm lý trị liệu dựa trên bằng chứng khoa học...",
  "agent_name": "RAG_agent",
  "conversation_id": null,
  "processing_time_ms": 1840,
  "metadata": {
    "user_id": "test-user-id",
    "documents_retrieved": "3"
  }
}
```

**Flow:**
1. Root agent identifies factual/educational question
2. Routes to `RAG_agent`
3. RAG agent uses `document_search_tool` to search knowledge base
4. Agent synthesizes retrieved documents into coherent answer
5. Response includes evidence-based information

### 4. With Conversation History

**Request:**
```bash
curl -X POST http://localhost:2003/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "message": "Vậy tôi nên làm gì tiếp theo?",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "history": [
      "Tôi đang lo lắng về kỳ thi sắp tới",
      "Lo lắng là cảm xúc bình thường. Bạn có thể thử kỹ thuật thở sâu",
      "Tôi đã thử nhưng vẫn còn lo",
      "Hãy thử viết ra những lo lắng cụ thể của bạn"
    ]
  }'
```

**Expected Response:**
```json
{
  "response": "Sau khi viết ra lo lắng, bước tiếp theo là thách thức những suy nghĩ tiêu cực:\n1. Hãy tự hỏi: 'Lo lắng này có cơ sở thực tế không?'\n2. Tìm bằng chứng ủng hộ và phản bác...",
  "agent_name": "CBT_agent",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "processing_time_ms": 1120,
  "metadata": {
    "user_id": "test-user-id"
  }
}
```

**Flow:**
1. `ChatContext` built with last 10 messages from history
2. Root agent uses context to understand conversation thread
3. Routes to `CBT_agent` (continuing therapy technique)
4. CBT agent provides next step in cognitive restructuring
5. Response maintains conversational continuity

## Key Components

### ChatRequest Model
```python
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: UUID | None = Field(None)
    history: list[str] = Field(default_factory=list, max_length=10)
```

### ChatContext Value Object
```python
class ChatContext(BaseModel):
    recent_messages: list[str] = Field(default_factory=list)
    sentiment: str | None = None
    detected_topics: list[str] = Field(default_factory=list)
    crisis_indicators: list[str] = Field(default_factory=list)
    session_duration_minutes: int = 0
```

### AgentResponse Value Object
```python
class AgentResponse(BaseModel):
    content: str
    agent_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    tokens_used: int = 0
    processing_time_ms: int
    metadata: dict[str, str] = Field(default_factory=dict)
```

### ChatResponseModel
```python
class ChatResponseModel(BaseModel):
    response: str
    agent_name: str
    conversation_id: UUID | None = None
    processing_time_ms: int
    metadata: dict[str, str] = Field(default_factory=dict)
```

## Error Handling

### Invalid Input
**Request:**
```json
{
  "message": "",
  "history": []
}
```

**Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### Processing Error
**Response (500 Internal Server Error):**
```json
{
  "detail": "Failed to process message: Agent initialization failed"
}
```

## Testing the Flow

1. Start the server:
```bash
make run
# or
uv run uvicorn app.main:app --reload --port 2003
```

2. Visit Swagger UI:
```
http://localhost:2003/docs
```

3. Test the `/api/v1/chat/` endpoint with sample requests

4. Monitor logs for agent routing:
```
INFO: Chat request from user test-user-id: message length=39, history length=0
INFO: Message routed through general_agent, processing time: 1250ms
INFO: Response generated by general_agent in 1250ms
```

## Next Steps

- Implement conversation persistence (requires repository implementation)
- Add streaming support for real-time responses
- Implement conversation history retrieval
- Add user feedback collection
- Implement session management
