"""Response Quality Evaluator for assessing answer quality"""

from typing import List, Optional

from pydantic import BaseModel, Field

from src.llm import LLMProvider, OpenAIProvider
from src.llm.prompts.quality import QUALITY_EVALUATION_PROMPT


class QualityEvaluationOutput(BaseModel):
    """Quality evaluation output model"""

    completeness: float = Field(ge=0.0, le=1.0)
    accuracy: float = Field(ge=0.0, le=1.0)
    clarity: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_disclaimer: bool


class QualityEvaluator:
    """Evaluator for response quality assessment"""

    # Thresholds for disclaimer decision
    CONFIDENCE_THRESHOLD = 0.8
    COMPLETENESS_THRESHOLD = 0.6
    ACCURACY_THRESHOLD = 0.7

    # Weights for confidence calculation
    COMPLETENESS_WEIGHT = 0.4
    ACCURACY_WEIGHT = 0.4
    CLARITY_WEIGHT = 0.2

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider or OpenAIProvider()

    def _calculate_confidence(
        self,
        completeness: float,
        accuracy: float,
        clarity: float,
    ) -> float:
        """Calculate weighted confidence score"""
        return (
            completeness * self.COMPLETENESS_WEIGHT
            + accuracy * self.ACCURACY_WEIGHT
            + clarity * self.CLARITY_WEIGHT
        )

    def _should_show_disclaimer(
        self,
        confidence: float,
        completeness: float,
        accuracy: float,
    ) -> bool:
        """Determine if disclaimer should be shown"""
        return (
            confidence < self.CONFIDENCE_THRESHOLD
            or completeness < self.COMPLETENESS_THRESHOLD
            or accuracy < self.ACCURACY_THRESHOLD
        )

    async def evaluate(
        self,
        query: str,
        response: str,
        sources: List[str],
    ) -> QualityEvaluationOutput:
        """Evaluate quality of generated response"""
        # Handle empty response
        if not response or not response.strip():
            return QualityEvaluationOutput(
                completeness=0.0,
                accuracy=0.0,
                clarity=0.0,
                confidence=0.0,
                needs_disclaimer=True,
            )

        # Format sources
        sources_text = "\n".join(f"- {s}" for s in sources) if sources else "No sources provided"

        # Generate evaluation
        prompt = QUALITY_EVALUATION_PROMPT.format(
            query=query,
            response=response,
            sources=sources_text,
        )

        result = await self.llm_provider.generate_structured(
            prompt=prompt,
            response_model=QualityEvaluationOutput,
            system_prompt="You are an expert at evaluating response quality. Be objective and precise.",
        )

        # Validate and potentially override confidence calculation
        calculated_confidence = self._calculate_confidence(
            result.completeness,
            result.accuracy,
            result.clarity,
        )

        # Use calculated confidence if significantly different
        if abs(result.confidence - calculated_confidence) > 0.1:
            result.confidence = calculated_confidence

        # Override disclaimer decision based on thresholds
        result.needs_disclaimer = self._should_show_disclaimer(
            result.confidence,
            result.completeness,
            result.accuracy,
        )

        return result

    def quick_evaluate(
        self,
        response: str,
        sources: List[str],
        avg_relevance: float,
    ) -> QualityEvaluationOutput:
        """Quick heuristic-based evaluation without LLM"""
        # Base scores
        completeness = 0.5
        accuracy = 0.5
        clarity = 0.5

        # Adjust based on response length
        response_len = len(response)
        if response_len > 500:
            completeness += 0.2
            clarity += 0.1
        elif response_len > 200:
            completeness += 0.1
        elif response_len < 50:
            completeness -= 0.2
            clarity -= 0.1

        # Adjust based on sources
        if sources and len(sources) >= 2:
            accuracy += 0.2
        elif sources:
            accuracy += 0.1

        # Adjust based on relevance
        if avg_relevance >= 0.8:
            accuracy += 0.2
            completeness += 0.1
        elif avg_relevance >= 0.6:
            accuracy += 0.1

        # Clamp values
        completeness = max(0.0, min(1.0, completeness))
        accuracy = max(0.0, min(1.0, accuracy))
        clarity = max(0.0, min(1.0, clarity))

        confidence = self._calculate_confidence(completeness, accuracy, clarity)
        needs_disclaimer = self._should_show_disclaimer(confidence, completeness, accuracy)

        return QualityEvaluationOutput(
            completeness=completeness,
            accuracy=accuracy,
            clarity=clarity,
            confidence=confidence,
            needs_disclaimer=needs_disclaimer,
        )
