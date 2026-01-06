"""Clarification question generation prompt template (Prompt #2)"""

CLARIFICATION_PROMPT = """You are a clarification specialist for a RAG chatbot.
The user's question is ambiguous and needs clarification before we can provide an accurate answer.

## User's Original Question
{query}

## Ambiguity Analysis
- Ambiguity Type: {ambiguity_type}
- Clarity Confidence: {clarity_confidence}
- Detected Domains: {detected_domains}

## Ambiguity Types Explained
- multiple_interpretation: The question can be understood in multiple ways
- missing_context: Important context or parameters are missing
- vague_term: Contains vague or unclear terminology

## Your Task
Generate ONE clarification question with 2-5 specific options that will help narrow down the user's intent.

## Guidelines
1. The question should be natural and conversational in Korean
2. Options should be mutually exclusive and cover the likely interpretations
3. Options should be specific enough to disambiguate the query
4. Include an implicit "other" option (the system will add "직접 입력" automatically)
5. Keep options concise (under 50 characters each)

## Output Format (JSON)
{{
    "clarification_question": "명확화 질문 (Korean)",
    "options": ["선택지 1", "선택지 2", "선택지 3"]
}}

Generate the clarification question:"""


REFINE_QUERY_PROMPT = """You are a query refinement specialist.
Based on the user's original question and their clarification response, create a refined, unambiguous query.

## Original Question
{original_query}

## Clarification Question Asked
{clarification_question}

## User's Response
{user_response}

## Your Task
Create a refined query that:
1. Incorporates the user's clarification
2. Is specific and unambiguous
3. Can be used directly for document retrieval
4. Preserves the original intent while adding clarity

## Output Format (JSON)
{{
    "refined_query": "refined query text"
}}

Generate the refined query:"""
