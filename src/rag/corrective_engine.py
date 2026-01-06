"""Corrective RAG Engine for retrieval correction loop"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.config import get_settings
from src.core.models import Document, RelevanceLevel, RewriteStrategy
from src.rag.retriever import DocumentRetriever
from src.rag.relevance_evaluator import RelevanceEvaluator, RelevanceEvaluationOutput
from src.rag.query_rewriter import QueryRewriter


class CorrectionAction(str, Enum):
    """Possible correction actions"""

    PROCEED = "proceed"  # Sufficient relevance, proceed to response
    REWRITE = "rewrite"  # Rewrite query and retry
    WEB_SEARCH = "web_search"  # Fall back to web search
    FAIL = "fail"  # Cannot improve, return partial response


class CorrectiveEngine:
    """Orchestrates the retrieval correction loop"""

    def __init__(
        self,
        retriever: Optional[DocumentRetriever] = None,
        relevance_evaluator: Optional[RelevanceEvaluator] = None,
        query_rewriter: Optional[QueryRewriter] = None,
        max_retries: int = 2,
        min_high_relevance_docs: int = 2,
    ):
        self.retriever = retriever or DocumentRetriever()
        self.relevance_evaluator = relevance_evaluator or RelevanceEvaluator()
        self.query_rewriter = query_rewriter or QueryRewriter()

        settings = get_settings()
        self.max_retries = max_retries or settings.max_correction_retries
        self.min_high_relevance_docs = min_high_relevance_docs or settings.min_high_relevance_docs
        self.relevance_threshold = settings.relevance_threshold

    def should_correct(self, state: Dict[str, Any]) -> bool:
        """Determine if correction is needed based on current state"""
        avg_relevance = state.get("avg_relevance", 0.0)
        high_count = state.get("high_relevance_count", 0)
        retry_count = state.get("retry_count", 0)

        # Don't correct if max retries reached
        if retry_count >= self.max_retries:
            return False

        # Correct if insufficient relevance
        if high_count < self.min_high_relevance_docs and avg_relevance < self.relevance_threshold:
            return True

        return False

    def determine_next_action(self, state: Dict[str, Any]) -> CorrectionAction:
        """Determine the next action based on state"""
        avg_relevance = state.get("avg_relevance", 0.0)
        high_count = state.get("high_relevance_count", 0)
        retry_count = state.get("retry_count", 0)

        # Sufficient relevance - proceed
        if high_count >= self.min_high_relevance_docs or avg_relevance >= self.relevance_threshold:
            return CorrectionAction.PROCEED

        # Can still retry - rewrite
        if retry_count < self.max_retries:
            return CorrectionAction.REWRITE

        # Max retries exhausted - web search
        return CorrectionAction.WEB_SEARCH

    async def retrieve_and_evaluate(
        self,
        query: str,
        domains: Optional[List[str]] = None,
    ) -> Tuple[List[Document], List[RelevanceEvaluationOutput], Dict[str, Any]]:
        """Retrieve documents and evaluate their relevance"""
        # Retrieve documents
        try:
            documents = await self.retriever.retrieve(query, domains=domains)
        except Exception:
            documents = []

        if not documents:
            return [], [], {
                "avg_relevance": 0.0,
                "high_relevance_count": 0,
                "sufficient": False,
            }

        # Evaluate relevance
        evaluations = await self.relevance_evaluator.evaluate_batch(query, documents)

        # Calculate metrics
        metrics = self.relevance_evaluator.calculate_metrics(evaluations)

        return documents, evaluations, metrics

    async def rewrite_and_retry(
        self,
        original_query: str,
        current_query: str,
        retry_count: int,
        previous_queries: List[str],
        previous_strategies: List[str],
        domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Rewrite query and retry retrieval"""
        # Rewrite query
        new_query, strategy = await self.query_rewriter.rewrite_auto(
            query=current_query,
            retry_count=retry_count,
            previous_queries=previous_queries,
            previous_strategies=previous_strategies,
        )

        # Update tracking
        updated_queries = previous_queries + [new_query]
        updated_strategies = previous_strategies + [strategy.value]

        # Retrieve with new query
        documents, evaluations, metrics = await self.retrieve_and_evaluate(
            new_query, domains
        )

        return {
            "refined_query": new_query,
            "strategy_used": strategy.value,
            "rewritten_queries": updated_queries,
            "previous_strategies": updated_strategies,
            "retry_count": retry_count + 1,
            "documents": documents,
            "evaluations": evaluations,
            "metrics": metrics,
            "correction_triggered": True,
        }

    async def run_correction_loop(
        self,
        query: str,
        domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run the full correction loop.

        Returns a dict with:
        - documents: List of relevant documents
        - evaluations: List of relevance evaluations
        - metrics: Relevance metrics
        - correction_triggered: Whether correction was needed
        - retry_count: Number of retries performed
        - rewritten_queries: List of rewritten queries
        - final_query: The query that produced results
        - action_taken: Final action (proceed/web_search)
        """
        current_query = query
        retry_count = 0
        rewritten_queries: List[str] = [query]
        previous_strategies: List[str] = []
        correction_triggered = False

        # Initial retrieval
        documents, evaluations, metrics = await self.retrieve_and_evaluate(
            current_query, domains
        )

        # Build state for decision
        state = {
            "avg_relevance": metrics.get("avg_relevance", 0.0),
            "high_relevance_count": metrics.get("high_relevance_count", 0),
            "retry_count": retry_count,
        }

        # Correction loop
        while self.should_correct(state):
            correction_triggered = True

            # Rewrite and retry
            result = await self.rewrite_and_retry(
                original_query=query,
                current_query=current_query,
                retry_count=retry_count,
                previous_queries=rewritten_queries,
                previous_strategies=previous_strategies,
                domains=domains,
            )

            # Update state
            current_query = result["refined_query"]
            retry_count = result["retry_count"]
            rewritten_queries = result["rewritten_queries"]
            previous_strategies = result["previous_strategies"]
            documents = result["documents"]
            evaluations = result["evaluations"]
            metrics = result["metrics"]

            state = {
                "avg_relevance": metrics.get("avg_relevance", 0.0),
                "high_relevance_count": metrics.get("high_relevance_count", 0),
                "retry_count": retry_count,
            }

        # Determine final action
        final_action = self.determine_next_action(state)

        return {
            "documents": documents,
            "evaluations": evaluations,
            "metrics": metrics,
            "correction_triggered": correction_triggered,
            "retry_count": retry_count,
            "rewritten_queries": rewritten_queries,
            "final_query": current_query,
            "action_taken": final_action.value,
            "web_search_needed": final_action == CorrectionAction.WEB_SEARCH,
        }
