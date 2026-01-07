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
5. **Use Markdown formatting** for better readability:
   - Use numbered lists (1. 2. 3.) for sequential steps
   - Use bullet points (- or *) for non-sequential items
   - Use **bold** for important terms
   - Use `code` for technical terms, file names, or commands
   - Use headers (### ) for sections if the answer is long
6. **Do not hallucinate** - only include information from the documents
7. If the documents don't contain enough information to answer:
   - Set has_sufficient_info to false
   - Explain what information is missing

## Response Format
Return a JSON object with:
- response: Your answer in Korean with Markdown formatting and source citations
- sources: List of source file paths or URLs used
- has_sufficient_info: Boolean indicating if documents contained sufficient information

## Example Response
{{
  "response": "### Docker 배포 방법\\n\\nDocker를 배포하려면 다음 단계를 따르세요:\\n\\n1. **Dockerfile 작성** - 애플리케이션 설정 정의 [1]\\n2. **이미지 빌드** - `docker build -t myapp .` 명령 실행 [1]\\n3. **컨테이너 실행** - `docker run myapp` 명령으로 시작 [2]",
  "sources": ["deployment.md", "docker-guide.md"],
  "has_sufficient_info": true
}}
"""
