"""Web Search Agent using Tavily API"""

import asyncio
from typing import List, Optional

import httpx
from pydantic import BaseModel, Field

from src.config import get_settings
from src.core.models import Document, DocumentMetadata, RetrievalSource
from src.llm import get_llm_provider
from src.llm.prompts.web_integration import (
    WEB_QUERY_OPTIMIZATION_PROMPT,
    WEB_RESULT_RELEVANCE_PROMPT,
)


class OptimizedQuery(BaseModel):
    """Optimized web search query"""
    optimized_query: str
    search_focus: str = "general"


class WebResultRelevance(BaseModel):
    """Web result relevance evaluation"""
    content_relevance: float = Field(ge=0.0, le=1.0)
    source_reliability: float = Field(ge=0.0, le=1.0)
    information_completeness: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)
    useful_excerpt: str = ""
    should_include: bool = True


class TavilyResult(BaseModel):
    """Tavily search result"""
    title: str
    url: str
    content: str
    score: float = 0.0


class WebSearchAgent:
    """Agent for web search fallback using Tavily API"""

    TAVILY_API_URL = "https://api.tavily.com/search"

    def __init__(self, llm_provider=None):
        self.settings = get_settings()
        self.llm = llm_provider or get_llm_provider()
        self.api_key = self.settings.tavily_api_key
        self.max_results = self.settings.tavily_max_results

    async def search(
        self,
        query: str,
        detected_domains: Optional[List[str]] = None,
        optimize_query: bool = True,
    ) -> List[Document]:
        """Perform web search and return results as Documents

        Args:
            query: The search query
            detected_domains: Domains from query analysis
            optimize_query: Whether to optimize query for web search

        Returns:
            List of Document objects from web search
        """
        # Optimize query for web search if requested
        search_query = query
        if optimize_query:
            search_query = await self._optimize_query(query, detected_domains)

        # Perform Tavily search
        raw_results = await self._tavily_search(search_query)

        if not raw_results:
            return []

        # Evaluate relevance of each result
        documents = await self._evaluate_and_convert(query, raw_results)

        return documents

    async def _optimize_query(
        self,
        query: str,
        detected_domains: Optional[List[str]] = None,
    ) -> str:
        """Optimize query for web search"""
        prompt = WEB_QUERY_OPTIMIZATION_PROMPT.format(
            query=query,
            detected_domains=", ".join(detected_domains) if detected_domains else "없음",
        )

        try:
            result = await self.llm.generate_structured(
                prompt=prompt,
                output_schema=OptimizedQuery,
            )
            return result.optimized_query
        except Exception:
            # Fallback: use original query
            return query

    async def _tavily_search(self, query: str) -> List[TavilyResult]:
        """Call Tavily API for web search"""
        if not self.api_key:
            return []

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": False,
            "include_raw_content": False,
            "max_results": self.max_results,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.TAVILY_API_URL, json=payload)
                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("results", []):
                    results.append(TavilyResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        content=item.get("content", ""),
                        score=item.get("score", 0.0),
                    ))
                return results
        except Exception as e:
            # Log error but don't fail
            print(f"Tavily search error: {e}")
            return []

    async def _evaluate_and_convert(
        self,
        original_query: str,
        results: List[TavilyResult],
    ) -> List[Document]:
        """Evaluate relevance and convert to Documents"""
        documents = []

        # Evaluate results in parallel
        evaluation_tasks = [
            self._evaluate_result(original_query, result)
            for result in results
        ]

        evaluations = await asyncio.gather(*evaluation_tasks, return_exceptions=True)

        for result, evaluation in zip(results, evaluations):
            if isinstance(evaluation, Exception):
                # If evaluation failed, include with default score
                evaluation = WebResultRelevance(
                    content_relevance=0.5,
                    source_reliability=0.5,
                    information_completeness=0.5,
                    overall_score=0.5,
                    useful_excerpt=result.content[:500],
                    should_include=True,
                )

            if evaluation.should_include and evaluation.overall_score >= 0.3:
                doc = Document(
                    content=evaluation.useful_excerpt or result.content,
                    metadata=DocumentMetadata(
                        source=result.url,
                        title=result.title,
                        section="web_search",
                    ),
                    embedding_score=result.score,
                    llm_relevance_score=evaluation.overall_score,
                    combined_score=evaluation.overall_score,
                )
                documents.append(doc)

        # Sort by relevance score
        documents.sort(key=lambda d: d.combined_score or 0, reverse=True)

        return documents

    async def _evaluate_result(
        self,
        query: str,
        result: TavilyResult,
    ) -> WebResultRelevance:
        """Evaluate a single web result"""
        prompt = WEB_RESULT_RELEVANCE_PROMPT.format(
            query=query,
            title=result.title,
            url=result.url,
            content=result.content[:2000],  # Limit content length
        )

        try:
            return await self.llm.generate_structured(
                prompt=prompt,
                output_schema=WebResultRelevance,
            )
        except Exception:
            # Default evaluation
            return WebResultRelevance(
                content_relevance=0.5,
                source_reliability=self._estimate_source_reliability(result.url),
                information_completeness=0.5,
                overall_score=0.5,
                useful_excerpt=result.content[:500],
                should_include=True,
            )

    def _estimate_source_reliability(self, url: str) -> float:
        """Estimate source reliability based on URL"""
        trusted_domains = [
            "docs.python.org",
            "developer.mozilla.org",
            "docs.microsoft.com",
            "cloud.google.com",
            "aws.amazon.com",
            "kubernetes.io",
            "docker.com",
            "github.com",
            "stackoverflow.com",
            "medium.com",
        ]

        url_lower = url.lower()
        for domain in trusted_domains:
            if domain in url_lower:
                return 0.9

        # Check for official documentation patterns
        if any(pattern in url_lower for pattern in ["docs.", "documentation", "wiki"]):
            return 0.8

        return 0.6

    def get_disclaimer_message(self) -> str:
        """Get disclaimer message for web search results"""
        return (
            "⚠️ 이 답변은 웹 검색 결과를 포함하고 있습니다. "
            "내부 문서에서 충분한 정보를 찾지 못해 외부 소스를 참조했습니다. "
            "정확성을 위해 공식 문서를 확인해 주세요."
        )


# Factory function
def get_web_search_agent() -> WebSearchAgent:
    """Get web search agent instance"""
    return WebSearchAgent()
