# Multi-Agent AI Deep Researcher

A production-grade system for autonomous research using multiple specialized AI agents. This system combines web search, content extraction, and intelligent report generation to provide comprehensive research analysis.

**Status:** Phase 2 - Core Agent Implementation (Retriever & Reporter complete, Pydantic refactoring complete)

## Original Setup Instructions

1. Install Python 3.10+
   ```bash
   # Verify installation
   python --version
   ```

2. Install Ollama (for local LLM inference): https://ollama.ai
   ```bash
   # After installation, pull a model in another terminal:
   ollama pull mistral
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your Tavily API key and other settings
   ```

5. Run the application:
   ```bash
   python main.py  # (Coming in Phase 4 - LangGraph orchestration)
   ```

## Architecture Overview

```
User Query
  ↓
[Retriever Agent] → Searches web and extracts content
  ↓
[State Management] → LangGraph StateGraph with checkpoints
  ↓
[Summarizer Agent] → (Planned) Condenses findings
  ↓
[Critic Agent] → (Planned) Quality assessment
  ↓
[Insight Agent] → (Planned) Key finding extraction
  ↓
[Reporter Agent] → Generates professional markdown report
  ↓
Final Research Output
```

---

# Comprehensive Documentation

The following sections provide detailed technical documentation for development and deployment.

---

6. [Configuration](#configuration)
7. [Implementation Status](#implementation-status)
8. [API Documentation](#api-documentation)
9. [Usage Examples](#usage-examples)
10. [Design Decisions](#design-decisions)
11. [Development](#development)
12. [Troubleshooting](#troubleshooting)

---

## Overview

The Multi-Agent AI Deep Researcher is an intelligent system that automates the research process through specialized agents working together in a coordinated pipeline:

1. **Retriever Agent** - Discovers and extracts relevant information from the web
2. **Reporter Agent** - Compiles findings into professional markdown reports
3. **Future Agents** - Summarizer, Critic, and Insight agents (planned)

### Key Features

- **Multi-Source Retrieval**: Uses Tavily Search API for accurate, deduplicated web search results
- **Intelligent Scraping**: Extracts article content while handling paywalls and encoding issues
- **Source Tracking**: Records metadata about all sources for citation and credibility assessment
- **Confidence Scoring**: Algorithmic assessment of source reliability based on multiple factors
- **Production-Grade Architecture**: Pydantic validation, structured logging, error recovery
- **Extensible Design**: Clean agent interfaces for adding new research capabilities
- **State Management**: LangGraph-based state orchestration with checkpoint persistence

---

## Architecture

### System Design

```
User Query
    ↓
[Retriever Agent] ← Tavily Search API
    ↓ (Documents + Source Metadata)
    ↓
[State Management] ← LangGraph StateGraph + Checkpoints
    ↓
[Reporter Agent] ← (Future: other agents)
    ↓
Professional Markdown Report
```

### Agent Architecture

Each agent implements a standard interface:

```
BaseAgent
├── process(state: Dict[str, Any]) → StateUpdate
│   ├── Convert dict to Pydantic ResearchState
│   ├── Validate input
│   └── Execute agent logic
│
├── execute(state: ResearchState) → StateUpdate
│   └── [Implemented by each subclass]
│
└── Error Handling
    ├── Graceful degradation
    ├── Logging with correlation IDs
    └── Return dict updates instead of exceptions
```

### State Management

The `ResearchState` Pydantic model is the central hub for all agent communication:

```
ResearchState (Pydantic BaseModel)
├── messages: List[Dict] - Conversation history
├── user_query: str - Original research question
├── session_id: str - Unique session identifier
├── retrieved_docs: List[str] - Document content
├── source_metadata: Dict[str, SourceMetadata] - Citation info
├── summary: str - Summarization output
├── critique: CritiqueSummary - Quality assessment
├── insights: List[Insight] - Key findings
├── final_report: str - Markdown output
├── error_messages: List[str] - Error tracking
└── execution_metadata: Dict - Timing & performance data
```

**Key Design Decision**: Pydantic models with `to_dict()`/`from_dict()` methods for seamless LangGraph compatibility while maintaining strict type safety and validation.

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **LLM Framework** | LangGraph | ≥0.0.20 | Graph orchestration & state management |
| **LLM Inference** | Ollama + langchain-ollama | ≥0.1.0 | Local LLM execution (free, private) |
| **Web Search** | Tavily API | Latest | Intelligent web search with deduplication |
| **Web Scraping** | BeautifulSoup4 + Requests | ≥4.12.0 | HTML parsing & content extraction |
| **Data Validation** | Pydantic | ≥2.0.0 | Runtime type checking & validation |
| **Configuration** | pydantic-settings | ≥2.0.0 | Environment-based config management |
| **Logging** | Python JSON Logger | ≥2.0.7 | Structured JSON logging for production |
| **Resilience** | tenacity | ≥8.2.3 | Retry logic with exponential backoff |
| **Web UI** | Streamlit | ≥1.28.0 | Real-time research interface |
| **Embeddings** | sentence-transformers | ≥2.2.2 | Semantic search capabilities |
| **Vector Store** | FAISS | ≥1.7.4 | Efficient vector similarity search |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Ollama (for local LLM): https://ollama.ai
- Tavily API Key: https://tavily.com

### Installation

1. **Clone and Navigate**
   ```bash
   cd Submissions-C4/Group_3/multi_agent_ai_deep_researcher
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   # On Windows:
   .\.venv\Scripts\Activate.ps1
   # On Unix:
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your Tavily API key:
   # TAVILY_API_KEY=your_api_key_here
   ```

5. **Start Ollama (if not running)**
   ```bash
   ollama serve
   # In another terminal, pull a model:
   ollama pull mistral
   ```

6. **Test Installation**
   ```python
   python -c "from agents.retriever import RetrieverAgent; print('✓ Retriever ready')"
   python -c "from agents.reporter import ReporterAgent; print('✓ Reporter ready')"
   ```

---

## Project Structure

```
multi_agent_ai_deep_researcher/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # Configuration template
├── .gitignore                         # Git ignore rules
│
├── config.py                          # Pydantic Settings (environment config)
│
├── logging/
│   ├── __init__.py
│   └── logger.py                      # Structured JSON logging setup
│
├── utils/
│   ├── __init__.py
│   ├── state.py                       # Pydantic state models & helpers
│   ├── scraper.py                     # Web scraping with BeautifulSoup
│   ├── llm.py                         # Ollama LLM interface & streaming
│   └── search.py                      # (Future) Embedding-based search
│
├── agents/
│   ├── __init__.py
│   ├── base.py                        # Abstract BaseAgent class
│   ├── retriever.py                   # ✓ RAG-based document retrieval
│   ├── reporter.py                    # ✓ Markdown report generation
│   ├── summarizer.py                  # (Planned) Content summarization
│   ├── critic.py                      # (Planned) Quality assessment
│   ├── insight.py                     # (Planned) Key finding extraction
│   └── supervisor.py                  # (Planned) Agent orchestration
│
├── ui/
│   └── app.py                         # (Planned) Streamlit interface
│
├── main.py                            # (Planned) LangGraph StateGraph
│
└── data/
    ├── faiss_index/                   # FAISS vector indices
    ├── checkpoints/                   # LangGraph checkpoint storage
    └── sessions/                      # Session data
```

---

## Configuration

All configuration is managed through Pydantic Settings, supporting both `.env` files (development) and environment variables (production).

### Environment Variables

#### Ollama LLM Configuration
```bash
OLLAMA_BASE_URL=http://localhost:11434    # Ollama service endpoint
OLLAMA_MODEL=mistral                      # Model name to use
OLLAMA_TIMEOUT=300                        # Request timeout (seconds)
```

#### Web Search Configuration
```bash
TAVILY_API_KEY=your_api_key_here         # Tavily API key from https://tavily.com
```

#### Vector Store Configuration
```bash
FAISS_INDEX_PATH=./data/faiss_index      # Local FAISS index storage
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

#### Checkpoint & Session Configuration
```bash
CHECKPOINT_PATH=./data/checkpoints       # LangGraph checkpoint database
SESSION_MEMORY_TYPE=sqlite                # 'memory' or 'sqlite'
```

#### Research Pipeline Configuration
```bash
MAX_SOURCES_DEFAULT=10                    # Default number of sources to retrieve
MAX_REFINEMENT_PASSES=3                   # Max refinement iterations
CHUNK_SIZE=1000                           # Document chunk size for processing
```

#### Logging Configuration
```bash
LOG_LEVEL=INFO                            # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json                           # 'json' (structured) or 'text' (readable)
```

#### Feature Flags
```bash
ENABLE_SOURCE_TRACKING=true               # Track source metadata
ENABLE_STREAMING=true                     # Stream results in real-time
DEBUG_MODE=false                          # Enable debug logging
```

#### Retry Configuration
```bash
MAX_RETRIES=3                             # Maximum retry attempts
RETRY_WAIT_SECONDS=1                      # Initial wait between retries
```

### Configuration Loading

```python
from config import settings

# Access any setting
api_key = settings.tavily_api_key
max_sources = settings.max_sources_default
log_level = settings.log_level
```

Settings are validated at application startup using Pydantic, ensuring all required values are present and correctly typed.

---

## Implementation Status

### ✅ Completed (Phase 1 & 2)

#### Foundation & Core Infrastructure
- [x] **config.py** - Pydantic Settings with environment validation
- [x] **logging/logger.py** - Structured JSON logging with correlation IDs
- [x] **requirements.txt** - All production dependencies (25+ packages)
- [x] **.env.example** - Configuration template

#### State Management
- [x] **utils/state.py** - Pydantic models for state management
  - `ResearchState` - 21-field state model with helper methods
  - `SourceMetadata` - Citation & credibility tracking
  - `CritiqueSummary` - Quality assessment results
  - `Insight` - Key finding extraction

#### Agent Infrastructure
- [x] **agents/base.py** - Abstract agent interface
  - `process()` - Dict-to-Pydantic conversion for LangGraph
  - `execute()` - Agent-specific implementation
  - Validation & error handling
  - Execution timing & metadata tracking

#### Retriever Agent (RAG)
- [x] **agents/retriever.py** - Multi-source document retrieval
  - Tavily Search API integration (replaced DuckDuckGo)
  - Parallel web scraping with error recovery
  - Confidence scoring algorithm (0.0-1.0)
  - Source metadata tracking
  - Session-based logging

#### Reporter Agent
- [x] **agents/reporter.py** - Markdown report generation
  - 7-section report structure
  - Source credibility ratings (⭐ system)
  - Confidence visualization
  - Fallback report generation
  - Citation formatting

#### Utility Modules
- [x] **utils/scraper.py** - Web content extraction
  - BeautifulSoup HTML parsing
  - Metadata extraction (author, date, title)
  - Error recovery (paywall detection)
  - Pydantic ScraperResult models
  - Retry logic with exponential backoff

- [x] **utils/llm.py** - Ollama LLM interface
  - Lazy initialization pattern
  - Streaming token generation
  - Retry logic for resilience
  - LLMResponse Pydantic model
  - Token counting & cost estimation

#### Pydantic Refactoring ✅
- [x] state.py - TypedDict → Pydantic BaseModel
- [x] agents/base.py - Pydantic-aware process method
- [x] agents/retriever.py - SourceMetadata object handling
- [x] agents/reporter.py - Mixed format compatibility
- [x] utils/scraper.py - ScraperResult models
- [x] utils/llm.py - LLMResponse model

#### Technology Upgrades ✅
- [x] DuckDuckGo → Tavily API migration
  - Removed duplicate result handling
  - Simplified query logic
  - Better search quality & deduplication
  - Configuration integration

### ⏳ Planned (Phase 3-5)

#### Phase 3: Additional Agents
- [ ] **agents/summarizer.py** - Content summarization
- [ ] **agents/critic.py** - Quality assessment & fact-checking
- [ ] **agents/insight.py** - Key finding extraction
- [ ] **agents/supervisor.py** - Agent orchestration

#### Phase 4: Orchestration
- [ ] **main.py** - LangGraph StateGraph compilation
  - Node definitions for each agent
  - Conditional routing logic
  - Checkpoint setup
  - Graph compilation & invocation

#### Phase 5: UI & Hardening
- [ ] **ui/app.py** - Streamlit interface
  - Query input
  - Real-time streaming results
  - Report visualization
  - Session management
  
- [ ] Production hardening
  - Load testing
  - Error recovery drills
  - Security audit
  - Performance optimization

---

## API Documentation

### RetrieverAgent

**Purpose**: Searches the web for relevant sources and extracts their content.

**Class Signature**
```python
class RetrieverAgent(BaseAgent):
    def __init__(
        self,
        max_sources: int = 10,
        scrape_timeout: int = 10,
    )
```

**Parameters**
- `max_sources` (int): Maximum number of sources to retrieve (default: 10)
- `scrape_timeout` (int): Timeout for scraping each URL in seconds (default: 10)

**Methods**

#### `execute(state: ResearchState) → StateUpdate`
Executes the retrieval pipeline.

**Args**
- `state` (ResearchState): Current research state with user_query

**Returns**
- StateUpdate dict with:
  - `retrieved_docs` (List[str]): Document content
  - `source_metadata` (Dict[str, dict]): Source information
  - `current_step` (str): "retriever"
  - `iteration_count` (int): Incremented iteration
  - `error_messages` (List[str]): Any errors encountered

**Example**
```python
from utils.state import ResearchState
from agents.retriever import RetrieverAgent

agent = RetrieverAgent(max_sources=15)
state = ResearchState(
    user_query="What are the latest advances in quantum computing?",
    session_id="session-123",
)
result = agent.execute(state)
print(f"Retrieved {len(result['retrieved_docs'])} documents")
```

**Error Handling**
- Returns empty lists on failure, logs errors with correlation ID
- Continues scraping even if individual URLs fail
- Graceful degradation on network errors

---

### ReporterAgent

**Purpose**: Compiles retrieved documents and metadata into a professional markdown report.

**Class Signature**
```python
class ReporterAgent(BaseAgent):
    def __init__(self)
```

**Methods**

#### `execute(state: ResearchState) → StateUpdate`
Generates a comprehensive markdown report.

**Args**
- `state` (ResearchState): Research state with retrieved_docs & source_metadata

**Returns**
- StateUpdate dict with:
  - `final_report` (str): Markdown-formatted report
  - `current_step` (str): "reporter"
  - `report_generated_at` (str): ISO timestamp
  - `error_messages` (List[str]): Any generation errors

**Report Structure**
1. **Title** - Query as main heading
2. **Executive Summary** - High-level overview of findings
3. **Key Findings** - Top 5 most important discoveries
4. **Source Analysis** - Table of sources with credibility ratings
5. **Detailed Analysis** - In-depth information from sources
6. **Insights** - Extracted key points with confidence scores
7. **Recommendations** - Suggested next steps
8. **References** - Numbered citations with metadata

**Example**
```python
from agents.reporter import ReporterAgent

agent = ReporterAgent()
report_update = agent.execute(state)
print(report_update['final_report'])
# Outputs markdown-formatted report
```

**Confidence Visualization**
- **Source Credibility**: ⭐⭐⭐ (High ≥0.8), ⭐⭐ (Medium ≥0.6), ⭐ (Low <0.6)
- **Insight Confidence**: Visual bar (█/░) with percentage
  - Example: "████░ 85%" for 85% confidence

---

### BaseAgent

**Purpose**: Abstract base class defining the agent interface.

**Class Signature**
```python
class BaseAgent(ABC):
    def __init__(self, name: str)
    
    @abstractmethod
    def execute(self, state: ResearchState) → StateUpdate
    
    def process(self, state: Dict[str, Any]) → StateUpdate
```

**Key Methods**

#### `process(state: Dict[str, Any]) → StateUpdate`
Entry point for LangGraph integration. Converts dict to Pydantic model and calls `execute()`.

- Handles dict-to-Pydantic conversion
- Validates input using Pydantic
- Measures execution time
- Logs with session correlation ID
- Handles exceptions gracefully

#### `execute(state: ResearchState) → StateUpdate`
Abstract method for subclasses to implement. Must return a dict with state updates.

---

### State Models

#### ResearchState
Central state model for all agent communication.

**Fields**
```python
class ResearchState(BaseModel):
    # Query & Session
    user_query: str                          # Research question
    session_id: str                          # Unique session ID
    
    # Document & Source Data
    messages: List[Dict[str, Any]] = []      # Conversation history
    retrieved_docs: List[str] = []           # Document content
    source_metadata: Dict[str, dict] = {}    # Citation info (SourceMetadata objects)
    
    # Processing & Results
    summary: str = ""                        # Summarization output
    critique: Optional[dict] = None          # Quality assessment (CritiqueSummary)
    insights: List[dict] = []                # Key findings (Insight objects)
    final_report: str = ""                   # Markdown output
    
    # Progress & Metadata
    current_step: str = "init"               # Current agent step
    iteration_count: int = 0                 # Refinement iterations
    total_iterations: int = 1                # Max iterations
    needs_refinement: bool = False           # Needs additional passes
    error_messages: List[str] = []           # Error tracking
    report_generated_at: Optional[str] = None  # Report generation timestamp
    total_sources_used: int = 0              # Final source count
    execution_metadata: Dict[str, Any] = {}  # Timing per agent
```

**Helper Methods**
```python
state.add_error(message: str)        # Add error message
state.add_document(doc: str)         # Append document
state.add_insight(text, confidence)  # Add insight
state.to_dict()                      # Serialize to dict (LangGraph)
state.from_dict(data: dict)          # Deserialize from dict (LangGraph)
```

#### SourceMetadata
Citation and credibility information for each source.

```python
class SourceMetadata(BaseModel):
    url: str                         # Source URL (required)
    title: str = ""                  # Article title
    snippet: str = ""                # Search result snippet
    excerpt: str = ""                # First N chars of content
    timestamp: str                   # ISO datetime (auto)
    confidence: float                # 0.0-1.0 credibility score
    domain: str = ""                 # Domain name
    author: Optional[str] = None     # Article author
```

#### CritiqueSummary
Quality assessment and fact-checking results.

```python
class CritiqueSummary(BaseModel):
    strengths: List[str] = []              # Strong points
    weaknesses: List[str] = []             # Problem areas
    contradictions: List[str] = []         # Conflicting info
    sources_flagged: List[str] = []        # Unreliable sources
    needs_refinement: bool = False         # Requires more research
    coverage_score: float = 0.0            # 0.0-1.0 topic coverage
```

#### Insight
Key finding with confidence assessment.

```python
class Insight(BaseModel):
    text: str                        # Finding text
    confidence: float                # 0.0-1.0 confidence
    supporting_sources: List[str] = []  # Source URLs
    reasoning: str = ""              # Why this is important
```

---

## Usage Examples

### Basic Research Pipeline

```python
from utils.state import ResearchState
from agents.retriever import RetrieverAgent
from agents.reporter import ReporterAgent
import uuid

# Initialize agents
retriever = RetrieverAgent(max_sources=15)
reporter = ReporterAgent()

# Create research session
session_id = str(uuid.uuid4())
state = ResearchState(
    user_query="What are the latest developments in renewable energy?",
    session_id=session_id,
)

# Step 1: Retrieve sources
print("🔍 Retrieving sources...")
retrieval_result = retriever.execute(state)
state.retrieved_docs = retrieval_result['retrieved_docs']
state.source_metadata = retrieval_result['source_metadata']
state.iteration_count = retrieval_result['iteration_count']
print(f"✓ Retrieved {len(state.retrieved_docs)} documents")

# Step 2: Generate report
print("\n📝 Generating report...")
report_result = reporter.execute(state)
state.final_report = report_result['final_report']
print("✓ Report generated")

# Display report
print("\n" + "="*80)
print(state.final_report)
print("="*80)
```

### Custom Logging Context

```python
from logging.logger import get_logger_with_context

logger = get_logger_with_context()

# Logs include session_id, agent, step, iteration automatically
logger.info_with_context(
    "Processing query",
    session_id=session_id,
    agent="retriever",
    step="search",
    iteration=0,
)
```

### Streaming LLM Responses

```python
from utils.llm import stream_llm

prompt = "Summarize the key findings from these documents: ..."
print("🤖 Generating summary:")

for token in stream_llm(prompt, max_tokens=500):
    print(token, end="", flush=True)
print()
```

### Error Handling & Recovery

```python
from agents.retriever import RetrieverAgent

agent = RetrieverAgent()

try:
    result = agent.execute(state)
    if result.get('error_messages'):
        print(f"⚠️ Warnings: {result['error_messages']}")
    else:
        print("✓ Retrieval successful")
except Exception as e:
    print(f"❌ Critical error: {e}")
    # Implement fallback logic
```

---

## Design Decisions

### 1. Pydantic for Type Safety

**Decision**: Use Pydantic BaseModel instead of TypedDict for all state and data models.

**Rationale**
- Runtime validation catches errors early
- IDE autocomplete and type checking
- Automatic serialization/deserialization
- Field descriptions for documentation
- Easy integration with LangGraph

**Implementation**
```python
from pydantic import BaseModel, Field, ConfigDict

class ResearchState(BaseModel):
    model_config = ConfigDict(extra="allow")
    user_query: str = Field(description="Research question")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for LangGraph compatibility"""
        return self.model_dump(mode="json")
```

### 2. Tavily Search API Over DuckDuckGo

**Decision**: Replace DuckDuckGo with Tavily for web search.

**Rationale**
- Tavily provides deduplicated, high-quality results
- Official API with better reliability
- No need for query variation logic
- Faster search execution
- Better structured result format
- Supports content extraction hints

**Tradeoff**: Requires API key, but free tier available at https://tavily.com

### 3. Agent-Based Architecture

**Decision**: Structure system as independent agents with standard interface.

**Rationale**
- Separation of concerns (each agent has single responsibility)
- Easy to test and debug individually
- Simple to add new agents
- Natural fit for LangGraph orchestration
- Enables parallel execution when appropriate

**Interface**
```python
class BaseAgent(ABC):
    def process(self, state: Dict) → StateUpdate  # LangGraph entry
    def execute(self, state: ResearchState) → StateUpdate  # Agent logic
```

### 4. Structured JSON Logging

**Decision**: Use structured JSON logging with correlation IDs.

**Rationale**
- Production-grade observability
- Easy to parse and analyze logs
- Correlation IDs trace requests through agents
- Session tracking for debugging
- Metrics can be extracted from logs

**Fields**: timestamp, level, logger, module, function, line_number, session_id, agent, step, iteration, execution_time_ms, exception

### 5. Graceful Degradation

**Decision**: Agents return partial results on failure instead of throwing exceptions.

**Rationale**
- Pipeline continues despite individual failures
- Better user experience (get some results vs. none)
- Easier error tracking and recovery
- Suitable for web operations (some URLs always fail)

**Implementation** All agents return StateUpdate dict with error_messages list

---

## Development

### Setting Up Development Environment

```bash
# Virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows

# Install with dev dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8

# Run tests
pytest tests/

# Format code
black agents/ utils/ config.py

# Lint code
flake8 agents/ utils/
```

### Code Style

- **Formatting**: Black (line length 100)
- **Linting**: flake8 with max line length 100
- **Type hints**: Full coverage, Pydantic models preferred
- **Docstrings**: Google style, include Args/Returns/Raises
- **Comments**: Explain "why", not "what"

### Adding a New Agent

1. **Create agent file** `agents/new_agent.py`
2. **Inherit from BaseAgent**
```python
from agents.base import BaseAgent
from utils.state import ResearchState, StateUpdate

class NewAgent(BaseAgent):
    def __init__(self):
        super().__init__("new_agent")
    
    def execute(self, state: ResearchState) → StateUpdate:
        # Implement agent logic
        return {
            "current_step": "new_agent",
            # ... state updates
        }
```

3. **Add unit tests** in `tests/test_new_agent.py`
4. **Update** `agents/__init__.py` to export
5. **Document** in API Documentation section
6. **Integrate** in `main.py` StateGraph

### Testing

```bash
# Simple test
def test_retriever_basic():
    from agents.retriever import RetrieverAgent
    from utils.state import ResearchState
    
    agent = RetrieverAgent()
    state = ResearchState(
        user_query="test",
        session_id="test-123"
    )
    result = agent.execute(state)
    assert "retrieved_docs" in result

# Run
pytest tests/test_retriever.py -v
```

---

## Troubleshooting

### Common Issues

#### 1. Missing TAVILY_API_KEY

**Error**: `ValueError: tavily_api_key is required`

**Solution**
```bash
# Check .env file
cat .env | grep TAVILY

# Add if missing
echo "TAVILY_API_KEY=your_key_here" >> .env

# Get key from https://tavily.com/
```

#### 2. Ollama Connection Failed

**Error**: `OllamaConnectionError: Failed to connect to Ollama at http://localhost:11434`

**Solution**
```bash
# Verify Ollama is running
ollama --version  # Should show version

# Start Ollama
ollama serve

# In another terminal, pull a model
ollama pull mistral

# Test connection
python -c "from utils.llm import get_llm; get_llm(); print('✓ Connected')"
```

#### 3. Insufficient Content Scraped

**Error**: Many sources are skipped with "insufficient content" warning

**Solution**
- This is normal for some sites (e.g., news indices)
- Lower the content threshold in `agents/retriever.py` line 50 from `50` (min chars)
- Check logs to see which domains fail:
```bash
# Run with more verbose logging
LOG_LEVEL=DEBUG python your_script.py
```

#### 4. Import Errors

**Error**: `ModuleNotFoundError: No module named 'agents'`

**Solution**
```bash
# Verify you're in correct directory
pwd  # Should end in multi_agent_ai_deep_researcher

# Reinstall package in editable mode
pip install -e .
```

#### 5. Pydantic Validation Error

**Error**: `ValidationError: 1 validation error for ResearchState`

**Solution**
Check that all required fields are provided:
```python
# ✗ Missing session_id
state = ResearchState(user_query="test")

# ✓ Correct
state = ResearchState(
    user_query="test",
    session_id="session-123"
)
```

### Debug Mode

Enable detailed logging:

```bash
# In .env
LOG_LEVEL=DEBUG
DEBUG_MODE=true

# Or in code
from config import settings
settings.log_level = "DEBUG"
```

### Performance Optimization

**Slow Retrieval?**
- Reduce `MAX_SOURCES_DEFAULT` in `.env`
- Increase `OLLAMA_TIMEOUT` if network is slow
- Check Tavily API quota

**Large Memory Usage?**
- Use `SESSION_MEMORY_TYPE=memory` only for testing
- Switch to `SESSION_MEMORY_TYPE=sqlite` (default) for persistence
- Monitor checkpoint database size: `du -h ./data/checkpoints/checkpoints.db`

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create branch**: `git checkout -b feature/your-feature`
3. **Implement** with tests
4. **Format code**: `black agents/ utils/`
5. **Run tests**: `pytest tests/`
6. **Commit**: `git commit -m "Add: Clear description"`
7. **Push**: `git push origin feature/your-feature`
8. **Submit PR** with description and test results

### Priority Contributions

- [ ] Integration tests for agent pipeline
- [ ] Supervisor agent for orchestration
- [ ] Streamlit UI implementation
- [ ] Performance benchmarking
- [ ] Additional LLM provider support

---

## License

This project is part of a hackathon submission and is provided as-is.

---

## Support

For issues, feature requests, or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review [Architecture](#architecture) documentation
- Check logs: Look in `./data/logs/` or terminal output with `LOG_LEVEL=DEBUG`
- Verify [Configuration](#configuration) is correct

---

## Project Timeline

- **Phase 1** ✅ (Complete) - Foundation & dependencies
- **Phase 2** ✅ (Complete) - Retriever & Reporter agents + Pydantic refactoring
- **Phase 3** 🚧 (Planned) - Summarizer, Critic, Insight agents
- **Phase 4** 🚧 (Planned) - LangGraph orchestration & main.py
- **Phase 5** 🚧 (Planned) - Streamlit UI & production hardening

---

**Last Updated**: February 15, 2026  
**Status**: Phase 2 Complete - Production-Ready Retriever & Reporter Agents