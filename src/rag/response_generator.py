"""Response Generator for creating answers from retrieved documents"""

from typing import List, Optional

from src.core.models import Document, ResponseOutput
from src.llm import LLMProvider, OpenAIProvider
from src.llm.prompts.response import RESPONSE_GENERATION_PROMPT


class ResponseGenerator:
    """Generate responses from retrieved documents"""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider or OpenAIProvider()

    def _format_documents_context(self, documents: List[Document]) -> str:
        """Format documents for context prompt"""
        if not documents:
            return "검색된 문서가 없습니다."

        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.source if doc.metadata else "unknown"
            title = doc.metadata.title if doc.metadata and doc.metadata.title else ""

            header = f"[문서 {i}] 출처: {source}"
            if title:
                header += f" - {title}"

            context_parts.append(f"{header}\n{doc.content}")

        return "\n\n---\n\n".join(context_parts)

    def _extract_sources(self, documents: List[Document]) -> List[str]:
        """Extract source references from documents"""
        sources = []
        seen = set()

        for doc in documents:
            if doc.metadata and doc.metadata.source:
                source = doc.metadata.source
                if source not in seen:
                    seen.add(source)
                    sources.append(source)

        return sources

    async def generate(
        self,
        query: str,
        documents: List[Document],
        web_results: Optional[List[Document]] = None,
    ) -> ResponseOutput:
        """Generate response from documents"""
        # Format context from documents
        context = self._format_documents_context(documents)

        # Add web results if available
        web_context = ""
        if web_results:
            web_context = "\n\n## 웹 검색 결과\n" + self._format_documents_context(
                web_results
            )

        # Build prompt
        prompt = RESPONSE_GENERATION_PROMPT.format(
            query=query,
            context=context,
            web_context=web_context,
        )

        # Generate structured response
        result = await self.llm_provider.generate_structured(
            prompt=prompt,
            response_model=ResponseOutput,
            system_prompt="You are a helpful assistant that answers questions based on the provided documents. Always cite your sources.",
        )

        # Ensure sources are populated
        if not result.sources and documents:
            result.sources = self._extract_sources(documents)

        return result

    def evaluate_response_quality(
        self,
        response: ResponseOutput,
        documents: List[Document],
    ) -> float:
        """Evaluate quality of generated response (0.0-1.0)"""
        quality_score = 0.0

        # Check if response has content
        if response.response and len(response.response) > 50:
            quality_score += 0.3

        # Check if sources are cited
        if response.sources and len(response.sources) > 0:
            quality_score += 0.3

        # Check if response indicates sufficient info
        if response.has_sufficient_info:
            quality_score += 0.4

        return min(quality_score, 1.0)
