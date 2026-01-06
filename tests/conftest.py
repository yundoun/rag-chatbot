"""Pytest configuration and fixtures"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    client = MagicMock()

    # Mock chat completion
    completion_response = MagicMock()
    completion_response.choices = [
        MagicMock(message=MagicMock(content='{"test": "response"}'))
    ]
    client.chat.completions.create = AsyncMock(return_value=completion_response)

    # Mock embeddings
    embedding_response = MagicMock()
    embedding_response.data = [MagicMock(embedding=[0.1] * 1536)]
    client.embeddings.create = AsyncMock(return_value=embedding_response)

    return client


@pytest.fixture
def mock_llm_provider(mock_openai_client):
    """Mock LLM Provider"""
    from src.llm.provider import LLMProvider

    provider = MagicMock(spec=LLMProvider)
    provider.generate = AsyncMock(return_value="Test response")
    provider.generate_structured = AsyncMock()
    provider.get_embeddings = AsyncMock(return_value=[[0.1] * 1536])
    provider.chat = AsyncMock(return_value="Test chat response")

    return provider


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client"""
    client = MagicMock()
    collection = MagicMock()

    # Mock query results
    collection.query.return_value = {
        "documents": [["Test document content about deployment"]],
        "metadatas": [[{"source": "test.md", "title": "Test Document"}]],
        "distances": [[0.1]],
        "ids": [["doc_1"]],
    }
    collection.count.return_value = 1
    collection.add = MagicMock()
    collection.delete = MagicMock()
    collection.update = MagicMock()

    client.get_or_create_collection.return_value = collection

    return client


@pytest.fixture
def mock_vector_store(mock_chroma_client):
    """Mock VectorStoreManager"""
    from src.vectorstore.manager import VectorStoreManager

    store = MagicMock(spec=VectorStoreManager)
    store.search = AsyncMock(
        return_value=[
            {
                "content": "Test document content about deployment",
                "metadata": {"source": "test.md", "title": "Test Document"},
                "distance": 0.1,
                "id": "doc_1",
            }
        ]
    )
    store.add_documents = AsyncMock(return_value=["doc_1"])
    store.get_document_count.return_value = 1

    return store


@pytest.fixture
def sample_query_analysis_output():
    """Sample query analysis output"""
    from src.core.models import QueryAnalysisOutput, Complexity

    return QueryAnalysisOutput(
        refined_query="Docker를 사용한 배포 방법",
        complexity=Complexity.SIMPLE,
        clarity_confidence=0.9,
        is_ambiguous=False,
        ambiguity_type=None,
        detected_domains=["devops", "deployment"],
    )


@pytest.fixture
def sample_documents():
    """Sample retrieved documents"""
    from src.core.models import Document, DocumentMetadata

    return [
        Document(
            content="Docker를 사용한 배포 방법: 1. Dockerfile 작성 2. 이미지 빌드 3. 컨테이너 실행",
            metadata=DocumentMetadata(
                source="deployment.md",
                title="배포 가이드",
                section="Docker",
            ),
            embedding_score=0.95,
        ),
        Document(
            content="docker build -t myapp . 명령으로 이미지를 빌드합니다.",
            metadata=DocumentMetadata(
                source="docker-guide.md",
                title="Docker 가이드",
            ),
            embedding_score=0.85,
        ),
    ]


@pytest.fixture
def sample_rag_state():
    """Sample RAG state"""
    return {
        "query": "Docker 배포 방법은?",
        "search_scope": "all",
        "session_id": "test-session-001",
        "refined_query": "",
        "complexity": "simple",
        "clarity_confidence": 0.9,
        "is_ambiguous": False,
        "ambiguity_type": None,
        "detected_domains": ["devops"],
        "clarification_needed": False,
        "clarification_question": None,
        "clarification_options": None,
        "user_response": None,
        "interaction_count": 0,
        "retrieved_docs": [],
        "relevance_scores": [],
        "avg_relevance": 0.0,
        "high_relevance_count": 0,
        "retrieval_source": "vector",
        "retry_count": 0,
        "rewritten_queries": [],
        "correction_triggered": False,
        "web_search_triggered": False,
        "web_results": [],
        "web_confidence": 0.0,
        "generated_response": "",
        "response_confidence": 0.0,
        "sources": [],
        "needs_disclaimer": False,
        "start_time": datetime.now(),
        "end_time": None,
        "total_llm_calls": 0,
        "error_log": [],
        "current_node": "start",
    }
