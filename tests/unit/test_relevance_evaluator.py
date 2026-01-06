"""Unit tests for Relevance Evaluator"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.rag.relevance_evaluator import RelevanceEvaluator
from src.core.models import (
    Document,
    DocumentMetadata,
    RelevanceLevel,
    RelevanceEvaluationOutput,
)


class TestRelevanceEvaluator:
    """Test cases for RelevanceEvaluator"""

    @pytest.fixture
    def evaluator(self, mock_llm_provider):
        return RelevanceEvaluator(llm_provider=mock_llm_provider)

    @pytest.fixture
    def sample_relevant_doc(self):
        return Document(
            content="Docker를 사용한 배포 방법: 1. Dockerfile 작성 2. 이미지 빌드 3. 컨테이너 실행",
            metadata=DocumentMetadata(
                source="deployment.md",
                title="배포 가이드",
            ),
            embedding_score=0.9,
        )

    @pytest.fixture
    def sample_irrelevant_doc(self):
        return Document(
            content="회사 휴가 정책: 연차 15일, 병가 5일 제공됩니다.",
            metadata=DocumentMetadata(
                source="hr-policy.md",
                title="HR 정책",
            ),
            embedding_score=0.3,
        )

    @pytest.mark.asyncio
    async def test_evaluate_high_relevance(self, evaluator, mock_llm_provider, sample_relevant_doc):
        """RE-001: High relevance document evaluation"""
        mock_llm_provider.generate_structured = AsyncMock(
            return_value=RelevanceEvaluationOutput(
                relevance_score=0.9,
                relevance_level=RelevanceLevel.HIGH,
                reason="Document directly addresses Docker deployment",
                useful_parts=["Dockerfile 작성", "이미지 빌드"],
            )
        )

        result = await evaluator.evaluate("Docker 배포 방법", sample_relevant_doc)

        assert result.relevance_score >= 0.8
        assert result.relevance_level == RelevanceLevel.HIGH
        assert len(result.useful_parts) > 0

    @pytest.mark.asyncio
    async def test_evaluate_low_relevance(self, evaluator, mock_llm_provider, sample_irrelevant_doc):
        """RE-003: Low relevance document skipped by embedding filter"""
        # With low embedding score, should skip LLM evaluation
        result = await evaluator.evaluate("Docker 배포 방법", sample_irrelevant_doc)

        assert result.relevance_score < 0.5
        assert result.relevance_level == RelevanceLevel.LOW

    @pytest.mark.asyncio
    async def test_score_to_level_mapping(self, evaluator):
        """RE-008: Score to level mapping is consistent"""
        assert evaluator._score_to_level(0.9) == RelevanceLevel.HIGH
        assert evaluator._score_to_level(0.8) == RelevanceLevel.HIGH
        assert evaluator._score_to_level(0.79) == RelevanceLevel.MEDIUM
        assert evaluator._score_to_level(0.5) == RelevanceLevel.MEDIUM
        assert evaluator._score_to_level(0.49) == RelevanceLevel.LOW
        assert evaluator._score_to_level(0.0) == RelevanceLevel.LOW

    @pytest.mark.asyncio
    async def test_calculate_metrics(self, evaluator):
        """Test metrics calculation"""
        evaluations = [
            RelevanceEvaluationOutput(
                relevance_score=0.9, relevance_level=RelevanceLevel.HIGH,
                reason="", useful_parts=[]
            ),
            RelevanceEvaluationOutput(
                relevance_score=0.85, relevance_level=RelevanceLevel.HIGH,
                reason="", useful_parts=[]
            ),
            RelevanceEvaluationOutput(
                relevance_score=0.6, relevance_level=RelevanceLevel.MEDIUM,
                reason="", useful_parts=[]
            ),
        ]

        metrics = evaluator.calculate_metrics(evaluations)

        assert metrics["high_relevance_count"] == 2
        assert metrics["medium_relevance_count"] == 1
        assert metrics["low_relevance_count"] == 0
        assert metrics["avg_relevance"] > 0.7
        assert metrics["sufficient"] is True  # 2 high relevance docs

    @pytest.mark.asyncio
    async def test_calculate_metrics_insufficient(self, evaluator):
        """Test metrics when insufficient relevance"""
        evaluations = [
            RelevanceEvaluationOutput(
                relevance_score=0.4, relevance_level=RelevanceLevel.LOW,
                reason="", useful_parts=[]
            ),
            RelevanceEvaluationOutput(
                relevance_score=0.3, relevance_level=RelevanceLevel.LOW,
                reason="", useful_parts=[]
            ),
        ]

        metrics = evaluator.calculate_metrics(evaluations)

        assert metrics["high_relevance_count"] == 0
        assert metrics["sufficient"] is False

    @pytest.mark.asyncio
    async def test_filter_relevant_documents(self, evaluator):
        """Test filtering documents by relevance level"""
        docs = [
            Document(content="High", metadata=DocumentMetadata(source="a.md")),
            Document(content="Medium", metadata=DocumentMetadata(source="b.md")),
            Document(content="Low", metadata=DocumentMetadata(source="c.md")),
        ]
        evals = [
            RelevanceEvaluationOutput(
                relevance_score=0.9, relevance_level=RelevanceLevel.HIGH,
                reason="", useful_parts=[]
            ),
            RelevanceEvaluationOutput(
                relevance_score=0.6, relevance_level=RelevanceLevel.MEDIUM,
                reason="", useful_parts=[]
            ),
            RelevanceEvaluationOutput(
                relevance_score=0.3, relevance_level=RelevanceLevel.LOW,
                reason="", useful_parts=[]
            ),
        ]

        filtered_docs, filtered_evals = evaluator.filter_relevant(
            docs, evals, min_level=RelevanceLevel.MEDIUM
        )

        assert len(filtered_docs) == 2
        assert filtered_docs[0].content == "High"
        assert filtered_docs[1].content == "Medium"
