"""Unit tests for Corrective RAG Engine"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.rag.corrective_engine import CorrectiveEngine, CorrectionAction
from src.core.models import Document, DocumentMetadata, RewriteStrategy


class TestCorrectiveEngine:
    """Test cases for CorrectiveEngine"""

    @pytest.fixture
    def mock_retriever(self):
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[
            Document(
                content="Test content",
                metadata=DocumentMetadata(source="test.md"),
                embedding_score=0.8
            )
        ])
        return retriever

    @pytest.fixture
    def mock_evaluator(self):
        evaluator = MagicMock()
        evaluator.evaluate_batch = AsyncMock()
        evaluator.calculate_metrics = MagicMock(return_value={
            "avg_relevance": 0.85,
            "high_relevance_count": 2,
            "sufficient": True
        })
        return evaluator

    @pytest.fixture
    def mock_rewriter(self):
        rewriter = MagicMock()
        rewriter.rewrite_auto = AsyncMock(
            return_value=("rewritten query", RewriteStrategy.SYNONYM_EXPANSION)
        )
        return rewriter

    @pytest.fixture
    def engine(self, mock_retriever, mock_evaluator, mock_rewriter):
        return CorrectiveEngine(
            retriever=mock_retriever,
            relevance_evaluator=mock_evaluator,
            query_rewriter=mock_rewriter,
            max_retries=2,
            min_high_relevance_docs=2
        )

    def test_should_correct_low_relevance(self, engine):
        """CR-001: Trigger correction on low relevance"""
        state = {
            "avg_relevance": 0.5,
            "high_relevance_count": 1,
            "retry_count": 0
        }

        assert engine.should_correct(state) is True

    def test_should_not_correct_sufficient_relevance(self, engine):
        """CR-002: No correction when relevance is sufficient"""
        state = {
            "avg_relevance": 0.85,
            "high_relevance_count": 3,
            "retry_count": 0
        }

        assert engine.should_correct(state) is False

    def test_should_not_correct_max_retries(self, engine):
        """CR-003: Respect max retry limit"""
        state = {
            "avg_relevance": 0.5,
            "high_relevance_count": 0,
            "retry_count": 2
        }

        assert engine.should_correct(state) is False

    def test_determine_action_proceed(self, engine):
        """Test proceed action when sufficient"""
        state = {
            "avg_relevance": 0.9,
            "high_relevance_count": 3,
            "retry_count": 0
        }

        assert engine.determine_next_action(state) == CorrectionAction.PROCEED

    def test_determine_action_rewrite(self, engine):
        """Test rewrite action when can retry"""
        state = {
            "avg_relevance": 0.5,
            "high_relevance_count": 0,
            "retry_count": 1
        }

        assert engine.determine_next_action(state) == CorrectionAction.REWRITE

    def test_determine_action_web_search(self, engine):
        """CR-007: Web search after max retries"""
        state = {
            "avg_relevance": 0.3,
            "high_relevance_count": 0,
            "retry_count": 2
        }

        assert engine.determine_next_action(state) == CorrectionAction.WEB_SEARCH

    @pytest.mark.asyncio
    async def test_retrieve_and_evaluate(self, engine, mock_retriever, mock_evaluator):
        """Test retrieve and evaluate pipeline"""
        mock_evaluator.evaluate_batch = AsyncMock(return_value=[])
        mock_evaluator.calculate_metrics = MagicMock(return_value={
            "avg_relevance": 0.8,
            "high_relevance_count": 1,
            "sufficient": False
        })

        docs, evals, metrics = await engine.retrieve_and_evaluate("test query")

        mock_retriever.retrieve.assert_called_once()
        mock_evaluator.evaluate_batch.assert_called_once()
        assert "avg_relevance" in metrics

    @pytest.mark.asyncio
    async def test_rewrite_and_retry(self, engine, mock_rewriter):
        """CR-004: Test retry count increment"""
        result = await engine.rewrite_and_retry(
            original_query="original",
            current_query="current",
            retry_count=0,
            previous_queries=["original"],
            previous_strategies=[],
        )

        assert result["retry_count"] == 1
        assert result["correction_triggered"] is True
        assert len(result["rewritten_queries"]) > 1
        mock_rewriter.rewrite_auto.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_correction_loop_no_correction_needed(self, engine, mock_evaluator):
        """Test loop when no correction needed"""
        mock_evaluator.calculate_metrics = MagicMock(return_value={
            "avg_relevance": 0.9,
            "high_relevance_count": 3,
            "sufficient": True
        })

        result = await engine.run_correction_loop("test query")

        assert result["correction_triggered"] is False
        assert result["retry_count"] == 0
        assert result["action_taken"] == "proceed"

    @pytest.mark.asyncio
    async def test_run_correction_loop_with_correction(self, engine, mock_evaluator, mock_rewriter):
        """Test loop with correction triggered"""
        # First call returns low relevance, second returns high
        mock_evaluator.calculate_metrics = MagicMock(side_effect=[
            {"avg_relevance": 0.4, "high_relevance_count": 0, "sufficient": False},
            {"avg_relevance": 0.9, "high_relevance_count": 2, "sufficient": True},
        ])

        result = await engine.run_correction_loop("test query")

        assert result["correction_triggered"] is True
        assert result["retry_count"] >= 1
