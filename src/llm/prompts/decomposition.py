"""Query decomposition prompt template (Prompt #3)"""

QUERY_DECOMPOSITION_PROMPT = """You are a query decomposition specialist for a RAG chatbot.
Complex questions often need to be broken down into simpler sub-questions for effective retrieval.

## User's Question
{query}

## Query Analysis
- Complexity: {complexity}
- Detected Domains: {detected_domains}

## Your Task
Decompose this complex question into 2-5 simpler sub-questions that:
1. Can each be answered independently
2. Together cover the full scope of the original question
3. Are specific enough for effective document retrieval

## Guidelines
1. Each sub-question should target a specific aspect or domain
2. Sub-questions should be self-contained (can be understood without context)
3. Order sub-questions logically (prerequisites first)
4. Identify which sub-questions can be searched in parallel
5. Provide a synthesis guide for combining answers

## Output Format (JSON)
{{
    "original_intent": "brief description of user's intent",
    "sub_questions": [
        {{
            "id": "q1",
            "question": "sub-question text",
            "target_domain": "relevant domain/topic",
            "dependencies": []
        }},
        {{
            "id": "q2",
            "question": "sub-question text",
            "target_domain": "relevant domain/topic",
            "dependencies": ["q1"]
        }}
    ],
    "parallel_groups": [
        ["q1", "q2"],
        ["q3"]
    ],
    "synthesis_guide": "How to combine answers into a coherent response"
}}

Decompose the question:"""


SUB_ANSWER_SYNTHESIS_PROMPT = """You are a response synthesizer.
Combine multiple sub-answers into a coherent, comprehensive response.

## Original Question
{original_query}

## Sub-Questions and Answers
{sub_answers}

## Synthesis Guide
{synthesis_guide}

## Your Task
1. Combine the sub-answers into a single coherent response
2. Maintain logical flow and structure
3. Remove redundancy while preserving all important information
4. Add transitions between sections as needed
5. Ensure the final answer fully addresses the original question

## Guidelines
- Use clear section headers if the answer is long
- Cite sources from sub-answers
- Flag any inconsistencies between sub-answers
- Keep the response in Korean

## Output Format (JSON)
{{
    "synthesized_response": "complete combined answer",
    "sources": ["source1", "source2"],
    "coverage_score": 0.0-1.0,
    "inconsistencies": ["any noted inconsistencies"]
}}

Synthesize the response:"""
