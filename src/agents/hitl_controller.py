"""Human-in-the-Loop Controller for clarification dialogues"""

import json
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from src.config import get_settings
from src.core.models import AmbiguityType, ClarificationOutput, HITLResponse
from src.llm import get_llm_provider
from src.llm.prompts.clarification import CLARIFICATION_PROMPT, REFINE_QUERY_PROMPT


class ClarificationResult(BaseModel):
    """Result of clarification question generation"""
    clarification_question: str
    options: List[str] = Field(min_length=2, max_length=5)


class RefinedQueryResult(BaseModel):
    """Result of query refinement"""
    refined_query: str


class HITLController:
    """Controller for Human-in-the-Loop clarification dialogues"""

    def __init__(self, llm_provider=None):
        self.llm = llm_provider or get_llm_provider()
        self.settings = get_settings()
        self.max_interactions = self.settings.max_hitl_interactions

    def should_clarify(
        self,
        clarity_confidence: float,
        is_ambiguous: bool,
        interaction_count: int,
    ) -> bool:
        """Determine if clarification is needed

        Args:
            clarity_confidence: Confidence score from query analysis (0.0-1.0)
            is_ambiguous: Whether query was flagged as ambiguous
            interaction_count: Number of HITL interactions so far

        Returns:
            True if clarification should be triggered
        """
        # HITL 비활성화 - 항상 False 반환
        return False

        # # Don't exceed max interactions
        # if interaction_count >= self.max_interactions:
        #     return False

        # # Trigger if ambiguous or low clarity
        # if is_ambiguous:
        #     return True

        # if clarity_confidence < 0.8:
        #     return True

        # return False

    async def generate_clarification(
        self,
        query: str,
        ambiguity_type: Optional[AmbiguityType],
        clarity_confidence: float,
        detected_domains: List[str],
    ) -> ClarificationOutput:
        """Generate clarification question with options

        Args:
            query: The original user query
            ambiguity_type: Type of ambiguity detected
            clarity_confidence: Confidence score from analysis
            detected_domains: Domains detected in the query

        Returns:
            ClarificationOutput with question and options
        """
        prompt = CLARIFICATION_PROMPT.format(
            query=query,
            ambiguity_type=ambiguity_type.value if ambiguity_type else "general",
            clarity_confidence=clarity_confidence,
            detected_domains=", ".join(detected_domains) if detected_domains else "없음",
        )

        try:
            result = await self.llm.generate_structured(
                prompt=prompt,
                output_schema=ClarificationResult,
            )

            # Ensure we have valid options
            options = result.options if result.options else self._get_default_options(ambiguity_type)

            # Limit to max 5 options
            options = options[:5]

            return ClarificationOutput(
                clarification_question=result.clarification_question,
                options=options,
            )
        except Exception as e:
            # Fallback to default clarification
            return self._get_default_clarification(query, ambiguity_type)

    async def refine_query(
        self,
        original_query: str,
        clarification_question: str,
        user_response: HITLResponse,
    ) -> str:
        """Refine the query based on user's clarification response

        Args:
            original_query: The original user query
            clarification_question: The clarification question asked
            user_response: User's response (selected option or custom input)

        Returns:
            Refined query string
        """
        # Get the actual response text
        response_text = user_response.custom_input or user_response.selected_option or ""

        prompt = REFINE_QUERY_PROMPT.format(
            original_query=original_query,
            clarification_question=clarification_question,
            user_response=response_text,
        )

        try:
            result = await self.llm.generate_structured(
                prompt=prompt,
                output_schema=RefinedQueryResult,
            )
            return result.refined_query
        except Exception:
            # Simple fallback: append clarification to original query
            return f"{original_query} ({response_text})"

    def process_user_response(self, response: HITLResponse) -> str:
        """Process user's HITL response into a string

        Args:
            response: User's HITLResponse

        Returns:
            Processed response string
        """
        if response.custom_input:
            return response.custom_input.strip()
        if response.selected_option:
            return response.selected_option.strip()
        return ""

    def _get_default_options(self, ambiguity_type: Optional[AmbiguityType]) -> List[str]:
        """Get default options based on ambiguity type"""
        if ambiguity_type == AmbiguityType.MULTIPLE_INTERPRETATION:
            return [
                "개념 설명이 필요해요",
                "사용 방법을 알고 싶어요",
                "문제 해결이 필요해요",
            ]
        elif ambiguity_type == AmbiguityType.MISSING_CONTEXT:
            return [
                "설정 관련",
                "개발 관련",
                "배포 관련",
            ]
        elif ambiguity_type == AmbiguityType.VAGUE_TERM:
            return [
                "기본 개념",
                "고급 기능",
                "실제 예시",
            ]
        else:
            return [
                "자세한 설명",
                "간단한 요약",
                "예시 코드",
            ]

    def _get_default_clarification(
        self,
        query: str,
        ambiguity_type: Optional[AmbiguityType],
    ) -> ClarificationOutput:
        """Get default clarification when LLM fails"""
        question_templates = {
            AmbiguityType.MULTIPLE_INTERPRETATION: "질문을 어떤 측면에서 답변해 드릴까요?",
            AmbiguityType.MISSING_CONTEXT: "추가 정보가 필요합니다. 어떤 상황인가요?",
            AmbiguityType.VAGUE_TERM: "좀 더 구체적으로 알려주시겠어요?",
        }

        question = question_templates.get(
            ambiguity_type,
            "질문을 좀 더 구체적으로 알려주시겠어요?",
        )

        return ClarificationOutput(
            clarification_question=question,
            options=self._get_default_options(ambiguity_type),
        )


# Factory function
def get_hitl_controller() -> HITLController:
    """Get HITL controller instance"""
    return HITLController()
