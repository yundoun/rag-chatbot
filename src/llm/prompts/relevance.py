"""Relevance Evaluation Prompt Template (Prompt #4)"""

RELEVANCE_EVALUATION_PROMPT = """Evaluate the relevance of the following document to the user's query.

## User Query
{query}

## Document to Evaluate
Source: {source}
Content:
{content}

## Evaluation Criteria

1. **relevance_score** (0.0 - 1.0):
   - 1.0: Perfectly answers the query, contains all needed information
   - 0.8-0.9: Highly relevant, addresses main aspects of the query
   - 0.6-0.8: Moderately relevant, partially addresses the query
   - 0.4-0.6: Somewhat relevant, tangentially related
   - 0.2-0.4: Low relevance, only mentions related keywords
   - 0.0-0.2: Not relevant, does not address the query

2. **relevance_level**: Based on score
   - "high": score >= 0.8
   - "medium": 0.5 <= score < 0.8
   - "low": score < 0.5

3. **reason**: Brief explanation (1-2 sentences) of why this score was assigned

4. **useful_parts**: List of specific text snippets from the document that are useful for answering the query (max 3)

## Response Format
Return a JSON object with:
- relevance_score: float (0.0-1.0)
- relevance_level: "high" | "medium" | "low"
- reason: string
- useful_parts: list of strings
"""

BATCH_RELEVANCE_EVALUATION_PROMPT = """Evaluate the relevance of multiple documents to the user's query.

## User Query
{query}

## Documents to Evaluate
{documents}

## Instructions
For each document, provide:
1. relevance_score (0.0-1.0)
2. relevance_level ("high", "medium", "low")
3. reason (brief explanation)
4. useful_parts (max 3 key snippets)

## Response Format
Return a JSON object with a "evaluations" array containing evaluation for each document in order.
"""
