"""RAG State definitions for LangGraph"""

from datetime import datetime
from typing import List, Literal, Optional, TypedDict

from .models import Document


class RAGState(TypedDict, total=False):
    """LangGraph state schema for RAG workflow"""

    # === Input ===
    query: str
    search_scope: str
    session_id: str

    # === Query Analysis ===
    refined_query: str
    complexity: Literal["simple", "complex"]
    clarity_confidence: float
    is_ambiguous: bool
    ambiguity_type: Optional[
        Literal["multiple_interpretation", "missing_context", "vague_term"]
    ]
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

    # === Query Decomposition ===
    sub_questions: Optional[List[dict]]
    parallel_groups: Optional[List[List[str]]]
    synthesis_guide: Optional[str]

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


def create_initial_state(query: str, session_id: str) -> RAGState:
    """Create initial RAG state"""
    return RAGState(
        query=query,
        search_scope="all",
        session_id=session_id,
        refined_query="",
        complexity="simple",
        clarity_confidence=0.0,
        is_ambiguous=False,
        ambiguity_type=None,
        detected_domains=[],
        clarification_needed=False,
        clarification_question=None,
        clarification_options=None,
        user_response=None,
        interaction_count=0,
        retrieved_docs=[],
        relevance_scores=[],
        avg_relevance=0.0,
        high_relevance_count=0,
        retrieval_source="vector",
        retry_count=0,
        rewritten_queries=[],
        correction_triggered=False,
        sub_questions=None,
        parallel_groups=None,
        synthesis_guide=None,
        web_search_triggered=False,
        web_results=[],
        web_confidence=0.0,
        generated_response="",
        response_confidence=0.0,
        sources=[],
        needs_disclaimer=False,
        start_time=datetime.now(),
        end_time=None,
        total_llm_calls=0,
        error_log=[],
        current_node="start",
    )
