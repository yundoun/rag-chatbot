# RAG Chatbot Technical Architecture Proposal

**Project:** Internal Document Search RAG Chatbot
**Version:** 1.0
**Date:** 2025-12-11
**Author:** Tech Architect Agent

---

## 1. Executive Summary

This document presents the technical architecture for a Lightweight Single-Agent + Corrective RAG + HITL (Human-in-the-Loop) chatbot system. The design prioritizes maintainability, extensibility, and production readiness while keeping MVP scope manageable.

### Confirmed Tech Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Framework | LangGraph | >=0.2.0 | State machine orchestration |
| Vector DB | ChromaDB | >=0.4.0 | Document embedding storage |
| LLM | OpenAI GPT-4o | Latest | Question analysis, response generation |
| Web Search | Tavily API | Latest | Fallback search |
| UI | Streamlit | >=1.28.0 | User interface |
| Language | Python | >=3.10 | Core development |

---

## 2. Project Directory Structure

```
rag-chatbot/
├── src/
│   ├── __init__.py
│   ├── main.py                      # Application entry point
│   │
│   ├── core/                        # Core business logic
│   │   ├── __init__.py
│   │   ├── orchestrator.py          # LangGraph workflow orchestration
│   │   ├── state.py                 # State definitions (TypedDict)
│   │   └── exceptions.py            # Custom exceptions
│   │
│   ├── agents/                      # Agent components
│   │   ├── __init__.py
│   │   ├── query_processor.py       # Query analysis
│   │   ├── hitl_controller.py       # Human-in-the-loop logic
│   │   ├── agentic_controller.py    # Complex query decomposition
│   │   └── web_search_agent.py      # Tavily web search
│   │
│   ├── rag/                         # RAG-specific components
│   │   ├── __init__.py
│   │   ├── corrective_engine.py     # Corrective RAG logic
│   │   ├── retriever.py             # Document retrieval
│   │   ├── relevance_evaluator.py   # Document relevance scoring
│   │   └── response_generator.py    # Answer generation
│   │
│   ├── vectorstore/                 # Vector database management
│   │   ├── __init__.py
│   │   ├── manager.py               # ChromaDB operations
│   │   ├── embeddings.py            # Embedding provider abstraction
│   │   └── indexer.py               # Document indexing
│   │
│   ├── llm/                         # LLM provider abstraction
│   │   ├── __init__.py
│   │   ├── provider.py              # Abstract LLM interface
│   │   ├── openai_provider.py       # OpenAI implementation
│   │   └── prompts/                 # Prompt templates
│   │       ├── __init__.py
│   │       ├── query_analysis.py
│   │       ├── clarification.py
│   │       ├── decomposition.py
│   │       ├── relevance.py
│   │       ├── rewrite.py
│   │       ├── response.py
│   │       ├── quality.py
│   │       └── web_integration.py
│   │
│   ├── config/                      # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py              # Pydantic settings
│   │   └── constants.py             # Application constants
│   │
│   ├── utils/                       # Utilities
│   │   ├── __init__.py
│   │   ├── logger.py                # Logging configuration
│   │   ├── metrics.py               # Performance metrics
│   │   └── cache.py                 # Caching utilities
│   │
│   └── ui/                          # Streamlit UI
│       ├── __init__.py
│       ├── app.py                   # Main Streamlit app
│       ├── components/              # UI components
│       │   ├── __init__.py
│       │   ├── chat.py
│       │   ├── sidebar.py
│       │   └── feedback.py
│       └── styles/
│           └── main.css
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_query_processor.py
│   │   ├── test_corrective_engine.py
│   │   ├── test_relevance_evaluator.py
│   │   └── test_response_generator.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_orchestrator.py
│   │   └── test_vectorstore.py
│   └── e2e/
│       ├── __init__.py
│       └── test_scenarios.py
│
├── scripts/                         # Utility scripts
│   ├── index_documents.py           # Document indexing
│   ├── evaluate_prompts.py          # Prompt evaluation
│   └── run_benchmarks.py            # Performance benchmarks
│
├── data/                            # Data directory
│   ├── documents/                   # Source documents
│   ├── chroma_db/                   # ChromaDB persistence
│   └── cache/                       # Response cache
│
├── docs/                            # Documentation
│   ├── api.md
│   ├── deployment.md
│   └── prompts.md
│
├── docker/                          # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
│
├── .env.example                     # Environment template
├── .gitignore
├── pyproject.toml                   # Project metadata (PEP 517)
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies
└── README.md
```

---

## 3. Component Module Structure

### 3.1 Core Components

#### RAG Orchestrator (`src/core/orchestrator.py`)

Central LangGraph workflow coordinator managing all agent interactions.

```python
# 모듈 책임: LangGraph 워크플로우 정의 및 실행
# 의존성: 모든 에이전트 컴포넌트

class RAGOrchestrator:
    """
    LangGraph 기반 RAG 워크플로우 오케스트레이터.
    상태 머신을 통해 쿼리 처리 → 검색 → 평가 → 응답 생성 플로우 관리.
    """

    def __init__(self, config: Settings):
        self.graph = self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        # LangGraph 노드 및 엣지 정의
        pass

    async def process_query(self, query: str, session_id: str) -> RAGResponse:
        # 쿼리 처리 진입점
        pass
```

#### State Management (`src/core/state.py`)

```python
# 상태 스키마 정의 - LangGraph StateGraph 용

from typing import TypedDict, Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel

class Document(BaseModel):
    """검색된 문서 모델"""
    content: str
    metadata: dict
    source: str
    relevance_score: Optional[float] = None

class RAGState(TypedDict):
    """LangGraph 상태 스키마"""

    # === Input ===
    query: str
    search_scope: str
    session_id: str

    # === Query Analysis ===
    refined_query: str
    complexity: Literal["simple", "complex"]
    clarity_confidence: float
    is_ambiguous: bool
    ambiguity_type: Optional[Literal[
        "multiple_interpretation",
        "missing_context",
        "vague_term"
    ]]
    detected_domains: List[str]

    # === HITL ===
    clarification_needed: bool
    clarification_question: Optional[str]
    clarification_options: Optional[List[str]]
    user_response: Optional[str]
    interaction_count: int

    # === Retrieval ===
    retrieved_docs: List[Document]
    relevance_scores: List[float]
    avg_relevance: float
    high_relevance_count: int
    retrieval_source: Literal["vector", "web", "hybrid"]

    # === Correction ===
    retry_count: int
    rewritten_queries: List[str]
    correction_triggered: bool

    # === Web Search ===
    web_search_triggered: bool
    web_results: List[Document]
    web_confidence: float

    # === Response ===
    generated_response: str
    response_confidence: float
    sources: List[str]
    needs_disclaimer: bool

    # === Metadata ===
    start_time: datetime
    end_time: Optional[datetime]
    total_llm_calls: int
    error_log: List[str]
    current_node: str
```

### 3.2 Agent Components

| Component | File | Responsibility | Complexity |
|-----------|------|----------------|------------|
| Query Processor | `agents/query_processor.py` | Analyze query clarity, complexity, ambiguity | Medium |
| HITL Controller | `agents/hitl_controller.py` | Generate clarification questions, manage user interaction | Medium |
| Agentic Controller | `agents/agentic_controller.py` | Decompose complex queries into sub-questions | Medium |
| Web Search Agent | `agents/web_search_agent.py` | Tavily API integration for web fallback | Low |

### 3.3 RAG Components

| Component | File | Responsibility | Complexity |
|-----------|------|----------------|------------|
| Corrective Engine | `rag/corrective_engine.py` | Orchestrate retrieval correction loop | High |
| Retriever | `rag/retriever.py` | Vector similarity search | Medium |
| Relevance Evaluator | `rag/relevance_evaluator.py` | Score document relevance (embedding + LLM) | Medium |
| Response Generator | `rag/response_generator.py` | Generate final answer with citations | Medium |

---

## 4. LangGraph State Machine Design

### 4.1 Node Definitions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LangGraph Workflow                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐                                                           │
│  │    START     │                                                           │
│  └──────┬───────┘                                                           │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐     ┌──────────────────────────────────────────┐         │
│  │analyze_query │────▶│ Outputs: complexity, clarity_confidence, │         │
│  │              │     │          is_ambiguous, refined_query     │         │
│  └──────┬───────┘     └──────────────────────────────────────────┘         │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐                                                           │
│  │ route_query  │◀─────────────────────────────────────────┐               │
│  └──────┬───────┘                                          │               │
│         │                                                   │               │
│    ┌────┴────┬──────────┐                                  │               │
│    ▼         ▼          ▼                                  │               │
│ ┌──────┐ ┌──────┐  ┌──────────┐                           │               │
│ │ HITL │ │decomp│  │ retrieve │                           │               │
│ │      │ │ose   │  │          │                           │               │
│ └──┬───┘ └──┬───┘  └────┬─────┘                           │               │
│    │        │           │                                  │               │
│    │        │           ▼                                  │               │
│    │        │    ┌──────────────┐                          │               │
│    │        │    │   evaluate   │                          │               │
│    │        │    │  relevance   │                          │               │
│    │        └───▶└──────┬───────┘                          │               │
│    │                    │                                   │               │
│    │              ┌─────┴─────┐                            │               │
│    │              ▼           ▼                            │               │
│    │         sufficient?   insufficient?                   │               │
│    │              │           │                            │               │
│    │              │           ▼                            │               │
│    │              │    ┌──────────────┐                    │               │
│    │              │    │   rewrite    │──retry < 2?────────┘               │
│    │              │    │    query     │                                     │
│    │              │    └──────┬───────┘                                     │
│    │              │           │                                             │
│    │              │           ▼ retry >= 2                                  │
│    │              │    ┌──────────────┐                                     │
│    │              │    │  web_search  │                                     │
│    │              │    └──────┬───────┘                                     │
│    │              │           │                                             │
│    │              └─────┬─────┘                                             │
│    │                    ▼                                                   │
│    │             ┌──────────────┐                                           │
│    └────────────▶│   generate   │                                           │
│                  │   response   │                                           │
│                  └──────┬───────┘                                           │
│                         │                                                   │
│                         ▼                                                   │
│                  ┌──────────────┐                                           │
│                  │   evaluate   │                                           │
│                  │   quality    │                                           │
│                  └──────┬───────┘                                           │
│                         │                                                   │
│                         ▼                                                   │
│                  ┌──────────────┐                                           │
│                  │     END      │                                           │
│                  └──────────────┘                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Node Specifications

```python
# LangGraph 노드 정의

NODES = {
    "analyze_query": {
        "function": "query_processor.analyze",
        "input": ["query"],
        "output": ["refined_query", "complexity", "clarity_confidence",
                   "is_ambiguous", "ambiguity_type", "detected_domains"],
        "llm_calls": 1
    },
    "clarify_hitl": {
        "function": "hitl_controller.generate_clarification",
        "input": ["query", "ambiguity_type"],
        "output": ["clarification_question", "clarification_options"],
        "llm_calls": 1,
        "interrupt": True  # Waits for user input
    },
    "decompose_query": {
        "function": "agentic_controller.decompose",
        "input": ["refined_query"],
        "output": ["sub_questions", "parallel_groups", "synthesis_guide"],
        "llm_calls": 1
    },
    "retrieve_documents": {
        "function": "retriever.search",
        "input": ["refined_query", "detected_domains"],
        "output": ["retrieved_docs"],
        "llm_calls": 0
    },
    "evaluate_relevance": {
        "function": "relevance_evaluator.evaluate",
        "input": ["query", "retrieved_docs"],
        "output": ["relevance_scores", "avg_relevance", "high_relevance_count"],
        "llm_calls": "N (per document)"
    },
    "rewrite_query": {
        "function": "corrective_engine.rewrite",
        "input": ["query", "rewritten_queries", "retry_count"],
        "output": ["refined_query", "rewritten_queries", "retry_count"],
        "llm_calls": 1
    },
    "web_search": {
        "function": "web_search_agent.search",
        "input": ["refined_query"],
        "output": ["web_results", "web_confidence", "web_search_triggered"],
        "llm_calls": 1
    },
    "generate_response": {
        "function": "response_generator.generate",
        "input": ["query", "retrieved_docs", "web_results"],
        "output": ["generated_response", "sources"],
        "llm_calls": 1
    },
    "evaluate_quality": {
        "function": "response_generator.evaluate_quality",
        "input": ["query", "generated_response", "sources"],
        "output": ["response_confidence", "needs_disclaimer"],
        "llm_calls": 1
    }
}
```

### 4.3 Edge Conditions (Routing Logic)

```python
# 조건부 라우팅 로직

def route_after_analysis(state: RAGState) -> str:
    """질문 분석 후 라우팅"""
    if state["is_ambiguous"] and state["interaction_count"] < 2:
        return "clarify_hitl"
    elif state["complexity"] == "complex":
        return "decompose_query"
    else:
        return "retrieve_documents"

def route_after_evaluation(state: RAGState) -> str:
    """관련성 평가 후 라우팅"""
    RELEVANCE_THRESHOLD = 0.8
    MIN_HIGH_RELEVANCE_DOCS = 2
    MAX_RETRIES = 2

    if (state["avg_relevance"] >= RELEVANCE_THRESHOLD and
        state["high_relevance_count"] >= MIN_HIGH_RELEVANCE_DOCS):
        return "generate_response"
    elif state["retry_count"] < MAX_RETRIES:
        return "rewrite_query"
    else:
        return "web_search"

def route_after_rewrite(state: RAGState) -> str:
    """쿼리 재작성 후 라우팅 (항상 재검색)"""
    return "retrieve_documents"

def route_after_web_search(state: RAGState) -> str:
    """웹 검색 후 라우팅 (항상 응답 생성)"""
    return "generate_response"
```

### 4.4 LangGraph Implementation

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

def build_rag_graph() -> CompiledStateGraph:
    """RAG 워크플로우 그래프 빌드"""

    graph = StateGraph(RAGState)

    # 노드 추가
    graph.add_node("analyze_query", analyze_query_node)
    graph.add_node("clarify_hitl", clarify_hitl_node)
    graph.add_node("decompose_query", decompose_query_node)
    graph.add_node("retrieve_documents", retrieve_documents_node)
    graph.add_node("evaluate_relevance", evaluate_relevance_node)
    graph.add_node("rewrite_query", rewrite_query_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("generate_response", generate_response_node)
    graph.add_node("evaluate_quality", evaluate_quality_node)

    # 시작점 설정
    graph.set_entry_point("analyze_query")

    # 조건부 엣지
    graph.add_conditional_edges(
        "analyze_query",
        route_after_analysis,
        {
            "clarify_hitl": "clarify_hitl",
            "decompose_query": "decompose_query",
            "retrieve_documents": "retrieve_documents"
        }
    )

    graph.add_edge("clarify_hitl", "analyze_query")  # HITL 후 재분석
    graph.add_edge("decompose_query", "retrieve_documents")
    graph.add_edge("retrieve_documents", "evaluate_relevance")

    graph.add_conditional_edges(
        "evaluate_relevance",
        route_after_evaluation,
        {
            "generate_response": "generate_response",
            "rewrite_query": "rewrite_query",
            "web_search": "web_search"
        }
    )

    graph.add_edge("rewrite_query", "retrieve_documents")
    graph.add_edge("web_search", "generate_response")
    graph.add_edge("generate_response", "evaluate_quality")
    graph.add_edge("evaluate_quality", END)

    # 체크포인터 설정 (HITL 중단점 지원)
    memory = MemorySaver()

    return graph.compile(
        checkpointer=memory,
        interrupt_before=["clarify_hitl"]  # HITL 전 중단
    )
```

---

## 5. Data Models (Pydantic Schemas)

### 5.1 Input/Output Models

```python
# src/core/models.py

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum

# === Enums ===

class Complexity(str, Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"

class AmbiguityType(str, Enum):
    MULTIPLE_INTERPRETATION = "multiple_interpretation"
    MISSING_CONTEXT = "missing_context"
    VAGUE_TERM = "vague_term"

class RelevanceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RewriteStrategy(str, Enum):
    SYNONYM_EXPANSION = "synonym_expansion"
    CONTEXT_ADDITION = "context_addition"
    GENERALIZATION = "generalization"
    SPECIFICATION = "specification"

class RetrievalSource(str, Enum):
    VECTOR = "vector"
    WEB = "web"
    HYBRID = "hybrid"

# === Document Models ===

class DocumentMetadata(BaseModel):
    """문서 메타데이터"""
    source: str
    title: Optional[str] = None
    section: Optional[str] = None
    page: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Document(BaseModel):
    """검색 문서 모델"""
    content: str
    metadata: DocumentMetadata
    embedding_score: Optional[float] = None
    llm_relevance_score: Optional[float] = None
    combined_score: Optional[float] = None

# === Query Analysis Models ===

class QueryAnalysisInput(BaseModel):
    """질문 분석 입력"""
    query: str
    search_scope: str = "all"

class QueryAnalysisOutput(BaseModel):
    """질문 분석 출력 (프롬프트 #1)"""
    refined_query: str
    complexity: Complexity
    clarity_confidence: float = Field(ge=0.0, le=1.0)
    is_ambiguous: bool
    ambiguity_type: Optional[AmbiguityType] = None
    detected_domains: List[str] = []

# === HITL Models ===

class ClarificationOutput(BaseModel):
    """명확화 질문 생성 출력 (프롬프트 #2)"""
    clarification_question: str
    options: List[str] = Field(min_length=2, max_length=5)

class HITLResponse(BaseModel):
    """사용자 HITL 응답"""
    selected_option: Optional[str] = None
    custom_input: Optional[str] = None

# === Query Decomposition Models ===

class DecompositionOutput(BaseModel):
    """질문 분해 출력 (프롬프트 #3)"""
    original_intent: str
    sub_questions: List[str] = Field(max_length=5)
    parallel_groups: List[List[int]]
    synthesis_guide: str

# === Relevance Evaluation Models ===

class RelevanceEvaluationOutput(BaseModel):
    """관련성 평가 출력 (프롬프트 #4)"""
    relevance_score: float = Field(ge=0.0, le=1.0)
    relevance_level: RelevanceLevel
    reason: str
    useful_parts: List[str] = []

# === Query Rewrite Models ===

class QueryRewriteOutput(BaseModel):
    """쿼리 재작성 출력 (프롬프트 #5)"""
    strategy: RewriteStrategy
    rewritten_query: str
    changes_made: str
    expected_improvement: str

# === Response Generation Models ===

class ResponseOutput(BaseModel):
    """답변 생성 출력 (프롬프트 #6)"""
    response: str
    sources: List[str]
    has_sufficient_info: bool

class QualityEvaluationOutput(BaseModel):
    """품질 평가 출력 (프롬프트 #7)"""
    completeness: float = Field(ge=0.0, le=1.0)
    accuracy: float = Field(ge=0.0, le=1.0)
    clarity: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_disclaimer: bool

# === Web Search Models ===

class WebSearchResult(BaseModel):
    """웹 검색 결과 항목"""
    title: str
    url: str
    summary: str
    relevance: float = Field(ge=0.0, le=1.0)
    published_date: Optional[datetime] = None

class WebIntegrationOutput(BaseModel):
    """웹 검색 통합 출력 (프롬프트 #8)"""
    relevant_results: List[WebSearchResult]
    overall_confidence: float = Field(ge=0.0, le=1.0)
    integration_notes: str
    disclaimer_needed: bool

# === API Response Models ===

class RAGRequest(BaseModel):
    """RAG API 요청"""
    query: str
    session_id: Optional[str] = None
    search_scope: str = "all"

class RAGResponse(BaseModel):
    """RAG API 응답"""
    response: str
    sources: List[str]
    confidence: float
    needs_disclaimer: bool
    retrieval_source: RetrievalSource
    processing_time_ms: int
    session_id: str

    # Optional debugging info
    debug: Optional[dict] = None
```

---

## 6. Dependency Management

### 6.1 requirements.txt (Production)

```txt
# Core Framework
langgraph>=0.2.0
langchain>=0.2.0
langchain-openai>=0.1.0
langchain-community>=0.2.0

# Vector Store
chromadb>=0.4.0

# LLM Providers
openai>=1.0.0

# Web Search
tavily-python>=0.3.0

# UI Framework
streamlit>=1.28.0

# Data Validation
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Async Support
aiohttp>=3.9.0
asyncio>=3.4.3

# Environment & Configuration
python-dotenv>=1.0.0

# Utilities
tenacity>=8.2.0  # Retry logic
structlog>=23.0.0  # Structured logging
cachetools>=5.3.0  # Caching

# HTTP Client
httpx>=0.25.0
```

### 6.2 requirements-dev.txt (Development)

```txt
-r requirements.txt

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0

# Code Quality
ruff>=0.1.0
mypy>=1.7.0
black>=23.0.0
isort>=5.12.0

# Documentation
mkdocs>=1.5.0
mkdocs-material>=9.0.0

# Development Tools
ipython>=8.0.0
jupyter>=1.0.0

# Debugging & Profiling
langsmith>=0.0.60  # LangChain tracing
py-spy>=0.3.0
```

### 6.3 Dependency Analysis

| Package | Bundle Impact | Alternatives Considered | Selection Rationale |
|---------|---------------|------------------------|---------------------|
| LangGraph | ~50KB | Custom state machine | Native LangChain integration, HITL support |
| ChromaDB | ~15MB | Pinecone, Weaviate | Local-first, no infrastructure needed for MVP |
| Streamlit | ~80MB | Gradio, FastAPI+React | Rapid prototyping, built-in components |
| OpenAI | ~5MB | Anthropic, local LLMs | GPT-4o quality, structured output support |
| Pydantic v2 | ~5MB | dataclasses, attrs | Validation, serialization, settings management |

**Total Estimated Package Size:** ~160MB (excluding transitive dependencies)

---

## 7. Environment Configuration

### 7.1 Configuration Schema (`src/config/settings.py`)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # === Application ===
    app_name: str = "RAG Chatbot"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # === OpenAI ===
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_temperature: float = 0.1
    openai_max_tokens: int = 2000

    # === Tavily ===
    tavily_api_key: str
    tavily_max_results: int = 5

    # === ChromaDB ===
    chroma_persist_directory: str = "./data/chroma_db"
    chroma_collection_name: str = "documents"

    # === RAG Settings ===
    relevance_threshold: float = 0.8
    min_high_relevance_docs: int = 2
    max_retrieval_results: int = 10
    max_correction_retries: int = 2
    max_hitl_interactions: int = 2

    # === Performance ===
    cache_ttl_seconds: int = 3600
    request_timeout_seconds: int = 30
    max_concurrent_requests: int = 10

    # === Streamlit ===
    streamlit_port: int = 8501
    streamlit_host: str = "0.0.0.0"

# Singleton instance
settings = Settings()
```

### 7.2 Environment Template (`.env.example`)

```env
# === Required API Keys ===
OPENAI_API_KEY=sk-your-openai-api-key
TAVILY_API_KEY=tvly-your-tavily-api-key

# === Application Settings ===
DEBUG=false
LOG_LEVEL=INFO

# === Model Configuration ===
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=2000

# === RAG Configuration ===
RELEVANCE_THRESHOLD=0.8
MIN_HIGH_RELEVANCE_DOCS=2
MAX_RETRIEVAL_RESULTS=10
MAX_CORRECTION_RETRIES=2
MAX_HITL_INTERACTIONS=2

# === ChromaDB ===
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
CHROMA_COLLECTION_NAME=documents

# === Performance ===
CACHE_TTL_SECONDS=3600
REQUEST_TIMEOUT_SECONDS=30

# === Streamlit ===
STREAMLIT_PORT=8501
```

### 7.3 Constants (`src/config/constants.py`)

```python
"""애플리케이션 상수 정의"""

# === Domain Categories ===
VALID_DOMAINS = [
    "development",
    "operations",
    "security",
    "infrastructure",
    "api",
    "database",
    "frontend",
    "backend",
    "devops",
    "general"
]

# === Relevance Score Mapping ===
RELEVANCE_LEVELS = {
    "high": (0.8, 1.0),
    "medium": (0.5, 0.8),
    "low": (0.0, 0.5)
}

# === Token Limits ===
MAX_CONTEXT_TOKENS = 8000
MAX_RESPONSE_TOKENS = 2000
MAX_DOCUMENT_CHUNK_SIZE = 1000

# === UI Messages ===
DISCLAIMER_MESSAGE = (
    "⚠️ 이 답변은 검색된 정보가 충분하지 않아 "
    "정확성이 보장되지 않습니다. 중요한 결정에는 "
    "추가 확인을 권장합니다."
)

WEB_SEARCH_DISCLAIMER = (
    "ℹ️ 내부 문서에서 관련 정보를 찾지 못하여 "
    "웹 검색 결과를 포함합니다."
)

# === Error Messages ===
ERROR_MESSAGES = {
    "no_results": "관련 문서를 찾을 수 없습니다.",
    "api_error": "API 호출 중 오류가 발생했습니다.",
    "timeout": "요청 시간이 초과되었습니다.",
    "rate_limit": "API 호출 한도에 도달했습니다. 잠시 후 다시 시도해주세요.",
    "invalid_query": "질문을 이해할 수 없습니다. 다시 입력해주세요."
}
```

---

## 8. Error Handling Strategy

### 8.1 Exception Hierarchy

```python
# src/core/exceptions.py

class RAGException(Exception):
    """RAG 시스템 기본 예외"""
    def __init__(self, message: str, recoverable: bool = True):
        self.message = message
        self.recoverable = recoverable
        super().__init__(message)

class LLMException(RAGException):
    """LLM 관련 예외"""
    pass

class APIRateLimitException(LLMException):
    """API Rate Limit 초과"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after}s",
            recoverable=True
        )
        self.retry_after = retry_after

class APITimeoutException(LLMException):
    """API 타임아웃"""
    pass

class ParsingException(RAGException):
    """LLM 출력 파싱 실패"""
    pass

class RetrievalException(RAGException):
    """검색 관련 예외"""
    pass

class NoResultsException(RetrievalException):
    """검색 결과 없음"""
    def __init__(self):
        super().__init__("No relevant documents found", recoverable=True)

class VectorStoreException(RAGException):
    """벡터 스토어 예외"""
    pass

class ConfigurationException(RAGException):
    """설정 오류"""
    def __init__(self, message: str):
        super().__init__(message, recoverable=False)
```

### 8.2 Error Handler

```python
# src/utils/error_handler.py

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import structlog

logger = structlog.get_logger()

def with_retry(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10
):
    """재시도 데코레이터"""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((APITimeoutException, APIRateLimitException)),
        before_sleep=lambda retry_state: logger.warning(
            "retrying",
            attempt=retry_state.attempt_number,
            exception=str(retry_state.outcome.exception())
        )
    )

class ErrorHandler:
    """중앙 에러 핸들러"""

    @staticmethod
    def handle_llm_error(e: Exception, context: dict) -> dict:
        """LLM 에러 처리"""
        logger.error("llm_error", error=str(e), **context)

        if isinstance(e, APIRateLimitException):
            return {
                "error_type": "rate_limit",
                "message": ERROR_MESSAGES["rate_limit"],
                "recoverable": True,
                "fallback_action": "retry"
            }
        elif isinstance(e, ParsingException):
            return {
                "error_type": "parsing_error",
                "message": "응답 처리 중 오류가 발생했습니다.",
                "recoverable": True,
                "fallback_action": "retry"
            }
        else:
            return {
                "error_type": "api_error",
                "message": ERROR_MESSAGES["api_error"],
                "recoverable": False,
                "fallback_action": "return_partial"
            }

    @staticmethod
    def handle_retrieval_error(e: Exception, state: RAGState) -> str:
        """검색 에러 처리 - 다음 노드 반환"""
        logger.error("retrieval_error", error=str(e), query=state["query"])

        if isinstance(e, NoResultsException):
            if state["retry_count"] < 2:
                return "rewrite_query"
            else:
                return "web_search"
        else:
            return "web_search"
```

### 8.3 Graceful Degradation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Error Handling Flow                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LLM API Error                                                  │
│       │                                                          │
│       ├── Rate Limit → Wait & Retry (exponential backoff)       │
│       ├── Timeout → Retry (max 3 attempts)                      │
│       ├── Parsing Error → Retry with simplified prompt          │
│       └── Other → Return partial response with disclaimer       │
│                                                                  │
│  Retrieval Error                                                │
│       │                                                          │
│       ├── No Results → Query Rewrite → Web Search               │
│       ├── Vector DB Error → Web Search fallback                 │
│       └── All Failed → "Unable to answer" response              │
│                                                                  │
│  Web Search Error                                               │
│       │                                                          │
│       └── Any Error → Return "No information found" with        │
│                       suggestion to rephrase query              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Logging and Monitoring Design

### 9.1 Logging Configuration

```python
# src/utils/logger.py

import structlog
from datetime import datetime
import sys

def configure_logging(log_level: str = "INFO"):
    """구조화된 로깅 설정"""

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(structlog, log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str):
    """명명된 로거 반환"""
    return structlog.get_logger(name)
```

### 9.2 Metrics Collection

```python
# src/utils/metrics.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
import statistics

@dataclass
class QueryMetrics:
    """쿼리별 메트릭"""
    session_id: str
    query: str
    start_time: datetime
    end_time: datetime = None

    # Processing metrics
    total_llm_calls: int = 0
    total_tokens_used: int = 0
    retrieval_count: int = 0
    correction_count: int = 0
    hitl_count: int = 0
    web_search_used: bool = False

    # Quality metrics
    avg_relevance_score: float = 0.0
    response_confidence: float = 0.0

    # Timing breakdown (ms)
    query_analysis_time: int = 0
    retrieval_time: int = 0
    relevance_eval_time: int = 0
    response_gen_time: int = 0

    @property
    def total_time_ms(self) -> int:
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0

class MetricsCollector:
    """메트릭 수집기"""

    def __init__(self):
        self.queries: List[QueryMetrics] = []

    def record(self, metrics: QueryMetrics):
        """메트릭 기록"""
        self.queries.append(metrics)

    def get_summary(self, last_n: int = 100) -> Dict:
        """요약 통계 반환"""
        recent = self.queries[-last_n:]
        if not recent:
            return {}

        return {
            "total_queries": len(recent),
            "avg_response_time_ms": statistics.mean(q.total_time_ms for q in recent),
            "avg_llm_calls": statistics.mean(q.total_llm_calls for q in recent),
            "correction_rate": sum(1 for q in recent if q.correction_count > 0) / len(recent),
            "web_fallback_rate": sum(1 for q in recent if q.web_search_used) / len(recent),
            "avg_confidence": statistics.mean(q.response_confidence for q in recent)
        }
```

### 9.3 LangSmith Integration (Optional)

```python
# src/utils/tracing.py

import os
from langsmith import Client

def setup_langsmith():
    """LangSmith 트레이싱 설정"""
    if os.getenv("LANGCHAIN_TRACING_V2") == "true":
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        os.environ["LANGCHAIN_PROJECT"] = "rag-chatbot"
        return Client()
    return None
```

### 9.4 Monitoring Dashboard (Streamlit)

```python
# src/ui/components/monitoring.py

import streamlit as st

def render_metrics_dashboard(metrics: MetricsCollector):
    """메트릭 대시보드 렌더링"""

    summary = metrics.get_summary()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Queries", summary.get("total_queries", 0))

    with col2:
        st.metric(
            "Avg Response Time",
            f"{summary.get('avg_response_time_ms', 0):.0f}ms"
        )

    with col3:
        st.metric(
            "Correction Rate",
            f"{summary.get('correction_rate', 0)*100:.1f}%"
        )

    with col4:
        st.metric(
            "Avg Confidence",
            f"{summary.get('avg_confidence', 0)*100:.1f}%"
        )
```

---

## 10. Test Strategy

### 10.1 Test Pyramid

```
              ┌─────────────┐
             /   E2E Tests   \        10% - Full workflow scenarios
            /   (Slow, Few)   \
           ├───────────────────┤
          /  Integration Tests  \     30% - Component interactions
         /   (Medium, Some)      \
        ├─────────────────────────┤
       /       Unit Tests          \   60% - Individual functions
      /      (Fast, Many)           \
     └───────────────────────────────┘
```

### 10.2 Test Categories

| Category | Focus | Tools | Coverage Target |
|----------|-------|-------|-----------------|
| Unit | Individual functions, classes | pytest, pytest-mock | 80% |
| Integration | Component interactions, LangGraph nodes | pytest-asyncio | 70% |
| E2E | Full workflow scenarios | pytest, Streamlit testing | 5 core scenarios |
| Performance | Response time, throughput | pytest-benchmark | < 15s avg response |

### 10.3 Test Fixtures

```python
# tests/conftest.py

import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_openai_client():
    """OpenAI 클라이언트 모킹"""
    client = MagicMock()
    client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"test": "response"}'))]
        )
    )
    return client

@pytest.fixture
def mock_chroma_client():
    """ChromaDB 클라이언트 모킹"""
    client = MagicMock()
    collection = MagicMock()
    collection.query.return_value = {
        "documents": [["Test document content"]],
        "metadatas": [[{"source": "test.md"}]],
        "distances": [[0.1]]
    }
    client.get_or_create_collection.return_value = collection
    return client

@pytest.fixture
def sample_rag_state():
    """샘플 RAG 상태"""
    return {
        "query": "How do I deploy the application?",
        "search_scope": "all",
        "session_id": "test-session-001",
        "refined_query": "",
        "complexity": "simple",
        "clarity_confidence": 0.9,
        "is_ambiguous": False,
        "ambiguity_type": None,
        "detected_domains": ["devops"],
        "clarification_needed": False,
        "clarification_question": None,
        "clarification_options": None,
        "user_response": None,
        "interaction_count": 0,
        "retrieved_docs": [],
        "relevance_scores": [],
        "avg_relevance": 0.0,
        "high_relevance_count": 0,
        "retrieval_source": "vector",
        "retry_count": 0,
        "rewritten_queries": [],
        "correction_triggered": False,
        "web_search_triggered": False,
        "web_results": [],
        "web_confidence": 0.0,
        "generated_response": "",
        "response_confidence": 0.0,
        "sources": [],
        "needs_disclaimer": False,
        "start_time": None,
        "end_time": None,
        "total_llm_calls": 0,
        "error_log": [],
        "current_node": "start"
    }
```

### 10.4 Unit Test Example

```python
# tests/unit/test_query_processor.py

import pytest
from src.agents.query_processor import QueryProcessor
from src.core.models import QueryAnalysisOutput

class TestQueryProcessor:

    @pytest.mark.asyncio
    async def test_analyze_simple_query(self, mock_openai_client):
        """단순 질문 분석 테스트"""
        processor = QueryProcessor(mock_openai_client)

        result = await processor.analyze("배포 방법은?")

        assert isinstance(result, QueryAnalysisOutput)
        assert result.complexity == "simple"
        assert result.clarity_confidence > 0.7

    @pytest.mark.asyncio
    async def test_detect_ambiguous_query(self, mock_openai_client):
        """모호한 질문 감지 테스트"""
        processor = QueryProcessor(mock_openai_client)

        result = await processor.analyze("그거 어떻게 해요?")

        assert result.is_ambiguous == True
        assert result.ambiguity_type in ["missing_context", "vague_term"]
```

### 10.5 Integration Test Example

```python
# tests/integration/test_orchestrator.py

import pytest
from src.core.orchestrator import RAGOrchestrator

class TestRAGOrchestrator:

    @pytest.mark.asyncio
    async def test_happy_path_flow(self, mock_openai_client, mock_chroma_client):
        """Happy Path 전체 플로우 테스트"""
        orchestrator = RAGOrchestrator(
            llm_client=mock_openai_client,
            vector_store=mock_chroma_client
        )

        result = await orchestrator.process_query(
            query="How do I configure the database?",
            session_id="test-001"
        )

        assert result.response is not None
        assert len(result.sources) > 0
        assert result.confidence > 0.5

    @pytest.mark.asyncio
    async def test_corrective_flow(self, mock_openai_client, mock_chroma_client):
        """Corrective RAG 플로우 테스트"""
        # 첫 검색에서 낮은 관련성 반환하도록 설정
        mock_chroma_client.get_or_create_collection().query.return_value = {
            "documents": [["Irrelevant content"]],
            "metadatas": [[{"source": "irrelevant.md"}]],
            "distances": [[0.9]]  # 낮은 유사도
        }

        orchestrator = RAGOrchestrator(
            llm_client=mock_openai_client,
            vector_store=mock_chroma_client
        )

        result = await orchestrator.process_query(
            query="Specific technical question",
            session_id="test-002"
        )

        # 쿼리 재작성이 발생했는지 확인
        assert result.debug.get("correction_triggered", False) == True
```

### 10.6 E2E Scenario Tests

```python
# tests/e2e/test_scenarios.py

import pytest

SCENARIOS = [
    {
        "name": "Happy Path",
        "query": "프로젝트 빌드 방법은?",
        "expected_flow": ["analyze", "retrieve", "evaluate", "generate"],
        "expected_source_type": "vector"
    },
    {
        "name": "HITL Flow",
        "query": "그거 어떻게 설정해요?",
        "expected_flow": ["analyze", "hitl", "analyze", "retrieve"],
        "expected_hitl_trigger": True
    },
    {
        "name": "Corrective Flow",
        "query": "2023년 12월 보안 패치 내용",
        "expected_flow": ["analyze", "retrieve", "rewrite", "retrieve"],
        "expected_correction": True
    },
    {
        "name": "Web Fallback",
        "query": "최신 React 19 변경사항",
        "expected_flow": ["analyze", "retrieve", "rewrite", "rewrite", "web_search"],
        "expected_source_type": "web"
    },
    {
        "name": "Complex Query",
        "query": "마이크로서비스 아키텍처의 장단점과 모놀리식과의 차이점",
        "expected_flow": ["analyze", "decompose", "retrieve"],
        "expected_complexity": "complex"
    }
]

@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["name"] for s in SCENARIOS])
@pytest.mark.asyncio
async def test_scenario(scenario, orchestrator):
    """시나리오별 E2E 테스트"""
    result = await orchestrator.process_query(
        query=scenario["query"],
        session_id=f"e2e-{scenario['name']}"
    )

    assert result.response is not None
    # 추가 검증 로직...
```

---

## 11. Deployment Considerations

### 11.1 Dockerfile

```dockerfile
# docker/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY src/ ./src/
COPY scripts/ ./scripts/

# 데이터 디렉토리 생성
RUN mkdir -p /app/data/chroma_db /app/data/documents /app/data/cache

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 포트 노출
EXPOSE 8501

# Streamlit 실행
CMD ["streamlit", "run", "src/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 11.2 Docker Compose

```yaml
# docker/docker-compose.yml

version: '3.8'

services:
  rag-chatbot:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: rag-chatbot
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - LOG_LEVEL=INFO
      - CHROMA_PERSIST_DIRECTORY=/app/data/chroma_db
    volumes:
      - ./data/chroma_db:/app/data/chroma_db
      - ./data/documents:/app/data/documents
      - ./data/cache:/app/data/cache
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Vector DB 외부화 시
  # chroma:
  #   image: chromadb/chroma:latest
  #   ports:
  #     - "8000:8000"
  #   volumes:
  #     - ./data/chroma_db:/chroma/chroma

volumes:
  chroma_data:
  document_data:
  cache_data:
```

### 11.3 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Production Deployment                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌──────────────────────────────────────────┐   │
│  │   Users     │───▶│           Load Balancer                   │   │
│  │  (Browser)  │    │         (Optional for HA)                 │   │
│  └─────────────┘    └──────────────────┬───────────────────────┘   │
│                                         │                           │
│                     ┌───────────────────┼───────────────────┐      │
│                     ▼                   ▼                   ▼      │
│              ┌────────────┐      ┌────────────┐      ┌────────────┐│
│              │ Container  │      │ Container  │      │ Container  ││
│              │  Instance  │      │  Instance  │      │  Instance  ││
│              │    (1)     │      │    (2)     │      │    (N)     ││
│              └─────┬──────┘      └─────┬──────┘      └─────┬──────┘│
│                    │                   │                   │       │
│                    └───────────────────┼───────────────────┘       │
│                                        │                            │
│                              ┌─────────┴─────────┐                 │
│                              ▼                   ▼                 │
│                       ┌────────────┐      ┌────────────┐          │
│                       │ ChromaDB   │      │  Shared    │          │
│                       │ (Embedded  │      │  Volume    │          │
│                       │  or Server)│      │ (Documents)│          │
│                       └────────────┘      └────────────┘          │
│                                                                     │
│  External Services:                                                │
│  ┌────────────┐  ┌────────────┐                                   │
│  │  OpenAI    │  │   Tavily   │                                   │
│  │    API     │  │    API     │                                   │
│  └────────────┘  └────────────┘                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.4 Environment-Specific Configuration

| Environment | ChromaDB Mode | Scaling | Monitoring |
|-------------|---------------|---------|------------|
| Development | Embedded (local) | Single instance | Console logs |
| Staging | Embedded (Docker volume) | Single instance | LangSmith |
| Production | Server mode (optional) | Multiple instances | LangSmith + Custom metrics |

---

## 12. Risk Analysis

### 12.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM latency degrading UX | High | Medium | Streaming responses, loading indicators |
| Relevance evaluation inaccuracy | Medium | High | Threshold tuning, golden dataset validation |
| Query rewrite infinite loop | Low | High | max_retries=2 (already addressed) |
| ChromaDB scaling limits | Low | Medium | Monitor document count, plan migration path |
| API rate limiting | Medium | Medium | Exponential backoff, request queuing |
| Token limit exceeded | Medium | Medium | Document chunking, summarization |

### 12.2 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Document staleness | High | Medium | Periodic re-indexing pipeline |
| User expectation mismatch | Medium | Medium | Clear feature scope, feedback loop |
| Sensitive info exposure | Low | High | Access control, document classification |
| Cost overruns | Medium | Medium | Usage monitoring, model tiering |

### 12.3 Risk Mitigation Priorities

1. **P0 (Critical):** Implement rate limiting and retry logic before deployment
2. **P1 (High):** Set up monitoring and alerting for response quality
3. **P2 (Medium):** Establish document update workflow
4. **P3 (Low):** Plan for ChromaDB migration if needed

---

## 13. Browser Support

| Browser | Minimum Version | Notes |
|---------|-----------------|-------|
| Chrome | 90+ | Full support |
| Firefox | 88+ | Full support |
| Safari | 14+ | Full support |
| Edge | 90+ | Full support |
| Mobile Chrome | 90+ | Responsive UI |
| Mobile Safari | 14+ | Responsive UI |

**Note:** Streamlit handles browser compatibility; focus is on modern evergreen browsers.

---

## 14. Implementation Roadmap

### Phase 1: Foundation (MVP)
1. Config Manager + Settings
2. LLM Provider (OpenAI abstraction)
3. Vector Store Manager (ChromaDB)
4. Basic Query Processor
5. Simple Retriever
6. Response Generator
7. Basic Streamlit UI

### Phase 2: Core RAG
1. Relevance Evaluator
2. Corrective RAG Engine
3. Query Rewrite logic
4. LangGraph Orchestrator

### Phase 3: Enhanced Features
1. HITL Controller
2. Web Search Agent
3. Quality Evaluator
4. Agentic Controller (complex queries)

### Phase 4: Production Readiness
1. Comprehensive error handling
2. Logging and monitoring
3. Performance optimization
4. Docker deployment
5. Integration tests

---

## 15. Appendix

### A. Prompt Template Locations

| Prompt | File | Purpose |
|--------|------|---------|
| #1 Query Analysis | `src/llm/prompts/query_analysis.py` | Analyze query clarity/complexity |
| #2 Clarification | `src/llm/prompts/clarification.py` | Generate HITL questions |
| #3 Decomposition | `src/llm/prompts/decomposition.py` | Break complex queries |
| #4 Relevance | `src/llm/prompts/relevance.py` | Evaluate document relevance |
| #5 Rewrite | `src/llm/prompts/rewrite.py` | Rewrite failed queries |
| #6 Response | `src/llm/prompts/response.py` | Generate final answer |
| #7 Quality | `src/llm/prompts/quality.py` | Evaluate response quality |
| #8 Web Integration | `src/llm/prompts/web_integration.py` | Process web results |

### B. Key Decision Thresholds

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `RELEVANCE_THRESHOLD` | 0.8 | Balance precision vs recall |
| `MIN_HIGH_RELEVANCE_DOCS` | 2 | Ensure sufficient context |
| `MAX_CORRECTION_RETRIES` | 2 | Prevent infinite loops |
| `MAX_HITL_INTERACTIONS` | 2 | Minimize user friction |
| `CLARITY_THRESHOLD` | 0.7 | Trigger HITL when below |
| `DISCLAIMER_THRESHOLD` | 0.6 | Show warning when confidence below |

---

**Document End**

*This architecture proposal is based on the feasibility report and prompt review report provided. Implementation details may be adjusted during development based on practical constraints and testing results.*
