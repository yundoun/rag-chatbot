"""Integration tests for basic RAG flow"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.core.models import (
    QueryAnalysisOutput,
    ResponseOutput,
    Complexity,
    Document,
    DocumentMetadata,
)


class TestBasicRAGFlow:
    """Test basic RAG flow from query to response"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from src.api.main import app
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    @pytest.mark.asyncio
    @patch("src.api.routes.chat.QueryProcessor")
    @patch("src.api.routes.chat.DocumentRetriever")
    @patch("src.api.routes.chat.ResponseGenerator")
    async def test_chat_endpoint_success(
        self,
        mock_response_generator_class,
        mock_retriever_class,
        mock_query_processor_class,
        client,
        sample_documents,
    ):
        """Test successful chat request"""
        # Setup mocks
        mock_query_processor = MagicMock()
        mock_query_processor.analyze = AsyncMock(
            return_value=QueryAnalysisOutput(
                refined_query="Docker 배포 방법",
                complexity=Complexity.SIMPLE,
                clarity_confidence=0.9,
                is_ambiguous=False,
                ambiguity_type=None,
                detected_domains=["devops"],
            )
        )
        mock_query_processor_class.return_value = mock_query_processor

        mock_retriever = MagicMock()
        mock_retriever.retrieve = AsyncMock(return_value=sample_documents)
        mock_retriever.calculate_relevance_metrics = MagicMock(
            return_value={
                "avg_relevance": 0.9,
                "high_relevance_count": 2,
                "relevance_scores": [0.95, 0.85],
            }
        )
        mock_retriever_class.return_value = mock_retriever

        mock_response_gen = MagicMock()
        mock_response_gen.generate = AsyncMock(
            return_value=ResponseOutput(
                response="Docker로 배포하려면 다음 단계를 따르세요: 1. Dockerfile 작성 [1]",
                sources=["deployment.md"],
                has_sufficient_info=True,
            )
        )
        mock_response_gen.evaluate_response_quality = MagicMock(return_value=0.9)
        mock_response_generator_class.return_value = mock_response_gen

        # Make request
        response = client.post(
            "/api/chat",
            json={"query": "Docker 배포 방법은?"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        assert "sources" in data
        assert "confidence" in data
        assert "session_id" in data
        assert "processing_time_ms" in data
        assert data["retrieval_source"] == "vector"

    def test_chat_endpoint_empty_query(self, client):
        """Test chat with empty query"""
        response = client.post(
            "/api/chat",
            json={"query": ""}
        )

        # Should return 400 or handle gracefully
        assert response.status_code in [400, 422, 500]


class TestAPISchemas:
    """Test API request/response schemas"""

    def test_rag_request_validation(self):
        """Test RAGRequest validation"""
        from src.core.models import RAGRequest

        # Valid request
        request = RAGRequest(query="테스트 질문")
        assert request.query == "테스트 질문"
        assert request.session_id is None
        assert request.search_scope == "all"

        # With optional fields
        request = RAGRequest(
            query="테스트 질문",
            session_id="test-123",
            search_scope="docs",
        )
        assert request.session_id == "test-123"

    def test_rag_response_model(self):
        """Test RAGResponse model"""
        from src.core.models import RAGResponse, RetrievalSource

        response = RAGResponse(
            response="테스트 응답입니다.",
            sources=["doc1.md", "doc2.md"],
            confidence=0.85,
            needs_disclaimer=False,
            retrieval_source=RetrievalSource.VECTOR,
            processing_time_ms=1500,
            session_id="test-session",
        )

        assert response.response == "테스트 응답입니다."
        assert len(response.sources) == 2
        assert response.confidence == 0.85


class TestQueryProcessorIntegration:
    """Integration tests for QueryProcessor"""

    @pytest.mark.asyncio
    async def test_query_processor_with_mock_llm(self, mock_llm_provider):
        """Test QueryProcessor with mocked LLM"""
        from src.agents.query_processor import QueryProcessor
        from src.core.models import QueryAnalysisOutput, Complexity

        # Configure mock response
        mock_llm_provider.generate_structured = AsyncMock(
            return_value=QueryAnalysisOutput(
                refined_query="Docker를 사용한 배포 방법",
                complexity=Complexity.SIMPLE,
                clarity_confidence=0.9,
                is_ambiguous=False,
                ambiguity_type=None,
                detected_domains=["devops"],
            )
        )

        processor = QueryProcessor(llm_provider=mock_llm_provider)
        result = await processor.analyze("Docker 배포 방법은?")

        assert isinstance(result, QueryAnalysisOutput)
        assert result.complexity == Complexity.SIMPLE
        assert result.clarity_confidence > 0.7


class TestDocumentRetrieverIntegration:
    """Integration tests for DocumentRetriever"""

    @pytest.mark.asyncio
    async def test_retriever_with_mock_store(self, mock_vector_store):
        """Test DocumentRetriever with mocked vector store"""
        from src.rag.retriever import DocumentRetriever

        retriever = DocumentRetriever(vector_store=mock_vector_store)
        documents = await retriever.retrieve("Docker 배포")

        assert len(documents) > 0
        assert documents[0].content is not None
        assert documents[0].metadata is not None

    @pytest.mark.asyncio
    async def test_retriever_metrics_calculation(self, sample_documents):
        """Test relevance metrics calculation"""
        from src.rag.retriever import DocumentRetriever

        retriever = DocumentRetriever()
        metrics = retriever.calculate_relevance_metrics(sample_documents, threshold=0.8)

        assert "avg_relevance" in metrics
        assert "high_relevance_count" in metrics
        assert "relevance_scores" in metrics
        assert metrics["high_relevance_count"] >= 0


class TestResponseGeneratorIntegration:
    """Integration tests for ResponseGenerator"""

    @pytest.mark.asyncio
    async def test_generator_with_mock_llm(
        self,
        mock_llm_provider,
        sample_documents,
    ):
        """Test ResponseGenerator with mocked LLM"""
        from src.rag.response_generator import ResponseGenerator
        from src.core.models import ResponseOutput

        mock_llm_provider.generate_structured = AsyncMock(
            return_value=ResponseOutput(
                response="Docker 배포를 위해서는 Dockerfile을 작성하고 이미지를 빌드합니다 [1].",
                sources=["deployment.md"],
                has_sufficient_info=True,
            )
        )

        generator = ResponseGenerator(llm_provider=mock_llm_provider)
        result = await generator.generate(
            query="Docker 배포 방법은?",
            documents=sample_documents,
        )

        assert isinstance(result, ResponseOutput)
        assert result.response is not None
        assert len(result.sources) > 0

    def test_response_quality_evaluation(self, sample_documents):
        """Test response quality evaluation"""
        from src.rag.response_generator import ResponseGenerator
        from src.core.models import ResponseOutput

        generator = ResponseGenerator()

        # High quality response
        response = ResponseOutput(
            response="Docker 배포를 위해서는 Dockerfile을 작성하고 이미지를 빌드합니다. 자세한 내용은 다음과 같습니다...",
            sources=["deployment.md", "docker-guide.md"],
            has_sufficient_info=True,
        )
        quality = generator.evaluate_response_quality(response, sample_documents)
        assert quality >= 0.7

        # Low quality response
        response_low = ResponseOutput(
            response="모름",
            sources=[],
            has_sufficient_info=False,
        )
        quality_low = generator.evaluate_response_quality(response_low, sample_documents)
        assert quality_low < 0.5
