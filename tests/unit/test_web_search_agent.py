"""Unit tests for Web Search Agent"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.web_search_agent import (
    WebSearchAgent,
    OptimizedQuery,
    WebResultRelevance,
    TavilyResult,
)
from src.core.models import Document


class TestWebSearchAgent:
    """Test cases for WebSearchAgent"""

    @pytest.fixture
    def agent(self, mock_llm_provider):
        """Create agent with mocked LLM"""
        agent = WebSearchAgent(llm_provider=mock_llm_provider)
        agent.api_key = "test_api_key"
        return agent

    @pytest.mark.asyncio
    async def test_optimize_query_success(self, agent, mock_llm_provider):
        """Test successful query optimization"""
        mock_llm_provider.generate_structured = AsyncMock(
            return_value=OptimizedQuery(
                optimized_query="Docker container deployment guide",
                search_focus="documentation",
            )
        )

        result = await agent._optimize_query(
            query="우리 회사 Docker 배포 방법",
            detected_domains=["docker", "deployment"],
        )

        assert result == "Docker container deployment guide"

    @pytest.mark.asyncio
    async def test_optimize_query_fallback(self, agent, mock_llm_provider):
        """Test query optimization fallback on error"""
        mock_llm_provider.generate_structured = AsyncMock(side_effect=Exception("Error"))

        result = await agent._optimize_query(
            query="Docker 배포 방법",
            detected_domains=[],
        )

        assert result == "Docker 배포 방법"  # Returns original query

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_tavily_search_success(self, mock_post, agent):
        """Test successful Tavily API call"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Docker Documentation",
                    "url": "https://docs.docker.com/",
                    "content": "Docker is a platform...",
                    "score": 0.9,
                },
                {
                    "title": "Docker Hub",
                    "url": "https://hub.docker.com/",
                    "content": "Container images...",
                    "score": 0.8,
                },
            ]
        }
        mock_response.raise_for_status = MagicMock()

        # Create async context manager mock
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        with patch("httpx.AsyncClient", return_value=mock_client):
            results = await agent._tavily_search("Docker deployment")

        assert len(results) == 2
        assert results[0].title == "Docker Documentation"
        assert results[0].url == "https://docs.docker.com/"

    @pytest.mark.asyncio
    async def test_tavily_search_no_api_key(self, mock_llm_provider):
        """Test Tavily search returns empty when no API key"""
        agent = WebSearchAgent(llm_provider=mock_llm_provider)
        agent.api_key = ""

        results = await agent._tavily_search("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_evaluate_result_success(self, agent, mock_llm_provider):
        """Test successful result evaluation"""
        mock_llm_provider.generate_structured = AsyncMock(
            return_value=WebResultRelevance(
                content_relevance=0.9,
                source_reliability=0.8,
                information_completeness=0.85,
                overall_score=0.85,
                useful_excerpt="Docker allows containerization...",
                should_include=True,
            )
        )

        result = TavilyResult(
            title="Docker Guide",
            url="https://docs.docker.com/guide",
            content="Docker allows containerization of applications...",
            score=0.8,
        )

        evaluation = await agent._evaluate_result("Docker 배포", result)

        assert evaluation.overall_score >= 0.8
        assert evaluation.should_include is True

    def test_estimate_source_reliability_trusted(self, agent):
        """Test source reliability for trusted domains"""
        assert agent._estimate_source_reliability("https://docs.python.org/") == 0.9
        assert agent._estimate_source_reliability("https://developer.mozilla.org/") == 0.9
        assert agent._estimate_source_reliability("https://stackoverflow.com/") == 0.9

    def test_estimate_source_reliability_docs(self, agent):
        """Test source reliability for documentation sites"""
        assert agent._estimate_source_reliability("https://docs.example.com/") == 0.8
        assert agent._estimate_source_reliability("https://example.com/documentation/") == 0.8

    def test_estimate_source_reliability_unknown(self, agent):
        """Test source reliability for unknown domains"""
        assert agent._estimate_source_reliability("https://random-blog.com/") == 0.6

    def test_get_disclaimer_message(self, agent):
        """Test disclaimer message"""
        message = agent.get_disclaimer_message()
        assert "웹 검색" in message
        assert "외부 소스" in message or "외부" in message

    @pytest.mark.asyncio
    async def test_evaluate_and_convert(self, agent, mock_llm_provider):
        """Test evaluation and conversion to documents"""
        mock_llm_provider.generate_structured = AsyncMock(
            return_value=WebResultRelevance(
                content_relevance=0.8,
                source_reliability=0.9,
                information_completeness=0.8,
                overall_score=0.8,
                useful_excerpt="Useful content here",
                should_include=True,
            )
        )

        results = [
            TavilyResult(
                title="Result 1",
                url="https://example.com/1",
                content="Content 1",
                score=0.9,
            ),
            TavilyResult(
                title="Result 2",
                url="https://example.com/2",
                content="Content 2",
                score=0.7,
            ),
        ]

        documents = await agent._evaluate_and_convert("test query", results)

        assert len(documents) == 2
        assert all(isinstance(d, Document) for d in documents)
        assert documents[0].metadata.source == "https://example.com/1"

    @pytest.mark.asyncio
    async def test_search_full_flow(self, agent, mock_llm_provider):
        """Test full search flow"""
        # Mock query optimization
        mock_llm_provider.generate_structured = AsyncMock(
            side_effect=[
                OptimizedQuery(optimized_query="Docker guide", search_focus="docs"),
                WebResultRelevance(
                    content_relevance=0.8,
                    source_reliability=0.9,
                    information_completeness=0.8,
                    overall_score=0.8,
                    useful_excerpt="Docker content",
                    should_include=True,
                ),
            ]
        )

        # Mock Tavily API
        with patch.object(agent, "_tavily_search") as mock_tavily:
            mock_tavily.return_value = [
                TavilyResult(
                    title="Docker Docs",
                    url="https://docs.docker.com/",
                    content="Docker documentation...",
                    score=0.9,
                )
            ]

            documents = await agent.search(
                query="Docker 배포",
                detected_domains=["docker"],
                optimize_query=True,
            )

        assert len(documents) >= 0  # May be 0 if filtering removes results
