"""Query Processor for analyzing user queries"""

from typing import Optional

from src.core.models import (
    Complexity,
    AmbiguityType,
    QueryAnalysisOutput,
)
from src.core.exceptions import ValidationException
from src.llm import LLMProvider, OpenAIProvider
from src.llm.prompts.query_analysis import QUERY_ANALYSIS_PROMPT


class QueryProcessor:
    """Query analyzer for determining complexity, clarity, and ambiguity"""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider or OpenAIProvider()

    async def analyze(self, query: str) -> QueryAnalysisOutput:
        """Analyze a user query"""
        # Validate input
        if not query or not query.strip():
            raise ValidationException("Query cannot be empty")

        # Truncate very long queries
        query = query[:2000] if len(query) > 2000 else query

        # Generate analysis using LLM
        prompt = QUERY_ANALYSIS_PROMPT.format(query=query)

        result = await self.llm_provider.generate_structured(
            prompt=prompt,
            response_model=QueryAnalysisOutput,
            system_prompt="You are a query analysis expert. Analyze the given query and return a structured analysis.",
        )

        return result

    def is_simple_query(self, analysis: QueryAnalysisOutput) -> bool:
        """Check if query is simple"""
        return analysis.complexity == Complexity.SIMPLE

    def needs_clarification(self, analysis: QueryAnalysisOutput) -> bool:
        """Check if query needs HITL clarification"""
        return analysis.is_ambiguous and analysis.clarity_confidence < 0.7
