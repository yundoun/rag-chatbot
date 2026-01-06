"""LangGraph Orchestrator for RAG workflow"""

from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from langgraph.graph import StateGraph, END

from src.config import get_settings
from src.core.state import RAGState, create_initial_state
from src.core.models import RAGResponse, RetrievalSource, ClarificationOutput
from src.core.nodes import (
    analyze_query_node,
    retrieve_documents_node,
    evaluate_relevance_node,
    rewrite_query_node,
    generate_response_node,
    evaluate_quality_node,
    web_search_node,
    clarify_hitl_node,
    process_hitl_response_node,
    decompose_query_node,
)
from src.core.edges import (
    route_after_analysis,
    route_after_evaluation,
    route_after_rewrite,
    route_after_web_search,
    route_after_hitl_response,
    route_after_decompose,
)


class RAGOrchestrator:
    """LangGraph-based RAG workflow orchestrator"""

    # Interrupt marker for HITL
    HITL_INTERRUPT = "__HITL_INTERRUPT__"

    def __init__(self):
        self.graph = self._build_graph()
        self.settings = get_settings()
        # Store pending HITL sessions
        self._pending_sessions: Dict[str, RAGState] = {}

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        # Create graph with state schema
        graph = StateGraph(RAGState)

        # Add nodes
        graph.add_node("analyze_query", analyze_query_node)
        graph.add_node("clarify_hitl", clarify_hitl_node)
        graph.add_node("process_hitl_response", process_hitl_response_node)
        graph.add_node("decompose_query", decompose_query_node)
        graph.add_node("retrieve", retrieve_documents_node)
        graph.add_node("evaluate_relevance", evaluate_relevance_node)
        graph.add_node("rewrite_query", rewrite_query_node)
        graph.add_node("web_search", web_search_node)
        graph.add_node("generate_response", generate_response_node)
        graph.add_node("evaluate_quality", evaluate_quality_node)

        # Set entry point
        graph.set_entry_point("analyze_query")

        # Add edges
        # After analysis -> conditional routing (clarify/decompose/retrieve)
        graph.add_conditional_edges(
            "analyze_query",
            route_after_analysis,
            {
                "clarify": "clarify_hitl",
                "decompose": "decompose_query",
                "retrieve": "retrieve",
            },
        )

        # After clarify_hitl -> END (will be resumed with user response)
        # This creates an interrupt point
        graph.add_edge("clarify_hitl", END)

        # After process_hitl_response -> conditional routing
        graph.add_conditional_edges(
            "process_hitl_response",
            route_after_hitl_response,
            {
                "decompose": "decompose_query",
                "retrieve": "retrieve",
            },
        )

        # After decompose -> retrieve
        graph.add_edge("decompose_query", "retrieve")

        # After retrieval -> evaluate relevance
        graph.add_edge("retrieve", "evaluate_relevance")

        # After evaluation -> conditional routing
        graph.add_conditional_edges(
            "evaluate_relevance",
            route_after_evaluation,
            {
                "generate": "generate_response",
                "rewrite": "rewrite_query",
                "web_search": "web_search",
            },
        )

        # After rewrite -> retrieve again
        graph.add_edge("rewrite_query", "retrieve")

        # After web search -> generate
        graph.add_edge("web_search", "generate_response")

        # After generation -> evaluate quality
        graph.add_edge("generate_response", "evaluate_quality")

        # After quality evaluation -> END
        graph.add_edge("evaluate_quality", END)

        return graph.compile()

    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_response: Optional[str] = None,
    ) -> RAGResponse | ClarificationOutput:
        """Process a query through the RAG workflow

        Args:
            query: The user's query
            session_id: Optional session ID for tracking
            user_response: Optional user response for HITL continuation

        Returns:
            RAGResponse if workflow completed, ClarificationOutput if HITL needed
        """
        start_time = datetime.now()
        session_id = session_id or str(uuid.uuid4())

        # Check if this is a HITL continuation
        if user_response and session_id in self._pending_sessions:
            return await self._continue_with_hitl_response(
                session_id, user_response, start_time
            )

        # Create initial state
        initial_state = create_initial_state(query, session_id)

        # Run the graph
        final_state = await self._run_graph(initial_state)

        # Check if HITL interrupt occurred
        if final_state.get("current_node") == "clarify_hitl":
            # Store state for later continuation
            self._pending_sessions[session_id] = final_state

            return ClarificationOutput(
                clarification_question=final_state.get("clarification_question", ""),
                options=final_state.get("clarification_options", []),
            )

        # Build and return response
        return self._build_response(final_state, session_id, start_time)

    async def _continue_with_hitl_response(
        self,
        session_id: str,
        user_response: str,
        start_time: datetime,
    ) -> RAGResponse | ClarificationOutput:
        """Continue workflow after HITL response"""
        # Get stored state
        stored_state = self._pending_sessions.pop(session_id)

        # Update state with user response
        stored_state["user_response"] = user_response

        # Create a new graph starting from process_hitl_response
        continuation_graph = self._build_continuation_graph()

        # Run from process_hitl_response
        final_state = await self._run_graph(stored_state, graph=continuation_graph)

        # Check if another HITL is needed
        if final_state.get("current_node") == "clarify_hitl":
            self._pending_sessions[session_id] = final_state
            return ClarificationOutput(
                clarification_question=final_state.get("clarification_question", ""),
                options=final_state.get("clarification_options", []),
            )

        return self._build_response(final_state, session_id, start_time)

    def _build_continuation_graph(self) -> StateGraph:
        """Build graph for HITL continuation"""
        from src.core.nodes import (
            process_hitl_response_node,
            decompose_query_node,
            retrieve_documents_node,
            evaluate_relevance_node,
            rewrite_query_node,
            web_search_node,
            generate_response_node,
            evaluate_quality_node,
        )

        graph = StateGraph(RAGState)

        # Add nodes (subset for continuation)
        graph.add_node("process_hitl_response", process_hitl_response_node)
        graph.add_node("decompose_query", decompose_query_node)
        graph.add_node("retrieve", retrieve_documents_node)
        graph.add_node("evaluate_relevance", evaluate_relevance_node)
        graph.add_node("rewrite_query", rewrite_query_node)
        graph.add_node("web_search", web_search_node)
        graph.add_node("generate_response", generate_response_node)
        graph.add_node("evaluate_quality", evaluate_quality_node)

        # Set entry point for continuation
        graph.set_entry_point("process_hitl_response")

        # Add edges
        graph.add_conditional_edges(
            "process_hitl_response",
            route_after_hitl_response,
            {
                "decompose": "decompose_query",
                "retrieve": "retrieve",
            },
        )

        graph.add_edge("decompose_query", "retrieve")
        graph.add_edge("retrieve", "evaluate_relevance")

        graph.add_conditional_edges(
            "evaluate_relevance",
            route_after_evaluation,
            {
                "generate": "generate_response",
                "rewrite": "rewrite_query",
                "web_search": "web_search",
            },
        )

        graph.add_edge("rewrite_query", "retrieve")
        graph.add_edge("web_search", "generate_response")
        graph.add_edge("generate_response", "evaluate_quality")
        graph.add_edge("evaluate_quality", END)

        return graph.compile()

    async def _run_graph(
        self,
        initial_state: RAGState,
        graph: Optional[StateGraph] = None,
    ) -> RAGState:
        """Run graph and return final state"""
        target_graph = graph or self.graph
        final_state = initial_state.copy()

        async for state in target_graph.astream(initial_state):
            for node_name, node_state in state.items():
                if node_state:
                    final_state = {**final_state, **node_state}

        return final_state

    def _build_response(
        self,
        final_state: RAGState,
        session_id: str,
        start_time: datetime,
    ) -> RAGResponse:
        """Build RAGResponse from final state"""
        end_time = datetime.now()
        processing_time_ms = int((end_time - start_time).total_seconds() * 1000)

        # Determine retrieval source
        retrieval_source = RetrievalSource.VECTOR
        if final_state.get("web_search_triggered"):
            retrieval_source = RetrievalSource.WEB
            if final_state.get("retrieved_docs"):
                retrieval_source = RetrievalSource.HYBRID

        # Build response
        return RAGResponse(
            response=final_state.get("generated_response", ""),
            sources=final_state.get("sources", []),
            confidence=final_state.get("response_confidence", 0.0),
            needs_disclaimer=final_state.get("needs_disclaimer", True),
            retrieval_source=retrieval_source,
            processing_time_ms=processing_time_ms,
            session_id=session_id,
            debug=self._build_debug_info(final_state) if self.settings.debug else None,
        )

    def has_pending_session(self, session_id: str) -> bool:
        """Check if session has pending HITL interaction"""
        return session_id in self._pending_sessions

    def get_pending_clarification(self, session_id: str) -> Optional[ClarificationOutput]:
        """Get pending clarification for a session"""
        if session_id not in self._pending_sessions:
            return None

        state = self._pending_sessions[session_id]
        return ClarificationOutput(
            clarification_question=state.get("clarification_question", ""),
            options=state.get("clarification_options", []),
        )

    def _build_debug_info(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Build debug information from final state"""
        return {
            "query_analysis": {
                "complexity": state.get("complexity"),
                "clarity_confidence": state.get("clarity_confidence"),
                "is_ambiguous": state.get("is_ambiguous"),
                "detected_domains": state.get("detected_domains"),
            },
            "retrieval": {
                "avg_relevance": state.get("avg_relevance"),
                "high_relevance_count": state.get("high_relevance_count"),
                "retry_count": state.get("retry_count", 0),
                "correction_triggered": state.get("correction_triggered", False),
                "rewritten_queries": state.get("rewritten_queries", []),
            },
            "web_search": {
                "triggered": state.get("web_search_triggered", False),
                "confidence": state.get("web_confidence", 0.0),
            },
            "response": {
                "confidence": state.get("response_confidence"),
                "needs_disclaimer": state.get("needs_disclaimer"),
            },
            "performance": {
                "total_llm_calls": state.get("total_llm_calls", 0),
            },
        }


# Singleton instance for convenience
_orchestrator: Optional[RAGOrchestrator] = None


def get_orchestrator() -> RAGOrchestrator:
    """Get or create the RAG orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = RAGOrchestrator()
    return _orchestrator
