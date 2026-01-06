"""Query Rewrite Prompt Template (Prompt #5)"""

QUERY_REWRITE_PROMPT = """The original search query did not return sufficiently relevant results.
Rewrite the query using the specified strategy to improve search results.

## Original Query
{query}

## Rewrite Strategy
{strategy}

## Strategy Descriptions
- **synonym_expansion**: Add synonyms and related terms to broaden the search
- **context_addition**: Add contextual keywords that clarify the query intent
- **generalization**: Make the query more general/broader if it's too specific
- **specification**: Make the query more specific if it's too vague

## Previous Attempts (avoid duplicating these)
{previous_queries}

## Instructions
1. Apply the {strategy} strategy to rewrite the query
2. Keep the original intent intact
3. Do NOT create a query similar to previous attempts
4. The rewritten query should be in the same language as the original

## Response Format
Return a JSON object with:
- strategy: The strategy used (string)
- rewritten_query: The new query (string)
- changes_made: Brief description of what was changed (string)
- expected_improvement: Why this should improve results (string)
"""

STRATEGY_SELECTION_PROMPT = """Based on the search results and query analysis, select the best rewrite strategy.

## Original Query
{query}

## Retry Count
{retry_count} (0 = first retry, 1 = second retry)

## Previous Strategies Used
{previous_strategies}

## Search Failure Reason
{failure_reason}

## Available Strategies
1. synonym_expansion - Good for: technical jargon, specific terms
2. context_addition - Good for: ambiguous queries, missing context
3. generalization - Good for: too specific queries with no matches
4. specification - Good for: too broad queries with irrelevant matches

## Instructions
- For first retry (count=0): prefer synonym_expansion or context_addition
- For second retry (count=1): prefer generalization
- Avoid strategies already used

## Response Format
Return a JSON object with:
- selected_strategy: One of the available strategies
- reason: Why this strategy was selected
"""
