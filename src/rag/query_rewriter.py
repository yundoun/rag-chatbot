"""Query Rewriter for failed search correction"""

from typing import List, Optional

from pydantic import BaseModel

from src.core.models import RewriteStrategy
from src.llm import LLMProvider, OpenAIProvider
from src.llm.prompts.rewrite import QUERY_REWRITE_PROMPT, STRATEGY_SELECTION_PROMPT


class QueryRewriteOutput(BaseModel):
    """Query rewrite output model"""

    strategy: str
    rewritten_query: str
    changes_made: str
    expected_improvement: str


class StrategySelectionOutput(BaseModel):
    """Strategy selection output model"""

    selected_strategy: str
    reason: str


class QueryRewriter:
    """Query rewriter for improving search results"""

    # Strategy order for retries
    FIRST_RETRY_STRATEGIES = [
        RewriteStrategy.SYNONYM_EXPANSION,
        RewriteStrategy.CONTEXT_ADDITION,
    ]
    SECOND_RETRY_STRATEGIES = [
        RewriteStrategy.GENERALIZATION,
    ]

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider or OpenAIProvider()

    def select_strategy(
        self,
        retry_count: int,
        previous_strategies: List[str],
    ) -> RewriteStrategy:
        """Select appropriate rewrite strategy based on retry count"""
        # Get available strategies based on retry count
        if retry_count == 0:
            candidates = self.FIRST_RETRY_STRATEGIES
        else:
            candidates = self.SECOND_RETRY_STRATEGIES

        # Filter out already used strategies
        available = [s for s in candidates if s.value not in previous_strategies]

        # If all strategies in current tier used, try next tier
        if not available:
            all_strategies = list(RewriteStrategy)
            available = [s for s in all_strategies if s.value not in previous_strategies]

        # Return first available or default
        return available[0] if available else RewriteStrategy.GENERALIZATION

    async def select_strategy_llm(
        self,
        query: str,
        retry_count: int,
        previous_strategies: List[str],
        failure_reason: str = "Low relevance results",
    ) -> RewriteStrategy:
        """Use LLM to select the best strategy"""
        prompt = STRATEGY_SELECTION_PROMPT.format(
            query=query,
            retry_count=retry_count,
            previous_strategies=", ".join(previous_strategies) if previous_strategies else "None",
            failure_reason=failure_reason,
        )

        result = await self.llm_provider.generate_structured(
            prompt=prompt,
            response_model=StrategySelectionOutput,
            system_prompt="You are an expert at query optimization.",
        )

        # Map string to enum
        try:
            return RewriteStrategy(result.selected_strategy)
        except ValueError:
            # Fallback to rule-based selection
            return self.select_strategy(retry_count, previous_strategies)

    async def rewrite(
        self,
        query: str,
        strategy: RewriteStrategy,
        previous_queries: List[str],
    ) -> QueryRewriteOutput:
        """Rewrite query using specified strategy"""
        prompt = QUERY_REWRITE_PROMPT.format(
            query=query,
            strategy=strategy.value,
            previous_queries="\n".join(f"- {q}" for q in previous_queries) if previous_queries else "None",
        )

        result = await self.llm_provider.generate_structured(
            prompt=prompt,
            response_model=QueryRewriteOutput,
            system_prompt="You are an expert at reformulating search queries for better results.",
        )

        return result

    async def rewrite_auto(
        self,
        query: str,
        retry_count: int,
        previous_queries: List[str],
        previous_strategies: List[str],
    ) -> tuple[str, RewriteStrategy]:
        """Automatically select strategy and rewrite query"""
        # Select strategy
        strategy = self.select_strategy(retry_count, previous_strategies)

        # Rewrite query
        result = await self.rewrite(query, strategy, previous_queries)

        return result.rewritten_query, strategy
