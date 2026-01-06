"""Response Generation Prompt Template (Prompt #6)"""

RESPONSE_GENERATION_PROMPT = """Based on the provided documents, answer the user's question.

## User Question
{query}

## Retrieved Documents
{context}
{web_context}

## Instructions

1. **Answer the question** based ONLY on the information in the provided documents
2. **Cite your sources** using [1], [2], etc. format referring to document numbers
3. **Be concise** but comprehensive
4. **Use Korean** for your response
5. **Do not hallucinate** - only include information from the documents
6. If the documents don't contain enough information to answer:
   - Set has_sufficient_info to false
   - Explain what information is missing

## Response Format
Return a JSON object with:
- response: Your answer in Korean with source citations
- sources: List of source file paths or URLs used
- has_sufficient_info: Boolean indicating if documents contained sufficient information

## Example Response
{{
  "response": "Docker를 배포하려면 다음 단계를 따르세요: 1. Dockerfile을 작성합니다 [1]. 2. 이미지를 빌드합니다 [1]. 3. 컨테이너를 실행합니다 [2].",
  "sources": ["deployment.md", "docker-guide.md"],
  "has_sufficient_info": true
}}
"""
