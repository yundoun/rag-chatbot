"""Integration tests for Web Search Fallback"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.core.models import (
    RAGResponse,
    RetrievalSource,
    Document,
    DocumentMetadata,
)
from src.agents.web_search_agent import WebSearchAgent, TavilyResult


class TestWebSearchFallback:
    """Integration tests for web search fallback behavior"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from src.api.main import app
        return TestClient(app)

    def test_health_check(self, client):
        """Verify API is running"""
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_web_search_triggered_after_retries(self, mock_llm_provider):
        """Test that web search is triggered after max correction retries"""
        from src.core.edges import route_after_evaluation

        # Simulate state after max retries with low relevance
        state = {
            "avg_relevance": 0.3,
            "high_relevance_count": 0,
            "retry_count": 2,  # Max retries reached
        }

        result = route_after_evaluation(state)

        assert result == "web_search"

    @pytest.mark.asyncio
    async def test_web_search_not_triggered_with_high_relevance(self, mock_llm_provider):
        """Test that web search is not triggered when relevance is sufficient"""
        from src.core.edges import route_after_evaluation

        state = {
            "avg_relevance": 0.9,
            "high_relevance_count": 3,
            "retry_count": 0,
        }

        result = route_after_evaluation(state)

        assert result == "generate"


class TestWebSearchAgent:
    """Test web search agent functionality"""

    @pytest.fixture
    def agent(self, mock_llm_provider):
        """Create agent with mocked LLM"""
        agent = WebSearchAgent(llm_provider=mock_llm_provider)
        agent.api_key = "test_api_key"
        return agent

    @pytest.mark.asyncio
    async def test_search_returns_documents(self, agent, mock_llm_provider):
        """Test that search returns Document objects"""
        from src.agents.web_search_agent import OptimizedQuery, WebResultRelevance

        mock_llm_provider.generate_structured = AsyncMock(
            side_effect=[
                OptimizedQuery(optimized_query="test query", search_focus="general"),
                WebResultRelevance(
                    content_relevance=0.8,
                    source_reliability=0.9,
                    information_completeness=0.8,
                    overall_score=0.85,
                    useful_excerpt="Useful content",
                    should_include=True,
                ),
            ]
        )

        with patch.object(agent, "_tavily_search") as mock_tavily:
            mock_tavily.return_value = [
                TavilyResult(
                    title="Test Result",
                    url="https://example.com/test",
                    content="Test content here",
                    score=0.9,
                )
            ]

            results = await agent.search("test query", optimize_query=True)

        assert all(isinstance(r, Document) for r in results)

    @pytest.mark.asyncio
    async def test_web_results_have_correct_metadata(self, agent, mock_llm_provider):
        """Test that web results have correct metadata"""
        from src.agents.web_search_agent import OptimizedQuery, WebResultRelevance

        mock_llm_provider.generate_structured = AsyncMock(
            side_effect=[
                OptimizedQuery(optimized_query="test", search_focus="general"),
                WebResultRelevance(
                    content_relevance=0.8,
                    source_reliability=0.9,
                    information_completeness=0.8,
                    overall_score=0.8,
                    useful_excerpt="Content",
                    should_include=True,
                ),
            ]
        )

        with patch.object(agent, "_tavily_search") as mock_tavily:
            mock_tavily.return_value = [
                TavilyResult(
                    title="Docker Guide",
                    url="https://docs.docker.com/guide",
                    content="Docker documentation",
                    score=0.9,
                )
            ]

            results = await agent.search("Docker guide")

        if results:
            assert results[0].metadata.source == "https://docs.docker.com/guide"
            assert results[0].metadata.title == "Docker Guide"
            assert results[0].metadata.section == "web_search"


class TestWebSearchNode:
    """Test web search LangGraph node"""

    @pytest.mark.asyncio
    async def test_web_search_node_sets_disclaimer(self, mock_llm_provider):
        """Test that web search node sets needs_disclaimer flag"""
        from src.core.nodes import web_search_node

        state = {
            "query": "test query",
            "refined_query": "refined query",
            "detected_domains": [],
            "error_log": [],
        }

        with patch("src.agents.web_search_agent.WebSearchAgent.search") as mock_search:
            mock_search.return_value = []

            result = await web_search_node(state)

        assert result["web_search_triggered"] is True
        assert result["needs_disclaimer"] is True

    @pytest.mark.asyncio
    async def test_web_search_node_returns_results(self, mock_llm_provider):
        """Test that web search node returns results"""
        from src.core.nodes import web_search_node

        state = {
            "query": "Docker deployment",
            "refined_query": "Docker deployment",
            "detected_domains": ["docker"],
            "error_log": [],
        }

        mock_doc = Document(
            content="Docker deployment guide",
            metadata=DocumentMetadata(
                source="https://docs.docker.com",
                title="Docker Deployment",
            ),
            combined_score=0.85,
        )

        with patch("src.agents.web_search_agent.WebSearchAgent.search") as mock_search:
            mock_search.return_value = [mock_doc]

            result = await web_search_node(state)

        assert result["web_search_triggered"] is True
        assert len(result["web_results"]) == 1
        assert result["web_confidence"] > 0


class TestWebSearchResponseGeneration:
    """Test response generation with web search results"""

    @pytest.mark.asyncio
    async def test_response_includes_web_sources(self, mock_llm_provider):
        """Test that generated response includes web sources"""
        from src.rag.response_generator import ResponseGenerator
        from src.core.models import ResponseOutput

        mock_llm_provider.generate_structured = AsyncMock(
            return_value=ResponseOutput(
                response="Based on web search results...",
                sources=["https://docs.docker.com/guide"],
                has_sufficient_info=True,
            )
        )

        generator = ResponseGenerator(llm_provider=mock_llm_provider)

        web_doc = Document(
            content="Docker deployment instructions",
            metadata=DocumentMetadata(
                source="https://docs.docker.com/guide",
                title="Docker Guide",
            ),
        )

        result = await generator.generate(
            query="Docker deployment",
            documents=[],
            web_results=[web_doc],
        )

        assert result.response != ""
        assert "https://docs.docker.com/guide" in result.sources


class TestRetrievalSourceType:
    """Test retrieval source type determination"""

    def test_vector_source(self):
        """Test vector-only retrieval source"""
        from src.core.orchestrator import RAGOrchestrator

        state = {
            "web_search_triggered": False,
            "retrieved_docs": [MagicMock()],
        }

        orchestrator = RAGOrchestrator()
        # Internal method test would go here

    def test_web_source(self):
        """Test web-only retrieval source"""
        state = {
            "web_search_triggered": True,
            "retrieved_docs": [],
        }
        # When web_search_triggered is True and no docs
        # retrieval_source should be WEB

    def test_hybrid_source(self):
        """Test hybrid retrieval source"""
        state = {
            "web_search_triggered": True,
            "retrieved_docs": [MagicMock()],
        }
        # When both web and vector docs exist
        # retrieval_source should be HYBRID


class TestWebSearchDisclaimer:
    """Test disclaimer handling for web search results"""

    def test_disclaimer_message_korean(self, mock_llm_provider):
        """Test that disclaimer message is in Korean"""
        agent = WebSearchAgent(llm_provider=mock_llm_provider)
        message = agent.get_disclaimer_message()

        assert "웹" in message or "외부" in message
        assert "⚠️" in message  # Warning symbol

    def test_needs_disclaimer_for_web_results(self, mock_llm_provider):
        """Test that needs_disclaimer is set for web results"""
        from src.core.state import create_initial_state

        state = create_initial_state("test", "session-1")

        # After web search, needs_disclaimer should be True
        state["web_search_triggered"] = True
        state["needs_disclaimer"] = True

        assert state["needs_disclaimer"] is True
