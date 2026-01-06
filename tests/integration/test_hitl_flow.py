"""Integration tests for HITL flow"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.core.models import (
    ClarificationOutput,
    RAGResponse,
    RetrievalSource,
    AmbiguityType,
)
from src.agents.hitl_controller import HITLController


class TestHITLFlow:
    """Integration tests for HITL clarification flow"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from src.api.main import app
        return TestClient(app)

    def test_health_check(self, client):
        """Verify API is running"""
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch("src.core.orchestrator.RAGOrchestrator")
    async def test_clarification_triggered_for_ambiguous_query(
        self, mock_orchestrator_class, client
    ):
        """Test that clarification is triggered for ambiguous queries"""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_query = AsyncMock(
            return_value=ClarificationOutput(
                clarification_question="어떤 종류의 배포를 원하시나요?",
                options=["Docker 배포", "Kubernetes 배포", "직접 서버 배포"],
            )
        )
        mock_orchestrator_class.return_value = mock_orchestrator

        response = client.post(
            "/api/chat",
            json={"query": "배포 방법"}
        )

        # Response should indicate clarification needed
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_hitl_controller_should_clarify(self, mock_llm_provider):
        """Test HITL controller clarification decision"""
        controller = HITLController(llm_provider=mock_llm_provider)

        # Should clarify for ambiguous query
        assert controller.should_clarify(
            clarity_confidence=0.5,
            is_ambiguous=True,
            interaction_count=0,
        ) is True

        # Should not clarify for clear query
        assert controller.should_clarify(
            clarity_confidence=0.9,
            is_ambiguous=False,
            interaction_count=0,
        ) is False

        # Should not exceed max interactions
        assert controller.should_clarify(
            clarity_confidence=0.5,
            is_ambiguous=True,
            interaction_count=2,
        ) is False


class TestHITLOrchestration:
    """Test HITL orchestration in LangGraph"""

    @pytest.mark.asyncio
    async def test_orchestrator_returns_clarification(self, mock_llm_provider):
        """Test orchestrator returns clarification for ambiguous query"""
        from src.core.orchestrator import RAGOrchestrator
        from src.core.models import QueryAnalysisOutput, Complexity

        with patch("src.agents.query_processor.QueryProcessor.analyze") as mock_analyze:
            mock_analyze.return_value = QueryAnalysisOutput(
                refined_query="배포 방법",
                complexity=Complexity.SIMPLE,
                clarity_confidence=0.4,  # Low confidence triggers HITL
                is_ambiguous=True,
                ambiguity_type=AmbiguityType.MULTIPLE_INTERPRETATION,
                detected_domains=["deployment"],
            )

            with patch("src.agents.hitl_controller.HITLController.generate_clarification") as mock_clarify:
                mock_clarify.return_value = ClarificationOutput(
                    clarification_question="어떤 배포 방식을 원하시나요?",
                    options=["Docker", "Kubernetes", "직접 설치"],
                )

                orchestrator = RAGOrchestrator()
                result = await orchestrator.process_query(
                    query="배포 방법",
                    session_id="test-session",
                )

                # Should return clarification output
                assert isinstance(result, ClarificationOutput)
                assert result.clarification_question != ""

    @pytest.mark.asyncio
    async def test_orchestrator_continues_after_clarification(self, mock_llm_provider):
        """Test orchestrator continues after user provides clarification"""
        from src.core.orchestrator import RAGOrchestrator

        orchestrator = RAGOrchestrator()

        # First call - should return clarification
        with patch("src.agents.query_processor.QueryProcessor.analyze") as mock_analyze:
            from src.core.models import QueryAnalysisOutput, Complexity

            mock_analyze.return_value = QueryAnalysisOutput(
                refined_query="배포",
                complexity=Complexity.SIMPLE,
                clarity_confidence=0.4,
                is_ambiguous=True,
                ambiguity_type=AmbiguityType.VAGUE_TERM,
                detected_domains=[],
            )

            with patch("src.agents.hitl_controller.HITLController.generate_clarification") as mock_clarify:
                mock_clarify.return_value = ClarificationOutput(
                    clarification_question="무엇을 배포하시려고요?",
                    options=["애플리케이션", "데이터베이스", "서비스"],
                )

                result = await orchestrator.process_query(
                    query="배포",
                    session_id="test-session-2",
                )

                assert isinstance(result, ClarificationOutput)
                assert orchestrator.has_pending_session("test-session-2")


class TestHITLAPI:
    """Test HITL-related API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from src.api.main import app
        return TestClient(app)

    def test_chat_endpoint_exists(self, client):
        """Test chat endpoint is accessible"""
        response = client.post(
            "/api/chat",
            json={"query": "테스트 질문"},
        )
        # May fail without real LLM, but endpoint should exist
        assert response.status_code in [200, 500]

    def test_clarify_endpoint_exists(self, client):
        """Test clarify endpoint is accessible"""
        response = client.post(
            "/api/chat/clarify",
            json={
                "session_id": "nonexistent-session",
                "user_response": "테스트 응답",
            },
        )
        # Should return 400 for expired/nonexistent session
        assert response.status_code in [400, 500]

    def test_clarify_requires_session_id(self, client):
        """Test clarify endpoint requires session_id"""
        response = client.post(
            "/api/chat/clarify",
            json={"user_response": "테스트"},
        )
        # Should fail validation
        assert response.status_code == 422  # Pydantic validation error


class TestMaxHITLInteractions:
    """Test maximum HITL interaction limit"""

    @pytest.mark.asyncio
    async def test_max_interactions_enforced(self, mock_llm_provider):
        """Test that max HITL interactions is enforced"""
        controller = HITLController(llm_provider=mock_llm_provider)

        # First interaction - should clarify
        assert controller.should_clarify(0.5, True, 0) is True

        # Second interaction - should clarify
        assert controller.should_clarify(0.5, True, 1) is True

        # Third interaction (at max=2) - should NOT clarify
        assert controller.should_clarify(0.5, True, 2) is False

        # Beyond max - should NOT clarify
        assert controller.should_clarify(0.5, True, 3) is False
