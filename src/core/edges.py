"""LangGraph Edge (routing) logic for RAG workflow"""

from typing import Literal

from src.config import get_settings
from src.core.state import RAGState


def route_after_analysis(
    state: RAGState,
) -> Literal["retrieve", "clarify", "decompose"]:
    """Route after query analysis

    Decision tree:
    1. If clarification needed -> clarify (HITL)
    2. If complex query -> decompose
    3. Otherwise -> retrieve
    """
    settings = get_settings()

    clarification_needed = state.get("clarification_needed", False)
    complexity = state.get("complexity", "simple")
    interaction_count = state.get("interaction_count", 0)
    max_interactions = settings.max_hitl_interactions

    # Check if HITL clarification is needed
    if clarification_needed and interaction_count < max_interactions:
        return "clarify"

    # Check if complex query needs decomposition
    if complexity == "complex":
        return "decompose"

    return "retrieve"


def route_after_clarify(state: RAGState) -> Literal["wait_for_response"]:
    """Route after generating clarification question

    This always goes to wait_for_response which is an interrupt point.
    The workflow will be resumed when user provides response.
    """
    return "wait_for_response"


def route_after_hitl_response(
    state: RAGState,
) -> Literal["retrieve", "decompose"]:
    """Route after processing HITL response"""
    complexity = state.get("complexity", "simple")

    if complexity == "complex":
        return "decompose"

    return "retrieve"


def route_after_decompose(state: RAGState) -> Literal["retrieve"]:
    """Route after query decomposition"""
    return "retrieve"


def route_after_evaluation(
    state: RAGState,
) -> Literal["generate", "rewrite", "web_search"]:
    """Route after relevance evaluation - core corrective logic

    Relaxed conditions for small document collections:
    - If any high relevance docs found, proceed to generate
    - If avg relevance >= threshold, proceed to generate
    - If medium relevance docs exist and some relevance found, proceed to generate
    """
    retrieved_docs = state.get("retrieved_docs", [])

    # 검색 결과가 있으면 바로 응답 생성 (relevance evaluation 건너뛰기)
    if len(retrieved_docs) > 0:
        return "generate"

    # 검색 결과 없으면 web search fallback
    return "web_search"

    # # 아래는 기존 relevance evaluation 로직 (비활성화)
    # settings = get_settings()
    #
    # avg_relevance = state.get("avg_relevance", 0.0)
    # high_count = state.get("high_relevance_count", 0)
    # medium_count = state.get("medium_relevance_count", 0)
    # retry_count = state.get("retry_count", 0)
    #
    # relevance_threshold = settings.relevance_threshold
    # min_high_docs = settings.min_high_relevance_docs
    # max_retries = settings.max_correction_retries
    #
    # # Condition 1: At least min_high_docs high relevance documents
    # if high_count >= min_high_docs:
    #     return "generate"
    #
    # # Condition 2: Average relevance meets threshold
    # if avg_relevance >= relevance_threshold:
    #     return "generate"
    #
    # # Condition 3: Has medium+ relevance docs (relaxed for small collections)
    # # If we have at least one medium relevance doc and some retrieval happened
    # if medium_count >= 1 and len(retrieved_docs) > 0 and avg_relevance >= 0.3:
    #     return "generate"
    #
    # # Can still retry - rewrite query
    # if retry_count < max_retries:
    #     return "rewrite"
    #
    # # Max retries exhausted - web search fallback
    # return "web_search"


def route_after_rewrite(state: RAGState) -> Literal["retrieve"]:
    """Route after query rewrite - always retry retrieval"""
    return "retrieve"


def route_after_web_search(state: RAGState) -> Literal["generate"]:
    """Route after web search - always proceed to generation"""
    return "generate"


def should_continue(state: RAGState) -> bool:
    """Check if workflow should continue (not errored)"""
    error_log = state.get("error_log", [])
    return len(error_log) == 0 or len(error_log) < 3  # Allow up to 3 errors
