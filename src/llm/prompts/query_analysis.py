"""Query Analysis Prompt Template (Prompt #1)"""

QUERY_ANALYSIS_PROMPT = """Analyze the following user query and provide a structured analysis.

## Query
{query}

## Analysis Requirements

1. **refined_query**: Improve the query for better search results. Keep the original intent.

2. **complexity**: Determine if the query is "simple" or "complex"
   - simple: Single topic, straightforward question
   - complex: Multiple parts, requires decomposition, comparative analysis

3. **clarity_confidence**: Score 0.0-1.0 indicating how clear the query is
   - 1.0: Perfectly clear, specific, actionable
   - 0.7-0.9: Mostly clear, minor improvements possible
   - 0.5-0.7: Somewhat unclear, may need clarification
   - Below 0.5: Unclear, needs clarification

4. **is_ambiguous**: true if the query has multiple interpretations or unclear terms

5. **ambiguity_type**: If ambiguous, specify the type:
   - "multiple_interpretation": Query could mean different things
   - "missing_context": Lacks necessary context (e.g., "설정을 변경하려면?" - which setting?)
   - "vague_term": Contains vague terms (e.g., "그거", "그것", "저것")

6. **detected_domains**: List relevant technical domains:
   - development, operations, security, infrastructure, api
   - database, frontend, backend, devops, general

## Response Format
Return a JSON object with all the above fields.
"""
