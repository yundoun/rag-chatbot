"""Pydantic models for RAG Chatbot"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# === Enums ===


class Complexity(str, Enum):
    """Query complexity level"""

    SIMPLE = "simple"
    COMPLEX = "complex"


class AmbiguityType(str, Enum):
    """Types of query ambiguity"""

    MULTIPLE_INTERPRETATION = "multiple_interpretation"
    MISSING_CONTEXT = "missing_context"
    VAGUE_TERM = "vague_term"


class RelevanceLevel(str, Enum):
    """Document relevance level"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RewriteStrategy(str, Enum):
    """Query rewrite strategies"""

    SYNONYM_EXPANSION = "synonym_expansion"
    CONTEXT_ADDITION = "context_addition"
    GENERALIZATION = "generalization"
    SPECIFICATION = "specification"


class RetrievalSource(str, Enum):
    """Source of retrieved documents"""

    VECTOR = "vector"
    WEB = "web"
    HYBRID = "hybrid"


# === Document Models ===


class DocumentMetadata(BaseModel):
    """Document metadata"""

    source: str
    title: Optional[str] = None
    section: Optional[str] = None
    page: Optional[int] = None
    chunk_index: Optional[int] = None
    total_chunks: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Document(BaseModel):
    """Retrieved document model"""

    content: str
    metadata: DocumentMetadata
    embedding_score: Optional[float] = None
    llm_relevance_score: Optional[float] = None
    combined_score: Optional[float] = None


# === Query Analysis Models ===


class QueryAnalysisInput(BaseModel):
    """Query analysis input"""

    query: str
    search_scope: str = "all"


class QueryAnalysisOutput(BaseModel):
    """Query analysis output (Prompt #1)"""

    refined_query: str
    complexity: Complexity
    clarity_confidence: float = Field(ge=0.0, le=1.0)
    is_ambiguous: bool
    ambiguity_type: Optional[AmbiguityType] = None
    detected_domains: List[str] = []


# === HITL Models ===


class ClarificationOutput(BaseModel):
    """Clarification question generation output (Prompt #2)"""

    clarification_question: str
    options: List[str] = Field(min_length=2, max_length=5)


class HITLResponse(BaseModel):
    """User HITL response"""

    selected_option: Optional[str] = None
    custom_input: Optional[str] = None


# === Relevance Evaluation Models ===


class RelevanceEvaluationOutput(BaseModel):
    """Relevance evaluation output (Prompt #4)"""

    relevance_score: float = Field(ge=0.0, le=1.0)
    relevance_level: RelevanceLevel
    reason: str
    useful_parts: List[str] = []


# === Response Generation Models ===


class ResponseOutput(BaseModel):
    """Response generation output (Prompt #6)"""

    response: str
    sources: List[str]
    has_sufficient_info: bool


# === API Models ===


class RAGRequest(BaseModel):
    """RAG API request"""

    query: str
    session_id: Optional[str] = None
    search_scope: str = "all"


class RAGResponse(BaseModel):
    """RAG API response"""

    response: str
    sources: List[str]
    confidence: float
    needs_disclaimer: bool
    retrieval_source: RetrievalSource
    processing_time_ms: int
    session_id: str

    # Optional debugging info
    debug: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
