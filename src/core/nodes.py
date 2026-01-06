"""LangGraph Node implementations for RAG workflow"""

from datetime import datetime
from typing import Any, Dict

from src.core.state import RAGState
from src.core.models import Document, DocumentMetadata, AmbiguityType
from src.agents.query_processor import QueryProcessor
from src.agents.hitl_controller import HITLController
from src.agents.web_search_agent import WebSearchAgent
from src.agents.agentic_controller import AgenticController
from src.rag.retriever import DocumentRetriever
from src.rag.relevance_evaluator import RelevanceEvaluator
from src.rag.query_rewriter import QueryRewriter
from src.rag.response_generator import ResponseGenerator


async def analyze_query_node(state: RAGState) -> Dict[str, Any]:
    """Analyze user query for complexity, clarity, and ambiguity"""
    processor = QueryProcessor()
    hitl = HITLController()

    analysis = await processor.analyze(state["query"])

    # Check if clarification is needed
    clarification_needed = hitl.should_clarify(
        clarity_confidence=analysis.clarity_confidence,
        is_ambiguous=analysis.is_ambiguous,
        interaction_count=state.get("interaction_count", 0),
    )

    return {
        "refined_query": analysis.refined_query or state["query"],
        "complexity": analysis.complexity.value,
        "clarity_confidence": analysis.clarity_confidence,
        "is_ambiguous": analysis.is_ambiguous,
        "ambiguity_type": analysis.ambiguity_type.value if analysis.ambiguity_type else None,
        "detected_domains": analysis.detected_domains,
        "clarification_needed": clarification_needed,
        "current_node": "analyze_query",
        "total_llm_calls": state.get("total_llm_calls", 0) + 1,
    }


async def retrieve_documents_node(state: RAGState) -> Dict[str, Any]:
    """Retrieve documents from vector store"""
    retriever = DocumentRetriever()

    query = state.get("refined_query") or state["query"]
    # domains 필터 비활성화 - 문서에 domain 메타데이터가 없으면 필터링으로 결과가 0개가 됨
    # domains = state.get("detected_domains")

    try:
        # domains 필터 없이 검색
        documents = await retriever.retrieve(query, domains=None)
    except Exception as e:
        print(f"Retrieval error: {type(e).__name__}: {e}")
        documents = []

    # Convert to serializable format
    retrieved_docs = []
    for doc in documents:
        retrieved_docs.append(Document(
            content=doc.content,
            metadata=doc.metadata,
            embedding_score=doc.embedding_score,
        ))

    return {
        "retrieved_docs": retrieved_docs,
        "current_node": "retrieve_documents",
    }


async def evaluate_relevance_node(state: RAGState) -> Dict[str, Any]:
    """Evaluate relevance of retrieved documents"""
    evaluator = RelevanceEvaluator()

    query = state.get("refined_query") or state["query"]
    documents = state.get("retrieved_docs", [])

    if not documents:
        return {
            "relevance_scores": [],
            "avg_relevance": 0.0,
            "high_relevance_count": 0,
            "medium_relevance_count": 0,
            "current_node": "evaluate_relevance",
        }

    evaluations = await evaluator.evaluate_batch(query, documents)
    metrics = evaluator.calculate_metrics(evaluations)

    return {
        "relevance_scores": [e.relevance_score for e in evaluations],
        "avg_relevance": metrics["avg_relevance"],
        "high_relevance_count": metrics["high_relevance_count"],
        "medium_relevance_count": metrics["medium_relevance_count"],
        "current_node": "evaluate_relevance",
        "total_llm_calls": state.get("total_llm_calls", 0) + len(documents),
    }


async def rewrite_query_node(state: RAGState) -> Dict[str, Any]:
    """Rewrite query for better retrieval"""
    rewriter = QueryRewriter()

    current_query = state.get("refined_query") or state["query"]
    retry_count = state.get("retry_count", 0)
    previous_queries = state.get("rewritten_queries", [])

    # Get strategies used from queries (simplified tracking)
    previous_strategies = []

    new_query, strategy = await rewriter.rewrite_auto(
        query=current_query,
        retry_count=retry_count,
        previous_queries=previous_queries,
        previous_strategies=previous_strategies,
    )

    return {
        "refined_query": new_query,
        "rewritten_queries": previous_queries + [new_query],
        "retry_count": retry_count + 1,
        "correction_triggered": True,
        "current_node": "rewrite_query",
        "total_llm_calls": state.get("total_llm_calls", 0) + 1,
    }


async def generate_response_node(state: RAGState) -> Dict[str, Any]:
    """Generate response from retrieved documents"""
    generator = ResponseGenerator()

    query = state["query"]  # Use original query for response
    documents = state.get("retrieved_docs", [])
    web_results = state.get("web_results", [])

    response = await generator.generate(
        query=query,
        documents=documents,
        web_results=web_results if web_results else None,
    )

    return {
        "generated_response": response.response,
        "sources": response.sources,
        "current_node": "generate_response",
        "total_llm_calls": state.get("total_llm_calls", 0) + 1,
    }


async def evaluate_quality_node(state: RAGState) -> Dict[str, Any]:
    """Evaluate quality of generated response"""
    # Import here to avoid circular dependency
    from src.rag.quality_evaluator import QualityEvaluator

    evaluator = QualityEvaluator()

    query = state["query"]
    response = state.get("generated_response", "")
    sources = state.get("sources", [])
    documents = state.get("retrieved_docs", [])
    web_search_triggered = state.get("web_search_triggered", False)

    evaluation = await evaluator.evaluate(
        query=query,
        response=response,
        sources=sources,
    )

    # Only show disclaimer if web search was actually used
    # Don't show "웹 검색 결과 포함" banner when only internal docs were used
    needs_disclaimer = web_search_triggered

    return {
        "response_confidence": evaluation.confidence,
        "needs_disclaimer": needs_disclaimer,
        "end_time": datetime.now(),
        "current_node": "evaluate_quality",
        "total_llm_calls": state.get("total_llm_calls", 0) + 1,
    }


async def web_search_node(state: RAGState) -> Dict[str, Any]:
    """Perform web search fallback"""
    agent = WebSearchAgent()

    query = state.get("refined_query") or state["query"]
    domains = state.get("detected_domains", [])

    try:
        web_results = await agent.search(
            query=query,
            detected_domains=domains,
            optimize_query=True,
        )

        # Calculate average confidence
        web_confidence = 0.0
        if web_results:
            scores = [r.combined_score or 0 for r in web_results]
            web_confidence = sum(scores) / len(scores)

        return {
            "web_search_triggered": True,
            "web_results": web_results,
            "web_confidence": web_confidence,
            "needs_disclaimer": True,  # Always show disclaimer for web results
            "current_node": "web_search",
        }
    except Exception as e:
        return {
            "web_search_triggered": True,
            "web_results": [],
            "web_confidence": 0.0,
            "needs_disclaimer": True,
            "error_log": state.get("error_log", []) + [f"Web search error: {str(e)}"],
            "current_node": "web_search",
        }


async def clarify_hitl_node(state: RAGState) -> Dict[str, Any]:
    """Generate clarification question for HITL

    Note: This node generates the clarification question and options.
    The actual user interaction happens via WebSocket, and the
    user_response is provided when resuming the workflow.
    """
    hitl = HITLController()

    query = state["query"]
    ambiguity_type_str = state.get("ambiguity_type")
    ambiguity_type = AmbiguityType(ambiguity_type_str) if ambiguity_type_str else None

    clarification = await hitl.generate_clarification(
        query=query,
        ambiguity_type=ambiguity_type,
        clarity_confidence=state.get("clarity_confidence", 0.0),
        detected_domains=state.get("detected_domains", []),
    )

    return {
        "clarification_question": clarification.clarification_question,
        "clarification_options": clarification.options,
        "interaction_count": state.get("interaction_count", 0) + 1,
        "current_node": "clarify_hitl",
        "total_llm_calls": state.get("total_llm_calls", 0) + 1,
    }


async def process_hitl_response_node(state: RAGState) -> Dict[str, Any]:
    """Process user's HITL response and refine query"""
    from src.core.models import HITLResponse

    hitl = HITLController()

    user_response_text = state.get("user_response", "")
    clarification_question = state.get("clarification_question", "")
    clarification_options = state.get("clarification_options", [])

    # Determine if it was a selection or custom input
    if user_response_text in clarification_options:
        response = HITLResponse(selected_option=user_response_text)
    else:
        response = HITLResponse(custom_input=user_response_text)

    # Refine the query based on user response
    refined_query = await hitl.refine_query(
        original_query=state["query"],
        clarification_question=clarification_question,
        user_response=response,
    )

    return {
        "refined_query": refined_query,
        "clarification_needed": False,
        "is_ambiguous": False,
        "current_node": "process_hitl_response",
        "total_llm_calls": state.get("total_llm_calls", 0) + 1,
    }


async def decompose_query_node(state: RAGState) -> Dict[str, Any]:
    """Decompose complex query into sub-questions"""
    controller = AgenticController()

    query = state.get("refined_query") or state["query"]
    complexity = state.get("complexity", "simple")
    domains = state.get("detected_domains", [])

    if not controller.should_decompose(complexity):
        return {
            "current_node": "decompose_query",
        }

    decomposition = await controller.decompose_query(
        query=query,
        complexity=complexity,
        detected_domains=domains,
    )

    # Store decomposition info in state for later use
    return {
        "sub_questions": [
            {"id": sq.id, "question": sq.question, "domain": sq.target_domain}
            for sq in decomposition.sub_questions
        ],
        "parallel_groups": decomposition.parallel_groups,
        "synthesis_guide": decomposition.synthesis_guide,
        "current_node": "decompose_query",
        "total_llm_calls": state.get("total_llm_calls", 0) + 1,
    }
