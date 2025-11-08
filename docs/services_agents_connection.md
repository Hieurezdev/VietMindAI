# Services and Agents Connection Map

## Overview

This document shows how services connect with ADK agents in the VietMindAI codebase.

## Connection Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        API Layer (FastAPI)                          │
│                   app/api/routers/chat.py                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Depends(get_agent_orchestration_service)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Dependency Injection Layer                       │
│                    app/api/dependencies.py                          │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │ get_agent_orchestration_service() → AgentOrchestrationService  │
│  │ get_crisis_detection_service() → CrisisDetectionService    │    │
│  │ get_llm_service_adapter() → LLMServiceAdapter              │    │
│  │ get_embedding_service_adapter() → EmbeddingServiceAdapter  │    │
│  └───────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ imports from
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Infrastructure Adapters                          │
│                    app/infra/adapters/                              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │ agent_orchestration_service.py                          │      │
│  │ - AgentOrchestrationService                             │      │
│  │ - __init__(root_agent: Agent) ← CONNECTS TO AGENTS      │      │
│  │ - route_message() → runs root_agent.run_async()         │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │ crisis_detection_service.py                             │      │
│  │ - CrisisDetectionService                                │      │
│  │ - Uses LLMServiceAdapter for analysis                   │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │ llm_service_adapter.py                                  │      │
│  │ - LLMServiceAdapter (implements ILLMService)            │      │
│  │ - Wraps app/services/llm_service.py                     │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │ embedding_service_adapter.py                            │      │
│  │ - EmbeddingServiceAdapter (implements IEmbeddingService)│      │
│  │ - Wraps app/services/embedding_service.py               │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  __init__.py exports all adapters                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ imports root_agent from
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        ADK Agents Layer                             │
│                        app/agents/                                  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │ agent.py                                                │      │
│  │ - root_agent = Agent(...)                              │      │
│  │ - sub_agents = [general_agent, crisis_detection_agent] │      │
│  │ - Uses prompt.py for instructions                      │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │ sub_agents/general_agent/agent.py                       │      │
│  │ - general_agent = Agent(...)                            │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │ sub_agents/crisis_detection_agent/agent.py              │      │
│  │ - crisis_detection_agent = Agent(...)                   │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │ tools/crisis_detection_tool.py                          │      │
│  │ - detect_crisis_indicators() function                   │      │
│  │ - Uses CrisisDetectionService                           │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │ tools/document_search_tool.py                           │      │
│  │ - search_knowledge_base() function                      │      │
│  │ - Uses DocumentUseCases                                 │      │
│  └─────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Connection Files

### 1. **app/api/dependencies.py** (Main Connection Hub)

This is the **primary connection point** between services and agents.

```python
# Lines 10, 44-46: Connects root_agent to AgentOrchestrationService
from app.agents.agent import root_agent

@lru_cache(maxsize=1)
def get_agent_orchestration_service() -> AgentOrchestrationService:
    """Get agent orchestration service singleton."""
    return AgentOrchestrationService(root_agent)  # ← CONNECTS HERE
```

**Location**: `app/api/dependencies.py:10, 44-46`

**What it does**:
- Imports `root_agent` from `app/agents/agent.py`
- Creates `AgentOrchestrationService` with `root_agent` as parameter
- Provides singleton instance via `@lru_cache`
- Used by FastAPI dependency injection in chat router

---

### 2. **app/infra/adapters/agent_orchestration_service.py** (Bridge Service)

This adapter **bridges core domain with ADK agents**.

```python
# Lines 7, 18-24: Stores and uses root_agent
from google.adk.agents import Agent

class AgentOrchestrationService(IAgentOrchestrationService):
    def __init__(self, root_agent: Agent) -> None:
        """Initialize agent orchestration service.

        Args:
            root_agent: The root ADK agent that routes to sub-agents.
        """
        self._root_agent = root_agent  # ← STORES AGENT HERE
        self._agents_registry: dict[str, Agent] = {}
```

**Location**: `app/infra/adapters/agent_orchestration_service.py:18-24`

**What it does**:
- Receives `root_agent` in constructor
- Stores it as `self._root_agent`
- Uses it in `route_message()` method to run agent chain
- Implements `IAgentOrchestrationService` interface from core domain

---

### 3. **app/agents/agent.py** (Agent Definition)

This file **creates and exports the root_agent**.

```python
# Lines 1-19: Creates root_agent with sub-agents
from google.adk.agents import Agent
from config.config import get_settings
from .prompt import root_agent_instruction
from .sub_agents.general_agent.agent import general_agent
from .sub_agents.crisis_detection_agent.agent import crisis_detection_agent

root_agent = Agent(
    name="root_agent",
    model=get_settings().gemini_model,
    description="Root agent có nhiệm vụ điều phối và chuyển giao các câu hỏi đến các sub agent phù hợp",
    instruction=root_agent_instruction,
    sub_agents=[general_agent, crisis_detection_agent]  # ← SUB-AGENTS HERE
)
```

**Location**: `app/agents/agent.py:14-19`

**What it does**:
- Creates Google ADK `Agent` instance
- Sets up hierarchical agent structure with sub_agents
- Uses settings for model configuration
- Exported and used by `dependencies.py`

---

### 4. **app/infra/adapters/__init__.py** (Adapter Exports)

This file **exports all adapters** for easy importing.

```python
# Lines 1-13: Exports all adapter services
from app.infra.adapters.agent_orchestration_service import AgentOrchestrationService
from app.infra.adapters.crisis_detection_service import CrisisDetectionService
from app.infra.adapters.embedding_service_adapter import EmbeddingServiceAdapter
from app.infra.adapters.llm_service_adapter import LLMServiceAdapter

__all__ = [
    "LLMServiceAdapter",
    "EmbeddingServiceAdapter",
    "CrisisDetectionService",
    "AgentOrchestrationService",
]
```

**Location**: `app/infra/adapters/__init__.py`

**What it does**:
- Centralized export point for all adapters
- Used by `dependencies.py` to import services
- Keeps imports clean and organized

---

### 5. **app/agents/tools/** (Agent Tools Using Services)

Agent tools **use services to provide functionality to ADK agents**.

**crisis_detection_tool.py**:
```python
# Lines 10, 15-16: Uses CrisisDetectionService
from app.infra.adapters import CrisisDetectionService, LLMServiceAdapter

_llm_adapter = LLMServiceAdapter()
_crisis_service = CrisisDetectionService(_llm_adapter)

async def detect_crisis_indicators(...):
    indicators = await _crisis_service.analyze_message(message, context)
    # Returns crisis analysis results
```

**document_search_tool.py**:
```python
# Lines 9, 46-48: Uses DocumentUseCases
from app.core.use_cases.document_use_cases import DocumentUseCases
from app.infra.adapters import EmbeddingServiceAdapter

_embedding_adapter = EmbeddingServiceAdapter()
_document_use_cases = DocumentUseCases(_mock_repo, _embedding_adapter)

async def search_knowledge_base(...):
    retrieved_docs = await _document_use_cases.search_documents(...)
    # Returns search results
```

**Location**:
- `app/agents/tools/crisis_detection_tool.py:10, 15-16`
- `app/agents/tools/document_search_tool.py:9, 46-48`

---

## Connection Flow Summary

### Step-by-Step Flow:

1. **Chat Router** (`app/api/routers/chat.py`) receives user request
   - Uses `Depends(get_agent_orchestration_service)` for DI

2. **Dependencies** (`app/api/dependencies.py`) provides service
   - `get_agent_orchestration_service()` creates `AgentOrchestrationService(root_agent)`
   - Imports `root_agent` from `app/agents/agent.py`

3. **Agent Orchestration Service** (`app/infra/adapters/agent_orchestration_service.py`)
   - Receives `root_agent` in `__init__()`
   - Stores as `self._root_agent`
   - Calls `self._root_agent.run_async(context_state)` in `route_message()`

4. **Root Agent** (`app/agents/agent.py`)
   - ADK Agent with sub_agents list
   - Routes to appropriate sub-agent based on message
   - Sub-agents use tools if needed

5. **Agent Tools** (`app/agents/tools/`)
   - Import and use services (CrisisDetectionService, DocumentUseCases, etc.)
   - Services use LLMServiceAdapter, EmbeddingServiceAdapter
   - Return results to agents

6. **Response Flow**
   - Agent generates response
   - `AgentOrchestrationService` collects response
   - Returns `AgentResponse` value object
   - Chat router maps to `ChatResponseModel`
   - User receives JSON response

---

## Key Files and Their Roles

| File | Role | Connects To |
|------|------|-------------|
| `app/api/dependencies.py` | **Main Hub** - DI provider | Imports `root_agent`, creates services |
| `app/infra/adapters/agent_orchestration_service.py` | **Bridge** - Connects domain to ADK | Receives and runs `root_agent` |
| `app/agents/agent.py` | **Agent Definition** - Creates root_agent | Exports agent to dependencies |
| `app/infra/adapters/__init__.py` | **Exports** - Central adapter exports | Used by dependencies.py |
| `app/agents/tools/*.py` | **Tools** - Agent functionality | Import and use services |
| `app/services/*.py` | **Core Services** - LLM, Embeddings | Wrapped by adapters |

---

## Import Chain

```python
# Complete import chain from API to Agents:

# 1. Chat Router
from app.api.dependencies import get_agent_orchestration_service

# 2. Dependencies
from app.agents.agent import root_agent
from app.infra.adapters import AgentOrchestrationService

# 3. Adapters __init__
from app.infra.adapters.agent_orchestration_service import AgentOrchestrationService

# 4. Agent Orchestration Service
from google.adk.agents import Agent

# 5. Root Agent
from google.adk.agents import Agent
from .sub_agents.general_agent.agent import general_agent
from .sub_agents.crisis_detection_agent.agent import crisis_detection_agent

# 6. Agent Tools
from app.infra.adapters import CrisisDetectionService, EmbeddingServiceAdapter
from app.core.use_cases.document_use_cases import DocumentUseCases
```

---

## Folder Structure

```
app/
├── api/
│   ├── dependencies.py          ← MAIN CONNECTION HUB
│   └── routers/
│       └── chat.py              ← Uses dependencies
│
├── infra/
│   └── adapters/
│       ├── __init__.py          ← Exports adapters
│       ├── agent_orchestration_service.py  ← BRIDGE TO AGENTS
│       ├── crisis_detection_service.py
│       ├── llm_service_adapter.py
│       └── embedding_service_adapter.py
│
├── agents/
│   ├── agent.py                 ← DEFINES ROOT_AGENT
│   ├── prompt.py
│   ├── sub_agents/
│   │   ├── general_agent/
│   │   │   └── agent.py
│   │   └── crisis_detection_agent/
│   │       └── agent.py
│   └── tools/
│       ├── crisis_detection_tool.py  ← Uses services
│       └── document_search_tool.py   ← Uses services
│
├── services/
│   ├── llm_service.py           ← Core LLM logic
│   └── embedding_service.py     ← Core embedding logic
│
└── core/
    ├── ports/
    │   └── services.py          ← Interfaces (ILLMService, etc.)
    └── use_cases/
        └── document_use_cases.py
```

---

## How Services Connect to Agents

### Connection Point 1: AgentOrchestrationService receives root_agent

**File**: `app/api/dependencies.py:44-46`

```python
@lru_cache(maxsize=1)
def get_agent_orchestration_service() -> AgentOrchestrationService:
    return AgentOrchestrationService(root_agent)  # ← CONNECTION
```

### Connection Point 2: Agent tools import services

**File**: `app/agents/tools/crisis_detection_tool.py:10, 15-16`

```python
from app.infra.adapters import CrisisDetectionService, LLMServiceAdapter

_llm_adapter = LLMServiceAdapter()
_crisis_service = CrisisDetectionService(_llm_adapter)  # ← CONNECTION
```

### Connection Point 3: Services wrapped by adapters

**File**: `app/infra/adapters/llm_service_adapter.py`

```python
from app.services.llm_service import LLMService

class LLMServiceAdapter(ILLMService):
    def __init__(self):
        self._llm_service = LLMService()  # ← CONNECTION
```

---

## Summary

The **main connection file** is:

### **`app/api/dependencies.py`**

This file:
1. Imports `root_agent` from `app/agents/agent.py` (line 10)
2. Creates `AgentOrchestrationService(root_agent)` (line 46)
3. Provides singleton services for FastAPI dependency injection
4. Acts as the bridge between API layer and agents layer

The **adapter folder** is:

### **`app/infra/adapters/`**

This folder contains all bridge services that connect core domain with infrastructure:
- `agent_orchestration_service.py` - Runs ADK agents
- `crisis_detection_service.py` - Crisis detection logic
- `llm_service_adapter.py` - Wraps LLM service
- `embedding_service_adapter.py` - Wraps embedding service
