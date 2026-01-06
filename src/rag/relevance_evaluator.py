"""Relevance Evaluator for document relevance scoring"""

from typing import List, Optional, Tuple

from src.config import get_settings
from src.core.models import (
    Document,
    RelevanceEvaluationOutput,
    RelevanceLevel,
)
from src.llm import LLMProvider, OpenAIProvider
from src.llm.prompts.relevance import RELEVANCE_EVALUATION_PROMPT


class RelevanceEvaluator:
    """Hybrid relevance evaluator using embedding similarity + LLM evaluation"""

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        # Lowered from 0.5 to 0.3 to include more documents for LLM evaluation
        embedding_threshold: float = 0.3,
    ):
        self.llm_provider = llm_provider or OpenAIProvider()
        self.embedding_threshold = embedding_threshold
        settings = get_settings()
        self.relevance_threshold = settings.relevance_threshold

    def _score_to_level(self, score: float) -> RelevanceLevel:
        """Convert numeric score to relevance level

        Thresholds adjusted for better recall:
        - HIGH: >= 0.6 (lowered from 0.8)
        - MEDIUM: >= 0.3 (lowered from 0.5)
        - LOW: < 0.3
        """
        if score >= 0.6:
            return RelevanceLevel.HIGH
        elif score >= 0.3:
            return RelevanceLevel.MEDIUM
        else:
            return RelevanceLevel.LOW

    async def evaluate(
        self,
        query: str,
        document: Document,
    ) -> RelevanceEvaluationOutput:
        """Evaluate relevance of a single document"""
        # First check embedding score if available (pre-filter)
        if document.embedding_score is not None:
            if document.embedding_score < self.embedding_threshold:
                # Skip LLM evaluation for clearly irrelevant documents
                return RelevanceEvaluationOutput(
                    relevance_score=document.embedding_score,
                    relevance_level=RelevanceLevel.LOW,
                    reason="Low embedding similarity - document unlikely to be relevant",
                    useful_parts=[],
                )

        # LLM-based detailed evaluation
        prompt = RELEVANCE_EVALUATION_PROMPT.format(
            query=query,
            source=document.metadata.source if document.metadata else "unknown",
            content=document.content[:2000],  # Truncate long documents
        )

        result = await self.llm_provider.generate_structured(
            prompt=prompt,
            response_model=RelevanceEvaluationOutput,
            system_prompt="You are an expert at evaluating document relevance. Be precise and objective.",
        )

        # Ensure level matches score
        result.relevance_level = self._score_to_level(result.relevance_score)

        # Update document with LLM relevance score
        document.llm_relevance_score = result.relevance_score

        # Calculate combined score if both available
        if document.embedding_score is not None:
            # Weighted average: 40% embedding, 60% LLM
            document.combined_score = (
                0.4 * document.embedding_score + 0.6 * result.relevance_score
            )

        return result

    async def evaluate_batch(
        self,
        query: str,
        documents: List[Document],
    ) -> List[RelevanceEvaluationOutput]:
        """Evaluate relevance of multiple documents"""
        results = []
        for doc in documents:
            result = await self.evaluate(query, doc)
            results.append(result)
        return results

    def calculate_metrics(
        self,
        evaluations: List[RelevanceEvaluationOutput],
        threshold: Optional[float] = None,
    ) -> dict:
        """Calculate aggregate relevance metrics"""
        if not evaluations:
            return {
                "avg_relevance": 0.0,
                "high_relevance_count": 0,
                "medium_relevance_count": 0,
                "low_relevance_count": 0,
                "sufficient": False,
            }

        threshold = threshold or self.relevance_threshold
        scores = [e.relevance_score for e in evaluations]

        high_count = sum(1 for e in evaluations if e.relevance_level == RelevanceLevel.HIGH)
        medium_count = sum(1 for e in evaluations if e.relevance_level == RelevanceLevel.MEDIUM)
        low_count = sum(1 for e in evaluations if e.relevance_level == RelevanceLevel.LOW)

        avg = sum(scores) / len(scores) if scores else 0.0

        # Relaxed sufficiency check:
        # - At least 1 high relevance doc, OR
        # - At least 1 medium relevance doc with avg >= threshold, OR
        # - avg >= threshold (for small collections)
        sufficient = (
            high_count >= 1 or
            (medium_count >= 1 and avg >= threshold) or
            avg >= threshold
        )

        return {
            "avg_relevance": avg,
            "high_relevance_count": high_count,
            "medium_relevance_count": medium_count,
            "low_relevance_count": low_count,
            "sufficient": sufficient,
        }

    def filter_relevant(
        self,
        documents: List[Document],
        evaluations: List[RelevanceEvaluationOutput],
        min_level: RelevanceLevel = RelevanceLevel.MEDIUM,
    ) -> Tuple[List[Document], List[RelevanceEvaluationOutput]]:
        """Filter documents by minimum relevance level"""
        level_order = {
            RelevanceLevel.LOW: 0,
            RelevanceLevel.MEDIUM: 1,
            RelevanceLevel.HIGH: 2,
        }
        min_order = level_order[min_level]

        filtered_docs = []
        filtered_evals = []

        for doc, eval_result in zip(documents, evaluations):
            if level_order[eval_result.relevance_level] >= min_order:
                filtered_docs.append(doc)
                filtered_evals.append(eval_result)

        return filtered_docs, filtered_evals
