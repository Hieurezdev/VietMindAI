# VietMindAI-ADK

🧠 **AI-Powered Mental Health Assistant** using hierarchical agentic architecture

Built with Google's ADK (Agent Development Kit), FastAPI, and Gemini 2.5 Flash for providing empathetic, intelligent mental health support with safety-first crisis detection.

## 🎯 Overview

MindAI-ADK is a sophisticated mental health AI assistant that uses a **hierarchical multi-agent system** to provide:

- ✅ **Crisis Detection & Intervention**: Automatic detection and handling of mental health emergencies
- ✅ **Empathetic Conversations**: Context-aware, supportive dialogue for mental wellness
- ✅ **RAG-Enhanced Responses**: Knowledge retrieval with hybrid search and reranking
- ✅ **Specialized Therapeutic Agents**: CBT, mindfulness, and general mental health support
- ✅ **ReAct Framework**: Systematic reasoning and action for agent orchestration

### 🤖 Agent Architecture

```
Root Agent (ReAct Orchestrator)
├── Crisis Detection Agent ⚠️
│   ├── Google Search Integration
│   └── Emergency Protocol Tools
├── General Agent 💬
│   └── Basic Mental Health Support
├── RAG Agent 📚
│   ├── Hybrid Search (Vector + Atlas)
│   ├── Document Reranking
│   └── Answer Generation
├── CBT Agent 🧘 (Cognitive Behavioral Therapy)
└── Mindfulness Agent 🌸 (Meditation & Wellness)
```

**Root Agent** uses a ReAct (Reasoning and Acting) framework to:
1. **Observe** user messages for emotional indicators and crisis signals
2. **Think** about appropriate routing and safety protocols
3. **Act** by delegating to specialized sub-agents
4. **Monitor** responses and ensure user safety

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL with pgvector extension
- Google Gemini API key

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
exec $SHELL

# Clone and setup project
git clone <your-repo>
cd MindAI-ADK

# Install dependencies and setup hooks
make setup
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required environment variables:
- `GEMINI_API_KEY`: Your Google Gemini API key (primary LLM)
- `DATABASE_URL`: PostgreSQL connection with pgvector support
- `ENV`: Environment (dev/prod)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

### Development

```bash
# Run the development server
make dev
# or
make run

# Format code
make format

# Run linting
make lint

# Run type checking
make type

# Run tests
make test

# Run all pre-commit hooks
make hooks
```

## 📁 Project Architecture

This project follows **hexagonal architecture** with agentic AI components:

```
app/
├── agents/                  # Multi-agent system
│   ├── agent.py            # Root agent (ReAct orchestrator)
│   ├── prompt.py           # Root agent instructions
│   └── sub_agents/         # Specialized agents
│       ├── crisis_detection_agent/  # Crisis handling
│       ├── general_agent/           # General support
│       ├── RAG_agent/              # Knowledge retrieval
│       ├── CBT_agent/              # CBT therapy
│       └── mindfulness_agent/      # Mindfulness guidance
├── api/                    # FastAPI routes and transport
├── core/                   # Domain logic and use cases
├── services/               # Application services (LLM, embeddings)
├── infra/                  # Infrastructure (DB, vector store)
└── config/                 # Configuration and logging
```

### 🔒 Safety-First Design

**Crisis Detection Protocol:**
- Automatic detection of suicide ideation, self-harm, or severe distress
- Immediate routing to Crisis Detection Agent
- `disallow_transfer_to_parent = True` prevents escalation loops
- Integration with emergency resources and search tools

## 🛠️ Technology Stack

### Mandatory Technologies
- **LLM**: Google Gemini 2.5 Flash (ONLY)
- **Agent Framework**: Google ADK (Agent Development Kit)
- **API**: FastAPI + Pydantic v2
- **Database**: PostgreSQL + pgvector
- **Embeddings**: gemini-embedding-001
- **Monitoring**: Langfuse
- **Package Manager**: uv

### Forbidden Technologies
❌ NO Langchain, LlamaIndex, or other LLM frameworks
❌ NO OpenAI, Claude, Cohere (only Gemini)
❌ NO SQLite, MySQL, ChromaDB, Pinecone
❌ NO Flask, Django

## 📖 API Documentation

Once running, access the API at `http://localhost:2003`:
- Swagger UI: http://localhost:2003/docs
- ReDoc: http://localhost:2003/redoc
- Health Check: http://localhost:2003/health

## 🧪 Development Tools

- **uv**: Fast Python package manager
- **FastAPI**: Modern async web framework
- **Pre-commit**: Code quality hooks
- **Ruff**: Fast linting and formatting
- **MyPy**: Strict type checking
- **Pytest**: Testing framework
- **Google ADK**: Agent orchestration

## 📋 Make Commands

- `make setup`: Install dependencies and setup pre-commit hooks
- `make run`: Start development server on port 2003
- `make format`: Auto-format code with ruff and isort
- `make lint`: Run linting checks
- `make type`: Run mypy type checking
- `make test`: Run pytest test suite
- `make hooks`: Run all pre-commit hooks
- `make clean`: Clean cache files

## 🎨 Code Quality Standards

All code must meet these standards:
- ✅ **100% Type Hints**: All functions and methods
- ✅ **Async/Await**: All I/O operations must be async
- ✅ **Error Handling**: Try-catch blocks in all service methods
- ✅ **Structured Logging**: All operations logged
- ✅ **Pydantic Validation**: All API input/output
- ✅ **Docstrings**: All classes and public methods

### Naming Conventions
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

## 🌟 Key Features

### 1. **ReAct Agent Orchestration**
The Root Agent follows a systematic ReAct framework:
- **Observation**: Analyzes user emotional state and crisis indicators
- **Thought**: Reasons about routing and safety protocols
- **Action**: Delegates to specialized sub-agents
- **Repeat**: Monitors and iterates until user needs are met

### 2. **Crisis Detection**
Advanced mental health crisis detection with:
- Keyword analysis for suicide ideation and self-harm
- Emotional tone and urgency assessment
- Immediate escalation to crisis agent
- Google Search integration for emergency resources

### 3. **RAG-Enhanced Responses**
Hybrid search system combining:
- Vector similarity search (pgvector)
- Atlas text search
- Document reranking for relevance
- Context-aware answer generation

### 4. **Multilingual Support**
Primarily Vietnamese language for mental health context in Vietnam, with English support for technical documentation.

## 🤝 Contributing

1. Follow the hexagonal architecture
2. Use Google ADK for all agent implementations
3. Maintain 100% type hint coverage
4. Run `make hooks` before committing
5. Add tests for new features
6. Document all public APIs

## 📄 License

MIT License

## ⚠️ Disclaimer

This is an AI assistant for mental health support and **not a replacement** for professional medical care. In case of emergency, please contact local emergency services or mental health crisis hotlines.
