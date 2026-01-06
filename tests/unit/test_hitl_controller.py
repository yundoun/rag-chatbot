"""Unit tests for HITL Controller"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.hitl_controller import HITLController, ClarificationResult, RefinedQueryResult
from src.core.models import AmbiguityType, ClarificationOutput, HITLResponse


class TestHITLController:
    """Test cases for HITLController"""

    @pytest.fixture
    def controller(self, mock_llm_provider):
        """Create controller with mocked LLM"""
        return HITLController(llm_provider=mock_llm_provider)

    def test_should_clarify_when_ambiguous(self, controller):
        """Should return True when query is ambiguous"""
        result = controller.should_clarify(
            clarity_confidence=0.5,
            is_ambiguous=True,
            interaction_count=0,
        )
        assert result is True

    def test_should_clarify_when_low_confidence(self, controller):
        """Should return True when clarity confidence is low"""
        result = controller.should_clarify(
            clarity_confidence=0.6,
            is_ambiguous=False,
            interaction_count=0,
        )
        assert result is True

    def test_should_not_clarify_when_clear(self, controller):
        """Should return False when query is clear"""
        result = controller.should_clarify(
            clarity_confidence=0.9,
            is_ambiguous=False,
            interaction_count=0,
        )
        assert result is False

    def test_should_not_clarify_when_max_interactions_reached(self, controller):
        """Should return False when max interactions reached"""
        result = controller.should_clarify(
            clarity_confidence=0.5,
            is_ambiguous=True,
            interaction_count=2,  # Max is 2
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_generate_clarification_success(self, controller, mock_llm_provider):
        """Test successful clarification generation"""
        mock_llm_provider.generate_structured = AsyncMock(
            return_value=ClarificationResult(
                clarification_question="어떤 종류의 배포를 원하시나요?",
                options=["Docker 배포", "Kubernetes 배포", "직접 서버 배포"],
            )
        )

        result = await controller.generate_clarification(
            query="배포 방법 알려줘",
            ambiguity_type=AmbiguityType.MULTIPLE_INTERPRETATION,
            clarity_confidence=0.5,
            detected_domains=["deployment"],
        )

        assert isinstance(result, ClarificationOutput)
        assert "배포" in result.clarification_question
        assert len(result.options) >= 2

    @pytest.mark.asyncio
    async def test_generate_clarification_fallback(self, controller, mock_llm_provider):
        """Test fallback when LLM fails"""
        mock_llm_provider.generate_structured = AsyncMock(side_effect=Exception("LLM Error"))

        result = await controller.generate_clarification(
            query="뭔가 알려줘",
            ambiguity_type=AmbiguityType.VAGUE_TERM,
            clarity_confidence=0.3,
            detected_domains=[],
        )

        assert isinstance(result, ClarificationOutput)
        assert result.clarification_question != ""
        assert len(result.options) >= 2

    @pytest.mark.asyncio
    async def test_refine_query_with_selected_option(self, controller, mock_llm_provider):
        """Test query refinement with selected option"""
        mock_llm_provider.generate_structured = AsyncMock(
            return_value=RefinedQueryResult(
                refined_query="Docker를 사용한 컨테이너 배포 방법",
            )
        )

        result = await controller.refine_query(
            original_query="배포 방법 알려줘",
            clarification_question="어떤 종류의 배포를 원하시나요?",
            user_response=HITLResponse(selected_option="Docker 배포"),
        )

        assert "Docker" in result

    @pytest.mark.asyncio
    async def test_refine_query_with_custom_input(self, controller, mock_llm_provider):
        """Test query refinement with custom input"""
        mock_llm_provider.generate_structured = AsyncMock(
            return_value=RefinedQueryResult(
                refined_query="AWS ECS를 사용한 컨테이너 배포 방법",
            )
        )

        result = await controller.refine_query(
            original_query="배포 방법 알려줘",
            clarification_question="어떤 종류의 배포를 원하시나요?",
            user_response=HITLResponse(custom_input="AWS ECS 배포"),
        )

        assert result != ""

    def test_process_user_response_selected_option(self, controller):
        """Test processing selected option response"""
        response = HITLResponse(selected_option="Option A")
        result = controller.process_user_response(response)
        assert result == "Option A"

    def test_process_user_response_custom_input(self, controller):
        """Test processing custom input response"""
        response = HITLResponse(custom_input="My custom input")
        result = controller.process_user_response(response)
        assert result == "My custom input"

    def test_process_user_response_empty(self, controller):
        """Test processing empty response"""
        response = HITLResponse()
        result = controller.process_user_response(response)
        assert result == ""

    def test_get_default_options_multiple_interpretation(self, controller):
        """Test default options for multiple interpretation"""
        options = controller._get_default_options(AmbiguityType.MULTIPLE_INTERPRETATION)
        assert len(options) >= 2

    def test_get_default_options_missing_context(self, controller):
        """Test default options for missing context"""
        options = controller._get_default_options(AmbiguityType.MISSING_CONTEXT)
        assert len(options) >= 2

    def test_get_default_options_vague_term(self, controller):
        """Test default options for vague term"""
        options = controller._get_default_options(AmbiguityType.VAGUE_TERM)
        assert len(options) >= 2

    def test_get_default_clarification(self, controller):
        """Test default clarification generation"""
        result = controller._get_default_clarification(
            query="뭔가 해줘",
            ambiguity_type=AmbiguityType.VAGUE_TERM,
        )

        assert isinstance(result, ClarificationOutput)
        assert result.clarification_question != ""
        assert len(result.options) >= 2
