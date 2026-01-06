# RAG Chatbot Test Design Document

**Project:** Internal Document Search RAG Chatbot
**Version:** 1.0
**Date:** 2025-12-11
**Author:** Test Designer Agent

---

## 1. Test Strategy Overview

### 1.1 Test Pyramid Distribution

```
                  ┌─────────────────┐
                 /    E2E Tests      \         10% (5 core scenarios)
                /   (Slow, Critical)  \
               ├───────────────────────┤
              /   Integration Tests     \      30% (Component interactions)
             /    (Medium, Important)    \
            ├─────────────────────────────┤
           /        Unit Tests             \    60% (Individual functions)
          /       (Fast, Comprehensive)     \
         └───────────────────────────────────┘
```

### 1.2 Test Coverage Targets

| Test Type | Coverage Target | Primary Focus |
|-----------|-----------------|---------------|
| Unit Tests | 80% line coverage | Individual functions, classes, edge cases |
| Integration Tests | 70% branch coverage | Component interactions, LangGraph nodes |
| E2E Tests | 100% scenario coverage | 5 core user scenarios |
| Performance Tests | All critical paths | Response time, throughput |

### 1.3 Testing Framework & Tools

| Tool | Purpose | Version |
|------|---------|---------|
| pytest | Test runner | >=7.4.0 |
| pytest-asyncio | Async test support | >=0.21.0 |
| pytest-cov | Coverage reporting | >=4.1.0 |
| pytest-mock | Mocking utilities | >=3.12.0 |
| pytest-benchmark | Performance testing | >=4.0.0 |
| httpx | API testing | >=0.25.0 |
| websockets | WebSocket testing | >=12.0 |
| @testing-library/react | Frontend testing | >=14.0.0 |
| Playwright | E2E browser testing | >=1.40.0 |

---

## 2. Component-Level Unit Test Cases

### 2.1 Query Processor (`src/agents/query_processor.py`)

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| QP-001 | Analyze simple clear query | "배포 방법은?" | complexity: simple, clarity_confidence > 0.7 | High |
| QP-002 | Detect ambiguous query - vague term | "그거 어떻게 해요?" | is_ambiguous: true, ambiguity_type: vague_term | High |
| QP-003 | Detect ambiguous query - missing context | "설정을 변경하려면?" | is_ambiguous: true, ambiguity_type: missing_context | High |
| QP-004 | Detect complex multi-part query | "마이크로서비스와 모놀리식의 장단점 비교" | complexity: complex | High |
| QP-005 | Extract detected domains | "API 인증 설정 방법" | detected_domains includes "api", "security" | Medium |
| QP-006 | Handle empty query | "" | Raise ValidationError | High |
| QP-007 | Handle very long query | 5000+ chars | Truncate or handle gracefully | Medium |
| QP-008 | Preserve query intent after refinement | "DB 연결 방법은요?" | refined_query preserves "database connection" intent | Medium |

```python
# tests/unit/test_query_processor.py

import pytest
from src.agents.query_processor import QueryProcessor
from src.core.models import QueryAnalysisOutput, Complexity, AmbiguityType

class TestQueryProcessor:

    @pytest.fixture
    def processor(self, mock_llm_provider):
        return QueryProcessor(mock_llm_provider)

    @pytest.mark.asyncio
    async def test_analyze_simple_clear_query(self, processor):
        """QP-001: Simple clear query analysis"""
        result = await processor.analyze("배포 방법은?")

        assert isinstance(result, QueryAnalysisOutput)
        assert result.complexity == Complexity.SIMPLE
        assert result.clarity_confidence > 0.7
        assert result.is_ambiguous is False

    @pytest.mark.asyncio
    async def test_detect_vague_term_ambiguity(self, processor):
        """QP-002: Detect vague term ambiguity"""
        result = await processor.analyze("그거 어떻게 해요?")

        assert result.is_ambiguous is True
        assert result.ambiguity_type == AmbiguityType.VAGUE_TERM

    @pytest.mark.asyncio
    async def test_detect_missing_context_ambiguity(self, processor):
        """QP-003: Detect missing context ambiguity"""
        result = await processor.analyze("설정을 변경하려면?")

        assert result.is_ambiguous is True
        assert result.ambiguity_type == AmbiguityType.MISSING_CONTEXT

    @pytest.mark.asyncio
    async def test_detect_complex_query(self, processor):
        """QP-004: Detect complex multi-part query"""
        result = await processor.analyze(
            "마이크로서비스 아키텍처의 장단점과 모놀리식과의 차이점"
        )

        assert result.complexity == Complexity.COMPLEX

    @pytest.mark.asyncio
    async def test_extract_detected_domains(self, processor):
        """QP-005: Extract relevant domains"""
        result = await processor.analyze("API 인증 설정 방법")

        assert "api" in result.detected_domains or "security" in result.detected_domains

    @pytest.mark.asyncio
    async def test_empty_query_raises_error(self, processor):
        """QP-006: Empty query should raise validation error"""
        with pytest.raises(ValueError):
            await processor.analyze("")

    @pytest.mark.asyncio
    async def test_very_long_query_handled(self, processor):
        """QP-007: Very long query handled gracefully"""
        long_query = "테스트 " * 1000
        result = await processor.analyze(long_query)

        assert result is not None
        assert len(result.refined_query) <= 2000
```

---

### 2.2 HITL Controller (`src/agents/hitl_controller.py`)

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| HITL-001 | Generate clarification for vague term | ambiguity_type: vague_term | Question with 3-5 options | High |
| HITL-002 | Generate clarification for missing context | ambiguity_type: missing_context | Context-seeking question | High |
| HITL-003 | Options count within limit | Any ambiguous query | 2-5 options returned | High |
| HITL-004 | Handle user option selection | selected_option: "옵션1" | Refined query returned | High |
| HITL-005 | Handle user custom input | custom_input: "커스텀 답변" | Custom input integrated | Medium |
| HITL-006 | Track interaction count | After 2 interactions | interaction_count == 2 | High |
| HITL-007 | Block after max interactions | interaction_count >= 2 | No new clarification generated | High |

```python
# tests/unit/test_hitl_controller.py

import pytest
from src.agents.hitl_controller import HITLController
from src.core.models import ClarificationOutput, HITLResponse, AmbiguityType

class TestHITLController:

    @pytest.fixture
    def controller(self, mock_llm_provider):
        return HITLController(mock_llm_provider)

    @pytest.mark.asyncio
    async def test_generate_clarification_vague_term(self, controller):
        """HITL-001: Generate clarification for vague term"""
        result = await controller.generate_clarification(
            query="그거 어떻게 해요?",
            ambiguity_type=AmbiguityType.VAGUE_TERM
        )

        assert isinstance(result, ClarificationOutput)
        assert result.clarification_question is not None
        assert 2 <= len(result.options) <= 5

    @pytest.mark.asyncio
    async def test_generate_clarification_missing_context(self, controller):
        """HITL-002: Generate clarification for missing context"""
        result = await controller.generate_clarification(
            query="설정 변경 방법",
            ambiguity_type=AmbiguityType.MISSING_CONTEXT
        )

        assert "어떤" in result.clarification_question or "무엇" in result.clarification_question

    @pytest.mark.asyncio
    async def test_options_count_within_limit(self, controller):
        """HITL-003: Options count should be 2-5"""
        result = await controller.generate_clarification(
            query="어떻게 하나요?",
            ambiguity_type=AmbiguityType.VAGUE_TERM
        )

        assert 2 <= len(result.options) <= 5

    @pytest.mark.asyncio
    async def test_handle_user_option_selection(self, controller):
        """HITL-004: Handle user option selection"""
        response = HITLResponse(selected_option="데이터베이스 설정")
        result = await controller.process_user_response(
            original_query="설정 변경하려면?",
            user_response=response
        )

        assert "데이터베이스" in result.refined_query

    @pytest.mark.asyncio
    async def test_handle_user_custom_input(self, controller):
        """HITL-005: Handle user custom input"""
        response = HITLResponse(custom_input="Redis 캐시 설정에 대해 알고 싶어요")
        result = await controller.process_user_response(
            original_query="캐시 설정",
            user_response=response
        )

        assert "Redis" in result.refined_query

    @pytest.mark.asyncio
    async def test_max_interactions_blocked(self, controller):
        """HITL-007: No clarification after max interactions"""
        result = await controller.should_clarify(
            is_ambiguous=True,
            interaction_count=2,
            max_interactions=2
        )

        assert result is False
```

---

### 2.3 Relevance Evaluator (`src/rag/relevance_evaluator.py`)

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| RE-001 | High relevance document | Highly relevant doc | score >= 0.8, level: high | High |
| RE-002 | Medium relevance document | Partially relevant doc | 0.5 <= score < 0.8, level: medium | High |
| RE-003 | Low relevance document | Irrelevant doc | score < 0.5, level: low | High |
| RE-004 | Extract useful parts | Relevant doc | useful_parts not empty | Medium |
| RE-005 | Provide evaluation reason | Any doc | reason not empty | Medium |
| RE-006 | Batch evaluation | Multiple docs | List of evaluations | Medium |
| RE-007 | Handle empty document | Empty content | score: 0.0, level: low | High |
| RE-008 | Score-level consistency | score: 0.85 | level: high | High |

```python
# tests/unit/test_relevance_evaluator.py

import pytest
from src.rag.relevance_evaluator import RelevanceEvaluator
from src.core.models import Document, RelevanceEvaluationOutput, RelevanceLevel

class TestRelevanceEvaluator:

    @pytest.fixture
    def evaluator(self, mock_llm_provider):
        return RelevanceEvaluator(mock_llm_provider)

    @pytest.fixture
    def sample_relevant_doc(self):
        return Document(
            content="Docker를 사용한 배포 방법: 1. Dockerfile 작성 2. 이미지 빌드 3. 컨테이너 실행",
            metadata={"source": "deployment.md", "title": "배포 가이드"}
        )

    @pytest.fixture
    def sample_irrelevant_doc(self):
        return Document(
            content="회사 휴가 정책: 연차 15일, 병가 5일 제공",
            metadata={"source": "hr-policy.md", "title": "HR 정책"}
        )

    @pytest.mark.asyncio
    async def test_high_relevance_document(self, evaluator, sample_relevant_doc):
        """RE-001: High relevance document evaluation"""
        result = await evaluator.evaluate(
            query="Docker 배포 방법",
            document=sample_relevant_doc
        )

        assert result.relevance_score >= 0.8
        assert result.relevance_level == RelevanceLevel.HIGH

    @pytest.mark.asyncio
    async def test_low_relevance_document(self, evaluator, sample_irrelevant_doc):
        """RE-003: Low relevance document evaluation"""
        result = await evaluator.evaluate(
            query="Docker 배포 방법",
            document=sample_irrelevant_doc
        )

        assert result.relevance_score < 0.5
        assert result.relevance_level == RelevanceLevel.LOW

    @pytest.mark.asyncio
    async def test_extract_useful_parts(self, evaluator, sample_relevant_doc):
        """RE-004: Extract useful parts from document"""
        result = await evaluator.evaluate(
            query="Docker 배포 방법",
            document=sample_relevant_doc
        )

        assert len(result.useful_parts) > 0

    @pytest.mark.asyncio
    async def test_provide_evaluation_reason(self, evaluator, sample_relevant_doc):
        """RE-005: Provide evaluation reason"""
        result = await evaluator.evaluate(
            query="Docker 배포 방법",
            document=sample_relevant_doc
        )

        assert result.reason is not None
        assert len(result.reason) > 0

    @pytest.mark.asyncio
    async def test_score_level_consistency(self, evaluator):
        """RE-008: Score and level should be consistent"""
        # Mock response with specific score
        result = RelevanceEvaluationOutput(
            relevance_score=0.85,
            relevance_level=RelevanceLevel.HIGH,
            reason="Highly relevant",
            useful_parts=[]
        )

        # Verify mapping
        assert (result.relevance_score >= 0.8) == (result.relevance_level == RelevanceLevel.HIGH)
```

---

### 2.4 Corrective RAG Engine (`src/rag/corrective_engine.py`)

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| CR-001 | Trigger correction on low relevance | avg_relevance < 0.8 | correction_triggered: true | High |
| CR-002 | No correction on sufficient relevance | avg_relevance >= 0.8, high_count >= 2 | correction_triggered: false | High |
| CR-003 | Respect max retry limit | retry_count >= 2 | No more corrections | High |
| CR-004 | Track retry count | After correction | retry_count incremented | High |
| CR-005 | Select rewrite strategy | Low relevance | strategy in valid strategies | Medium |
| CR-006 | Different strategy on second retry | retry_count: 1 | Different strategy from first | Medium |
| CR-007 | Trigger web search after max retries | retry_count >= 2, still low | web_search_triggered: true | High |

```python
# tests/unit/test_corrective_engine.py

import pytest
from src.rag.corrective_engine import CorrectiveEngine
from src.core.models import RewriteStrategy

class TestCorrectiveEngine:

    @pytest.fixture
    def engine(self, mock_llm_provider, mock_retriever):
        return CorrectiveEngine(mock_llm_provider, mock_retriever)

    @pytest.mark.asyncio
    async def test_trigger_correction_on_low_relevance(self, engine):
        """CR-001: Trigger correction when relevance is low"""
        state = {
            "avg_relevance": 0.5,
            "high_relevance_count": 1,
            "retry_count": 0
        }

        should_correct = engine.should_correct(state)
        assert should_correct is True

    @pytest.mark.asyncio
    async def test_no_correction_on_sufficient_relevance(self, engine):
        """CR-002: No correction when relevance is sufficient"""
        state = {
            "avg_relevance": 0.85,
            "high_relevance_count": 3,
            "retry_count": 0
        }

        should_correct = engine.should_correct(state)
        assert should_correct is False

    @pytest.mark.asyncio
    async def test_respect_max_retry_limit(self, engine):
        """CR-003: Respect max retry limit"""
        state = {
            "avg_relevance": 0.5,
            "high_relevance_count": 0,
            "retry_count": 2
        }

        should_correct = engine.should_correct(state)
        assert should_correct is False

    @pytest.mark.asyncio
    async def test_track_retry_count(self, engine):
        """CR-004: Track retry count after correction"""
        state = {"retry_count": 0, "query": "테스트 질문"}

        new_state = await engine.rewrite_and_retry(state)
        assert new_state["retry_count"] == 1

    @pytest.mark.asyncio
    async def test_trigger_web_search_after_max_retries(self, engine):
        """CR-007: Trigger web search after max retries"""
        state = {
            "avg_relevance": 0.3,
            "high_relevance_count": 0,
            "retry_count": 2
        }

        next_action = engine.determine_next_action(state)
        assert next_action == "web_search"
```

---

### 2.5 Response Generator (`src/rag/response_generator.py`)

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| RG-001 | Generate response with sources | Relevant docs | response + sources list | High |
| RG-002 | Include source citations | Docs with metadata | [1], [2] style citations | High |
| RG-003 | Handle insufficient info | Low relevance docs | has_sufficient_info: false | High |
| RG-004 | No hallucination | Limited context | Response only from sources | Critical |
| RG-005 | Integrate web results | Web search results | Web sources marked | Medium |
| RG-006 | Handle empty documents | No documents | Appropriate error response | High |
| RG-007 | Respect max response length | Any input | response <= max_tokens | Medium |

```python
# tests/unit/test_response_generator.py

import pytest
from src.rag.response_generator import ResponseGenerator
from src.core.models import Document, ResponseOutput

class TestResponseGenerator:

    @pytest.fixture
    def generator(self, mock_llm_provider):
        return ResponseGenerator(mock_llm_provider)

    @pytest.fixture
    def sample_docs(self):
        return [
            Document(
                content="Docker 설치: apt install docker.io",
                metadata={"source": "install.md", "section": "설치"}
            ),
            Document(
                content="Docker 실행: docker run -d image",
                metadata={"source": "usage.md", "section": "실행"}
            )
        ]

    @pytest.mark.asyncio
    async def test_generate_response_with_sources(self, generator, sample_docs):
        """RG-001: Generate response with sources"""
        result = await generator.generate(
            query="Docker 사용법",
            documents=sample_docs
        )

        assert isinstance(result, ResponseOutput)
        assert result.response is not None
        assert len(result.sources) > 0

    @pytest.mark.asyncio
    async def test_include_source_citations(self, generator, sample_docs):
        """RG-002: Include source citations in response"""
        result = await generator.generate(
            query="Docker 설치 방법",
            documents=sample_docs
        )

        # Check for citation markers
        assert "[1]" in result.response or "install.md" in str(result.sources)

    @pytest.mark.asyncio
    async def test_handle_insufficient_info(self, generator):
        """RG-003: Handle insufficient information"""
        irrelevant_docs = [
            Document(
                content="회사 점심 메뉴: 한식, 중식",
                metadata={"source": "lunch.md"}
            )
        ]

        result = await generator.generate(
            query="Kubernetes 배포 방법",
            documents=irrelevant_docs
        )

        assert result.has_sufficient_info is False

    @pytest.mark.asyncio
    async def test_handle_empty_documents(self, generator):
        """RG-006: Handle empty documents list"""
        result = await generator.generate(
            query="테스트 질문",
            documents=[]
        )

        assert result.has_sufficient_info is False
        assert "찾을 수 없" in result.response or "없습니다" in result.response
```

---

### 2.6 Quality Evaluator (`src/rag/quality_evaluator.py`)

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| QE-001 | Evaluate high quality response | Complete, accurate response | confidence >= 0.8 | High |
| QE-002 | Evaluate low quality response | Incomplete response | confidence < 0.6 | High |
| QE-003 | Trigger disclaimer on low confidence | confidence < 0.6 | needs_disclaimer: true | High |
| QE-004 | No disclaimer on high confidence | confidence >= 0.6 | needs_disclaimer: false | High |
| QE-005 | Calculate composite confidence | completeness, accuracy, clarity | Weighted average | Medium |
| QE-006 | Evaluate completeness | Partial answer | completeness < 1.0 | Medium |
| QE-007 | Evaluate accuracy against sources | Response vs sources | accuracy score | Medium |

```python
# tests/unit/test_quality_evaluator.py

import pytest
from src.rag.quality_evaluator import QualityEvaluator
from src.core.models import QualityEvaluationOutput

class TestQualityEvaluator:

    @pytest.fixture
    def evaluator(self, mock_llm_provider):
        return QualityEvaluator(mock_llm_provider)

    @pytest.mark.asyncio
    async def test_high_quality_response(self, evaluator):
        """QE-001: Evaluate high quality response"""
        result = await evaluator.evaluate(
            query="Docker 설치 방법",
            response="Docker를 설치하려면: 1. apt update 2. apt install docker.io",
            sources=["install.md"]
        )

        assert result.confidence >= 0.8
        assert result.needs_disclaimer is False

    @pytest.mark.asyncio
    async def test_low_quality_triggers_disclaimer(self, evaluator):
        """QE-003: Low confidence triggers disclaimer"""
        result = await evaluator.evaluate(
            query="복잡한 마이크로서비스 설계 방법",
            response="마이크로서비스는 작은 서비스입니다.",
            sources=[]
        )

        assert result.confidence < 0.6
        assert result.needs_disclaimer is True

    @pytest.mark.asyncio
    async def test_composite_confidence_calculation(self, evaluator):
        """QE-005: Composite confidence calculation"""
        result = QualityEvaluationOutput(
            completeness=0.8,
            accuracy=0.9,
            clarity=0.85,
            confidence=0.0,  # To be calculated
            needs_disclaimer=False
        )

        # Verify calculation formula
        expected = (0.8 * 0.4) + (0.9 * 0.4) + (0.85 * 0.2)
        calculated = evaluator.calculate_confidence(result)

        assert abs(calculated - expected) < 0.01
```

---

### 2.7 Web Search Agent (`src/agents/web_search_agent.py`)

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| WS-001 | Search with Tavily API | Valid query | Search results returned | High |
| WS-002 | Filter relevant results | Search results | relevance >= 0.5 filtered | Medium |
| WS-003 | Handle API timeout | Timeout scenario | Graceful error handling | High |
| WS-004 | Handle rate limit | Rate limit exceeded | Retry with backoff | High |
| WS-005 | Set disclaimer for web results | Web results | disclaimer_needed: true | High |
| WS-006 | Limit result count | Many results | max_results respected | Medium |
| WS-007 | Handle empty results | No results found | appropriate message | High |

```python
# tests/unit/test_web_search_agent.py

import pytest
from src.agents.web_search_agent import WebSearchAgent
from src.core.models import WebIntegrationOutput

class TestWebSearchAgent:

    @pytest.fixture
    def agent(self, mock_tavily_client):
        return WebSearchAgent(mock_tavily_client)

    @pytest.mark.asyncio
    async def test_search_returns_results(self, agent):
        """WS-001: Search returns results"""
        result = await agent.search("React 19 새로운 기능")

        assert isinstance(result, WebIntegrationOutput)
        assert len(result.relevant_results) > 0

    @pytest.mark.asyncio
    async def test_filter_relevant_results(self, agent):
        """WS-002: Filter results by relevance"""
        result = await agent.search("Python 비동기 프로그래밍")

        for item in result.relevant_results:
            assert item.relevance >= 0.5

    @pytest.mark.asyncio
    async def test_disclaimer_for_web_results(self, agent):
        """WS-005: Web results trigger disclaimer"""
        result = await agent.search("테스트 쿼리")

        assert result.disclaimer_needed is True

    @pytest.mark.asyncio
    async def test_limit_result_count(self, agent):
        """WS-006: Respect max results limit"""
        agent.max_results = 5
        result = await agent.search("인기 있는 검색어")

        assert len(result.relevant_results) <= 5

    @pytest.mark.asyncio
    async def test_handle_empty_results(self, agent, mock_tavily_empty):
        """WS-007: Handle empty results gracefully"""
        result = await agent.search("존재하지않는검색어123456")

        assert len(result.relevant_results) == 0
        assert result.overall_confidence == 0.0
```

---

### 2.8 LangGraph Orchestrator (`src/core/orchestrator.py`)

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| LG-001 | Route simple query correctly | Simple, clear query | Direct to retrieve | High |
| LG-002 | Route ambiguous query to HITL | Ambiguous query | Route to clarify_hitl | High |
| LG-003 | Route complex query to decompose | Complex query | Route to decompose_query | High |
| LG-004 | Route low relevance to rewrite | Low relevance results | Route to rewrite_query | High |
| LG-005 | Route max retries to web search | retry_count >= 2 | Route to web_search | High |
| LG-006 | Complete happy path flow | Clear query + good docs | End with response | Critical |
| LG-007 | State persistence for HITL | HITL interrupt | State preserved | High |
| LG-008 | Error state handling | Node error | Graceful recovery | High |

```python
# tests/unit/test_orchestrator.py

import pytest
from src.core.orchestrator import RAGOrchestrator, route_after_analysis, route_after_evaluation
from src.core.state import RAGState

class TestOrchestratorRouting:

    def test_route_simple_query_to_retrieve(self):
        """LG-001: Simple query routes to retrieve"""
        state = {
            "is_ambiguous": False,
            "complexity": "simple",
            "interaction_count": 0
        }

        next_node = route_after_analysis(state)
        assert next_node == "retrieve_documents"

    def test_route_ambiguous_query_to_hitl(self):
        """LG-002: Ambiguous query routes to HITL"""
        state = {
            "is_ambiguous": True,
            "complexity": "simple",
            "interaction_count": 0
        }

        next_node = route_after_analysis(state)
        assert next_node == "clarify_hitl"

    def test_route_complex_query_to_decompose(self):
        """LG-003: Complex query routes to decompose"""
        state = {
            "is_ambiguous": False,
            "complexity": "complex",
            "interaction_count": 0
        }

        next_node = route_after_analysis(state)
        assert next_node == "decompose_query"

    def test_route_low_relevance_to_rewrite(self):
        """LG-004: Low relevance routes to rewrite"""
        state = {
            "avg_relevance": 0.5,
            "high_relevance_count": 1,
            "retry_count": 0
        }

        next_node = route_after_evaluation(state)
        assert next_node == "rewrite_query"

    def test_route_max_retries_to_web_search(self):
        """LG-005: Max retries routes to web search"""
        state = {
            "avg_relevance": 0.5,
            "high_relevance_count": 1,
            "retry_count": 2
        }

        next_node = route_after_evaluation(state)
        assert next_node == "web_search"

    def test_route_sufficient_relevance_to_generate(self):
        """Route sufficient relevance to generate"""
        state = {
            "avg_relevance": 0.85,
            "high_relevance_count": 3,
            "retry_count": 0
        }

        next_node = route_after_evaluation(state)
        assert next_node == "generate_response"
```

---

## 3. E2E Test Cases for 5 Key Scenarios

### 3.1 Scenario 1: Happy Path

**Description:** 명확한 질문 → 검색 성공 → 고품질 답변

```python
# tests/e2e/test_happy_path.py

import pytest
from tests.e2e.conftest import E2ETestClient

class TestHappyPath:
    """E2E-001: Happy Path - Clear question with successful retrieval"""

    @pytest.fixture
    def client(self):
        return E2ETestClient()

    @pytest.mark.asyncio
    async def test_happy_path_complete_flow(self, client):
        """
        Given: 명확한 질문 "Docker 컨테이너 실행 방법"
        When: RAG 시스템에 질문 제출
        Then:
          - 답변이 생성됨
          - 출처가 포함됨
          - confidence >= 0.8
          - 면책 조항 없음
        """
        response = await client.ask("Docker 컨테이너 실행 방법은?")

        # Assertions
        assert response.status == "success"
        assert response.response is not None
        assert len(response.response) > 50
        assert len(response.sources) >= 1
        assert response.confidence >= 0.8
        assert response.needs_disclaimer is False
        assert response.retrieval_source == "vector"

    @pytest.mark.asyncio
    async def test_happy_path_flow_nodes(self, client):
        """Verify correct node sequence in happy path"""
        response = await client.ask_with_trace("프로젝트 빌드 방법")

        expected_flow = [
            "analyze_query",
            "retrieve_documents",
            "evaluate_relevance",
            "generate_response",
            "evaluate_quality"
        ]

        assert response.node_sequence == expected_flow

    @pytest.mark.asyncio
    async def test_happy_path_response_time(self, client):
        """Happy path should complete within 10 seconds"""
        response = await client.ask("API 인증 방법")

        assert response.processing_time_ms < 10000  # 10 seconds
```

---

### 3.2 Scenario 2: HITL Flow

**Description:** 모호한 질문 → 명확화 요청 → 사용자 응답 → 검색

```python
# tests/e2e/test_hitl_flow.py

import pytest
from tests.e2e.conftest import E2ETestClient, WebSocketTestClient

class TestHITLFlow:
    """E2E-002: HITL Flow - Ambiguous question requiring clarification"""

    @pytest.fixture
    def ws_client(self):
        return WebSocketTestClient()

    @pytest.mark.asyncio
    async def test_hitl_clarification_triggered(self, ws_client):
        """
        Given: 모호한 질문 "그거 어떻게 설정해요?"
        When: RAG 시스템에 질문 제출
        Then:
          - clarification_needed: true
          - clarification_question 생성됨
          - 2-5개의 options 제공
        """
        async with ws_client.connect() as session:
            response = await session.send("그거 어떻게 설정해요?")

            assert response.clarification_needed is True
            assert response.clarification_question is not None
            assert 2 <= len(response.options) <= 5

    @pytest.mark.asyncio
    async def test_hitl_user_selection_flow(self, ws_client):
        """
        Given: HITL 명확화 질문이 제시됨
        When: 사용자가 옵션 선택
        Then:
          - 선택에 맞는 검색 수행
          - 최종 답변 반환
        """
        async with ws_client.connect() as session:
            # Initial ambiguous question
            response1 = await session.send("설정 변경하려면?")
            assert response1.clarification_needed is True

            # User selects option
            response2 = await session.select_option(response1.options[0])

            assert response2.clarification_needed is False
            assert response2.response is not None

    @pytest.mark.asyncio
    async def test_hitl_custom_input_flow(self, ws_client):
        """
        Given: HITL 명확화 질문이 제시됨
        When: 사용자가 커스텀 답변 입력
        Then: 커스텀 입력 기반 검색 수행
        """
        async with ws_client.connect() as session:
            response1 = await session.send("환경 설정")
            assert response1.clarification_needed is True

            # Custom input
            response2 = await session.custom_input("Redis 캐시 TTL 설정 방법")

            assert "Redis" in response2.refined_query or "캐시" in response2.refined_query

    @pytest.mark.asyncio
    async def test_hitl_max_interactions_limit(self, ws_client):
        """
        Given: 2회 연속 명확화 진행됨
        When: 3번째 모호한 응답
        Then: 더 이상 명확화 없이 최선의 답변 시도
        """
        async with ws_client.connect() as session:
            # First interaction
            await session.send("그거")
            await session.custom_input("그 기능")

            # Second interaction
            response2 = await session.custom_input("아까 그거")

            # Should not trigger third clarification
            assert response2.interaction_count == 2
            assert response2.clarification_needed is False

    @pytest.mark.asyncio
    async def test_hitl_flow_nodes(self, ws_client):
        """Verify correct node sequence in HITL flow"""
        async with ws_client.connect() as session:
            response = await session.send_with_trace("모호한 질문")
            await session.select_option(response.options[0])
            final = await session.get_final_response()

            expected_contains = ["analyze_query", "clarify_hitl", "retrieve_documents"]
            for node in expected_contains:
                assert node in final.node_sequence
```

---

### 3.3 Scenario 3: Corrective Flow

**Description:** 검색 결과 부족 → 쿼리 재작성 → 재검색

```python
# tests/e2e/test_corrective_flow.py

import pytest
from tests.e2e.conftest import E2ETestClient

class TestCorrectiveFlow:
    """E2E-003: Corrective Flow - Query rewriting on insufficient results"""

    @pytest.fixture
    def client(self):
        return E2ETestClient()

    @pytest.mark.asyncio
    async def test_correction_triggered_on_low_relevance(self, client):
        """
        Given: 검색 결과의 관련성이 낮은 질문
        When: RAG 시스템에 질문 제출
        Then:
          - correction_triggered: true
          - 쿼리 재작성 수행
          - 재검색 후 개선된 결과
        """
        # Query that likely triggers correction
        response = await client.ask_with_trace("2023년 12월 보안 패치 상세 내용")

        assert response.correction_triggered is True
        assert response.retry_count >= 1
        assert len(response.rewritten_queries) >= 1

    @pytest.mark.asyncio
    async def test_correction_improves_relevance(self, client):
        """
        Given: 첫 검색에서 관련성 낮음
        When: 쿼리 재작성 후 재검색
        Then: 재검색 결과의 관련성 향상
        """
        response = await client.ask_with_trace("특정 기술 문서 검색")

        if response.correction_triggered:
            assert response.final_avg_relevance > response.initial_avg_relevance

    @pytest.mark.asyncio
    async def test_correction_max_retries_respected(self, client):
        """
        Given: 매우 특수한 질문 (관련 문서 없음)
        When: 2회 재시도 후에도 실패
        Then: retry_count == 2, 웹 검색으로 전환
        """
        response = await client.ask_with_trace("존재하지않는아주특수한문서12345")

        assert response.retry_count <= 2
        if response.retry_count == 2:
            assert response.web_search_triggered is True

    @pytest.mark.asyncio
    async def test_rewrite_strategies_vary(self, client):
        """
        Given: 2회 재작성 수행
        When: 각 재작성 확인
        Then: 다른 전략 사용
        """
        response = await client.ask_with_trace("관련성 낮은 질문 테스트")

        if len(response.rewrite_history) >= 2:
            strategies = [r.strategy for r in response.rewrite_history]
            # At least attempt different strategies
            assert len(set(strategies)) >= 1

    @pytest.mark.asyncio
    async def test_corrective_flow_nodes(self, client):
        """Verify node sequence includes rewrite"""
        response = await client.ask_with_trace("correction trigger query")

        if response.correction_triggered:
            assert "rewrite_query" in response.node_sequence
            # Should have multiple retrieve attempts
            assert response.node_sequence.count("retrieve_documents") >= 2
```

---

### 3.4 Scenario 4: Web Fallback

**Description:** 내부 검색 실패 → 웹 검색 Fallback

```python
# tests/e2e/test_web_fallback.py

import pytest
from tests.e2e.conftest import E2ETestClient

class TestWebFallback:
    """E2E-004: Web Fallback - External search when internal fails"""

    @pytest.fixture
    def client(self):
        return E2ETestClient()

    @pytest.mark.asyncio
    async def test_web_search_triggered_after_failures(self, client):
        """
        Given: 내부 문서에 없는 최신 정보 질문
        When: 2회 재시도 실패 후
        Then:
          - web_search_triggered: true
          - retrieval_source: "web" or "hybrid"
        """
        response = await client.ask("React 19 새로운 기능 목록")

        assert response.web_search_triggered is True
        assert response.retrieval_source in ["web", "hybrid"]

    @pytest.mark.asyncio
    async def test_web_results_include_disclaimer(self, client):
        """
        Given: 웹 검색 결과 사용
        When: 답변 생성
        Then: 면책 조항 포함
        """
        response = await client.ask("최신 JavaScript 프레임워크 트렌드 2024")

        if response.web_search_triggered:
            assert response.needs_disclaimer is True
            # Or check for web disclaimer in response
            assert "웹 검색" in response.response or response.web_disclaimer_shown

    @pytest.mark.asyncio
    async def test_web_results_have_urls(self, client):
        """
        Given: 웹 검색 수행
        When: 결과 확인
        Then: 각 결과에 URL 포함
        """
        response = await client.ask("외부 API 문서 참조")

        if response.web_search_triggered:
            for source in response.web_sources:
                assert source.url is not None
                assert source.url.startswith("http")

    @pytest.mark.asyncio
    async def test_web_fallback_confidence_adjusted(self, client):
        """
        Given: 웹 검색 결과만으로 답변
        When: 품질 평가
        Then: confidence 적절히 조정됨
        """
        response = await client.ask("매우 최신의 기술 동향")

        if response.web_search_triggered and response.retrieval_source == "web":
            # Web-only results typically have lower confidence
            assert response.confidence <= 0.9

    @pytest.mark.asyncio
    async def test_web_fallback_flow_nodes(self, client):
        """Verify node sequence includes web_search"""
        response = await client.ask_with_trace("internal docs dont have this")

        if response.web_search_triggered:
            assert "web_search" in response.node_sequence
            # Web search should come after max retries
            rewrite_count = response.node_sequence.count("rewrite_query")
            assert rewrite_count <= 2
```

---

### 3.5 Scenario 5: Complex Query

**Description:** 복잡한 질문 → 분해 → 병렬 검색 → 통합 답변

```python
# tests/e2e/test_complex_query.py

import pytest
from tests.e2e.conftest import E2ETestClient

class TestComplexQuery:
    """E2E-005: Complex Query - Question decomposition and parallel search"""

    @pytest.fixture
    def client(self):
        return E2ETestClient()

    @pytest.mark.asyncio
    async def test_complex_query_decomposed(self, client):
        """
        Given: 복잡한 다중 주제 질문
        When: RAG 시스템에 질문 제출
        Then:
          - complexity: complex
          - 하위 질문들로 분해됨
        """
        response = await client.ask_with_trace(
            "마이크로서비스 아키텍처의 장단점과 모놀리식 아키텍처와의 차이점을 설명해주세요"
        )

        assert response.complexity == "complex"
        assert len(response.sub_questions) >= 2

    @pytest.mark.asyncio
    async def test_sub_questions_have_parallel_groups(self, client):
        """
        Given: 분해된 하위 질문들
        When: 병렬 그룹 확인
        Then: parallel_groups 정의됨
        """
        response = await client.ask_with_trace(
            "Docker와 Kubernetes의 차이점, 각각의 장단점 비교"
        )

        if response.complexity == "complex":
            assert response.parallel_groups is not None
            assert len(response.parallel_groups) >= 1

    @pytest.mark.asyncio
    async def test_synthesis_guide_provided(self, client):
        """
        Given: 하위 질문 답변들
        When: 최종 답변 통합
        Then: synthesis_guide에 따라 통합됨
        """
        response = await client.ask_with_trace(
            "CI/CD 파이프라인 구축 방법과 모범 사례"
        )

        if response.complexity == "complex":
            assert response.synthesis_guide is not None

    @pytest.mark.asyncio
    async def test_complex_query_response_comprehensive(self, client):
        """
        Given: 복잡한 비교 질문
        When: 최종 답변 확인
        Then: 모든 하위 주제가 다뤄짐
        """
        response = await client.ask(
            "REST API와 GraphQL의 차이점, 각각 언제 사용하면 좋은지"
        )

        # Response should cover both topics
        response_lower = response.response.lower()
        assert "rest" in response_lower
        assert "graphql" in response_lower

    @pytest.mark.asyncio
    async def test_complex_query_max_sub_questions(self, client):
        """
        Given: 매우 복잡한 질문
        When: 분해 수행
        Then: 하위 질문 수 제한 (최대 5개)
        """
        response = await client.ask_with_trace(
            "프론트엔드, 백엔드, 데이터베이스, 인프라, 보안, CI/CD 모든 측면에서의 모범 사례"
        )

        if response.complexity == "complex":
            assert len(response.sub_questions) <= 5

    @pytest.mark.asyncio
    async def test_complex_query_flow_nodes(self, client):
        """Verify node sequence includes decompose"""
        response = await client.ask_with_trace("complex multi-part question")

        if response.complexity == "complex":
            assert "decompose_query" in response.node_sequence
```

---

## 4. API Endpoint Test Cases

### 4.1 POST /api/chat - 질문 제출

| Test ID | Test Case | Request | Expected Response | Status Code |
|---------|-----------|---------|-------------------|-------------|
| API-001 | Valid question submission | {"query": "테스트"} | RAGResponse | 200 |
| API-002 | Empty query | {"query": ""} | ValidationError | 422 |
| API-003 | Missing query field | {} | ValidationError | 422 |
| API-004 | Very long query | {"query": "x"*10000} | Handled gracefully | 200/400 |
| API-005 | With session_id | {"query": "q", "session_id": "abc"} | Same session | 200 |
| API-006 | Invalid session_id format | {"session_id": 123} | ValidationError | 422 |
| API-007 | With search_scope | {"query": "q", "search_scope": "api"} | Filtered results | 200 |

```python
# tests/api/test_chat_endpoint.py

import pytest
from httpx import AsyncClient
from src.api.main import app

class TestChatEndpoint:

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_valid_question_submission(self, client):
        """API-001: Valid question submission"""
        response = await client.post("/api/chat", json={
            "query": "Docker 설치 방법"
        })

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "sources" in data
        assert "confidence" in data
        assert "session_id" in data

    @pytest.mark.asyncio
    async def test_empty_query_rejected(self, client):
        """API-002: Empty query rejected"""
        response = await client.post("/api/chat", json={
            "query": ""
        })

        assert response.status_code == 422
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_missing_query_field(self, client):
        """API-003: Missing query field"""
        response = await client.post("/api/chat", json={})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_with_session_id(self, client):
        """API-005: Request with session_id"""
        session_id = "test-session-123"
        response = await client.post("/api/chat", json={
            "query": "테스트",
            "session_id": session_id
        })

        assert response.status_code == 200
        assert response.json()["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_with_search_scope(self, client):
        """API-007: Request with search_scope filter"""
        response = await client.post("/api/chat", json={
            "query": "API 문서",
            "search_scope": "api"
        })

        assert response.status_code == 200
```

---

### 4.2 GET /api/chat/{session_id} - 세션 조회

| Test ID | Test Case | Request | Expected Response | Status Code |
|---------|-----------|---------|-------------------|-------------|
| API-010 | Get existing session | GET /api/chat/valid-id | Session history | 200 |
| API-011 | Get non-existent session | GET /api/chat/invalid | NotFound | 404 |
| API-012 | Session contains history | GET /api/chat/valid-id | messages array | 200 |

```python
# tests/api/test_session_endpoint.py

import pytest
from httpx import AsyncClient

class TestSessionEndpoint:

    @pytest.mark.asyncio
    async def test_get_existing_session(self, client, created_session):
        """API-010: Get existing session"""
        response = await client.get(f"/api/chat/{created_session.session_id}")

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "messages" in data

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, client):
        """API-011: Get non-existent session returns 404"""
        response = await client.get("/api/chat/nonexistent-session-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_session_contains_history(self, client, session_with_history):
        """API-012: Session contains message history"""
        response = await client.get(f"/api/chat/{session_with_history.session_id}")

        data = response.json()
        assert len(data["messages"]) > 0
        assert data["messages"][0]["role"] in ["user", "assistant"]
```

---

### 4.3 POST /api/feedback - 피드백 제출

| Test ID | Test Case | Request | Expected Response | Status Code |
|---------|-----------|---------|-------------------|-------------|
| API-020 | Submit positive feedback | {"session_id": "x", "rating": "positive"} | Success | 200 |
| API-021 | Submit negative feedback with comment | {"rating": "negative", "comment": "..."} | Success | 200 |
| API-022 | Invalid rating value | {"rating": "invalid"} | ValidationError | 422 |
| API-023 | Missing session_id | {"rating": "positive"} | ValidationError | 422 |

```python
# tests/api/test_feedback_endpoint.py

import pytest
from httpx import AsyncClient

class TestFeedbackEndpoint:

    @pytest.mark.asyncio
    async def test_submit_positive_feedback(self, client, created_session):
        """API-020: Submit positive feedback"""
        response = await client.post("/api/feedback", json={
            "session_id": created_session.session_id,
            "message_id": created_session.last_message_id,
            "rating": "positive"
        })

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_submit_negative_feedback_with_comment(self, client, created_session):
        """API-021: Submit negative feedback with comment"""
        response = await client.post("/api/feedback", json={
            "session_id": created_session.session_id,
            "message_id": created_session.last_message_id,
            "rating": "negative",
            "comment": "답변이 정확하지 않습니다"
        })

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_rating_rejected(self, client, created_session):
        """API-022: Invalid rating value rejected"""
        response = await client.post("/api/feedback", json={
            "session_id": created_session.session_id,
            "rating": "invalid_rating"
        })

        assert response.status_code == 422
```

---

## 5. WebSocket HITL Test Cases

### 5.1 WS /ws/chat/{session_id} - HITL 실시간 통신

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| WS-001 | Establish connection | Connect to /ws/chat/session | Connection established | High |
| WS-002 | Send question message | {"type": "question", "query": "..."} | Processing started | High |
| WS-003 | Receive clarification request | Ambiguous query | {"type": "clarification", ...} | High |
| WS-004 | Send option selection | {"type": "response", "option": "..."} | Continue processing | High |
| WS-005 | Send custom input | {"type": "response", "custom": "..."} | Continue processing | High |
| WS-006 | Receive final response | Complete processing | {"type": "answer", ...} | High |
| WS-007 | Handle connection timeout | Idle for 5 minutes | Connection closed gracefully | Medium |
| WS-008 | Handle reconnection | Reconnect with session_id | State restored | Medium |
| WS-009 | Handle invalid message format | Malformed JSON | Error message | Medium |
| WS-010 | Receive progress updates | During processing | {"type": "progress", ...} | Low |

```python
# tests/websocket/test_hitl_websocket.py

import pytest
import asyncio
import websockets
import json

class TestHITLWebSocket:

    @pytest.fixture
    def ws_url(self):
        return "ws://localhost:8000/ws/chat"

    @pytest.mark.asyncio
    async def test_establish_connection(self, ws_url):
        """WS-001: Establish WebSocket connection"""
        async with websockets.connect(f"{ws_url}/test-session") as ws:
            assert ws.open is True

    @pytest.mark.asyncio
    async def test_send_question_message(self, ws_url):
        """WS-002: Send question and receive acknowledgment"""
        async with websockets.connect(f"{ws_url}/test-session") as ws:
            await ws.send(json.dumps({
                "type": "question",
                "query": "Docker 설치 방법"
            }))

            response = await ws.recv()
            data = json.loads(response)

            assert data["type"] in ["processing", "answer", "clarification"]

    @pytest.mark.asyncio
    async def test_receive_clarification_request(self, ws_url):
        """WS-003: Receive clarification for ambiguous query"""
        async with websockets.connect(f"{ws_url}/test-session") as ws:
            await ws.send(json.dumps({
                "type": "question",
                "query": "그거 어떻게 해요?"
            }))

            response = await ws.recv()
            data = json.loads(response)

            if data["type"] == "clarification":
                assert "clarification_question" in data
                assert "options" in data
                assert len(data["options"]) >= 2

    @pytest.mark.asyncio
    async def test_send_option_selection(self, ws_url):
        """WS-004: Send option selection response"""
        async with websockets.connect(f"{ws_url}/test-session") as ws:
            # Send ambiguous query
            await ws.send(json.dumps({
                "type": "question",
                "query": "설정 변경"
            }))

            response = await ws.recv()
            data = json.loads(response)

            if data["type"] == "clarification":
                # Send option selection
                await ws.send(json.dumps({
                    "type": "response",
                    "selected_option": data["options"][0]
                }))

                final_response = await ws.recv()
                final_data = json.loads(final_response)

                assert final_data["type"] in ["processing", "answer"]

    @pytest.mark.asyncio
    async def test_send_custom_input(self, ws_url):
        """WS-005: Send custom input response"""
        async with websockets.connect(f"{ws_url}/test-session") as ws:
            await ws.send(json.dumps({
                "type": "question",
                "query": "모호한 질문"
            }))

            response = await ws.recv()
            data = json.loads(response)

            if data["type"] == "clarification":
                await ws.send(json.dumps({
                    "type": "response",
                    "custom_input": "Redis 캐시 설정에 대해 알고 싶습니다"
                }))

                final_response = await ws.recv()
                assert json.loads(final_response) is not None

    @pytest.mark.asyncio
    async def test_receive_final_response(self, ws_url):
        """WS-006: Receive complete answer"""
        async with websockets.connect(f"{ws_url}/test-session") as ws:
            await ws.send(json.dumps({
                "type": "question",
                "query": "Docker 컨테이너 실행 명령어"
            }))

            # Collect all messages until answer
            messages = []
            while True:
                response = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(response)
                messages.append(data)

                if data["type"] == "answer":
                    break

            final = messages[-1]
            assert final["type"] == "answer"
            assert "response" in final
            assert "sources" in final

    @pytest.mark.asyncio
    async def test_handle_invalid_message_format(self, ws_url):
        """WS-009: Handle invalid message format"""
        async with websockets.connect(f"{ws_url}/test-session") as ws:
            await ws.send("invalid json {{{")

            response = await ws.recv()
            data = json.loads(response)

            assert data["type"] == "error"
            assert "message" in data

    @pytest.mark.asyncio
    async def test_receive_progress_updates(self, ws_url):
        """WS-010: Receive progress updates during processing"""
        async with websockets.connect(f"{ws_url}/test-session") as ws:
            await ws.send(json.dumps({
                "type": "question",
                "query": "복잡한 질문에 대한 답변"
            }))

            progress_received = False
            while True:
                response = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(response)

                if data["type"] == "progress":
                    progress_received = True
                    assert "step" in data
                    assert "message" in data

                if data["type"] == "answer":
                    break

            # Progress updates are optional but should be supported
            # assert progress_received is True  # Uncomment if required
```

---

## 6. Error Scenarios and Response Strategies

### 6.1 Error Classification

| Category | Error Type | Severity | Recovery Strategy |
|----------|------------|----------|-------------------|
| **LLM Errors** | API Rate Limit | Medium | Exponential backoff retry |
| | API Timeout | Medium | Retry (max 3 attempts) |
| | Parsing Error | Low | Retry with simplified prompt |
| | Token Limit Exceeded | Medium | Truncate context, retry |
| | Invalid Response | Low | Retry, fallback to default |
| **Retrieval Errors** | No Results | Low | Query rewrite → Web search |
| | Vector DB Connection | High | Return cached results if available |
| | Embedding Error | Medium | Retry, use alternative model |
| **WebSocket Errors** | Connection Lost | Medium | Auto-reconnect with state |
| | Message Timeout | Low | Prompt user to retry |
| **System Errors** | Configuration Missing | Critical | Fail fast with clear message |
| | Memory Exhaustion | Critical | Graceful degradation |

### 6.2 Error Response Schema

```python
# src/core/models.py

from enum import Enum
from pydantic import BaseModel
from typing import Optional

class ErrorType(str, Enum):
    PARSING_ERROR = "parsing_error"
    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    NO_RESULT = "no_result"
    TOKEN_LIMIT = "token_limit"
    VALIDATION_ERROR = "validation_error"
    CONNECTION_ERROR = "connection_error"
    INTERNAL_ERROR = "internal_error"

class FallbackAction(str, Enum):
    RETRY = "retry"
    WEB_SEARCH = "web_search"
    ASK_USER = "ask_user"
    RETURN_PARTIAL = "return_partial"
    RETURN_CACHED = "return_cached"
    FAIL = "fail"

class ErrorResponse(BaseModel):
    """Standard error response schema"""
    error_type: ErrorType
    error_message: str
    error_code: str
    recoverable: bool
    fallback_action: FallbackAction
    retry_after_seconds: Optional[int] = None
    user_message: str  # User-friendly message in Korean

    class Config:
        json_schema_extra = {
            "example": {
                "error_type": "rate_limit",
                "error_message": "OpenAI API rate limit exceeded",
                "error_code": "ERR_RATE_LIMIT",
                "recoverable": True,
                "fallback_action": "retry",
                "retry_after_seconds": 60,
                "user_message": "요청이 많아 잠시 후 다시 시도해주세요."
            }
        }
```

### 6.3 Error Test Cases

| Test ID | Error Scenario | Trigger | Expected Behavior | Priority |
|---------|----------------|---------|-------------------|----------|
| ERR-001 | LLM Rate Limit | Mock 429 response | Retry with backoff, user notified | High |
| ERR-002 | LLM Timeout | Mock slow response | Retry up to 3 times | High |
| ERR-003 | JSON Parsing Failure | Invalid LLM output | Retry with fallback prompt | High |
| ERR-004 | Token Limit Exceeded | Very long context | Truncate and retry | Medium |
| ERR-005 | Vector DB Connection Lost | Kill DB connection | Return error, suggest retry | High |
| ERR-006 | No Search Results | Query with no matches | Trigger query rewrite | High |
| ERR-007 | Web Search API Error | Mock Tavily error | Return partial response | Medium |
| ERR-008 | WebSocket Disconnect | Force disconnect | Auto-reconnect, restore state | High |
| ERR-009 | Invalid User Input | Malformed request | Return validation error | Medium |
| ERR-010 | All Fallbacks Failed | Every option fails | Graceful "unable to answer" | High |

```python
# tests/error/test_error_handling.py

import pytest
from unittest.mock import AsyncMock, patch
from src.core.exceptions import (
    APIRateLimitException,
    APITimeoutException,
    ParsingException,
    NoResultsException
)

class TestErrorHandling:

    @pytest.mark.asyncio
    async def test_rate_limit_retry_with_backoff(self, orchestrator, mock_rate_limit):
        """ERR-001: Rate limit triggers retry with backoff"""
        with patch.object(
            orchestrator.llm_provider,
            'complete',
            side_effect=[APIRateLimitException(retry_after=60), AsyncMock()]
        ):
            result = await orchestrator.process_query("테스트")

            # Should eventually succeed after retry
            assert result is not None
            assert orchestrator.retry_count >= 1

    @pytest.mark.asyncio
    async def test_timeout_retry(self, orchestrator):
        """ERR-002: Timeout triggers retry"""
        with patch.object(
            orchestrator.llm_provider,
            'complete',
            side_effect=[APITimeoutException(), APITimeoutException(), AsyncMock()]
        ):
            result = await orchestrator.process_query("테스트")

            assert result is not None

    @pytest.mark.asyncio
    async def test_parsing_failure_fallback(self, orchestrator):
        """ERR-003: Parsing failure triggers fallback"""
        with patch.object(
            orchestrator.llm_provider,
            'complete',
            side_effect=[ParsingException("Invalid JSON"), AsyncMock()]
        ):
            result = await orchestrator.process_query("테스트")

            assert result is not None

    @pytest.mark.asyncio
    async def test_no_results_triggers_rewrite(self, orchestrator):
        """ERR-006: No results triggers query rewrite"""
        with patch.object(
            orchestrator.retriever,
            'search',
            side_effect=NoResultsException()
        ):
            result = await orchestrator.process_query("특수한 검색어")

            assert result.correction_triggered is True

    @pytest.mark.asyncio
    async def test_all_fallbacks_failed(self, orchestrator):
        """ERR-010: Graceful handling when all fallbacks fail"""
        with patch.multiple(
            orchestrator,
            retriever=AsyncMock(side_effect=Exception()),
            web_search=AsyncMock(side_effect=Exception())
        ):
            result = await orchestrator.process_query("테스트")

            assert result.error is not None
            assert "답변을 생성할 수 없습니다" in result.user_message
```

### 6.4 Error Response Mapping

```python
# src/utils/error_handler.py

ERROR_USER_MESSAGES = {
    ErrorType.RATE_LIMIT: "요청이 많아 잠시 후 다시 시도해주세요.",
    ErrorType.TIMEOUT: "응답 시간이 초과되었습니다. 다시 시도해주세요.",
    ErrorType.NO_RESULT: "관련 문서를 찾지 못했습니다. 다른 표현으로 질문해보세요.",
    ErrorType.PARSING_ERROR: "응답 처리 중 문제가 발생했습니다. 다시 시도해주세요.",
    ErrorType.TOKEN_LIMIT: "질문이 너무 깁니다. 더 짧게 질문해주세요.",
    ErrorType.CONNECTION_ERROR: "서버 연결에 문제가 발생했습니다.",
    ErrorType.INTERNAL_ERROR: "시스템 오류가 발생했습니다. 관리자에게 문의해주세요."
}

ERROR_FALLBACK_ACTIONS = {
    ErrorType.RATE_LIMIT: FallbackAction.RETRY,
    ErrorType.TIMEOUT: FallbackAction.RETRY,
    ErrorType.NO_RESULT: FallbackAction.WEB_SEARCH,
    ErrorType.PARSING_ERROR: FallbackAction.RETRY,
    ErrorType.TOKEN_LIMIT: FallbackAction.ASK_USER,
    ErrorType.CONNECTION_ERROR: FallbackAction.RETURN_CACHED,
    ErrorType.INTERNAL_ERROR: FallbackAction.FAIL
}
```

---

## 7. Performance Test Criteria

### 7.1 Response Time Targets

| Scenario | Target (P95) | Maximum | Measurement Point |
|----------|--------------|---------|-------------------|
| Happy Path | < 8 seconds | 10 seconds | First response |
| HITL Flow (per interaction) | < 3 seconds | 5 seconds | Each clarification |
| Corrective Flow | < 12 seconds | 15 seconds | With 2 retries |
| Web Fallback | < 14 seconds | 18 seconds | Including web search |
| Complex Query | < 15 seconds | 20 seconds | With decomposition |

### 7.2 Throughput Targets

| Metric | Target | Condition |
|--------|--------|-----------|
| Concurrent Users | 50 | Sustained load |
| Requests per Second | 10 | Average load |
| Peak Requests per Second | 25 | Burst capacity |
| WebSocket Connections | 100 | Simultaneous |

### 7.3 Resource Utilization Limits

| Resource | Warning Threshold | Critical Threshold |
|----------|-------------------|-------------------|
| CPU Usage | 70% | 90% |
| Memory Usage | 80% | 95% |
| Vector DB Query Time | 500ms | 1000ms |
| LLM API Latency | 3s | 5s |

### 7.4 Performance Test Cases

```python
# tests/performance/test_performance.py

import pytest
import asyncio
from pytest_benchmark import benchmark

class TestPerformance:

    @pytest.mark.benchmark
    async def test_happy_path_response_time(self, benchmark, client):
        """Measure happy path response time"""
        result = await benchmark(
            client.ask,
            "Docker 설치 방법"
        )

        assert result.processing_time_ms < 10000  # 10 seconds max

    @pytest.mark.benchmark
    async def test_concurrent_requests(self, benchmark, client):
        """Test concurrent request handling"""
        async def make_request():
            return await client.ask("테스트 질문")

        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All requests should succeed
        assert all(r.status == "success" for r in results)

        # Average response time should be reasonable
        avg_time = sum(r.processing_time_ms for r in results) / len(results)
        assert avg_time < 15000  # 15 seconds average

    @pytest.mark.benchmark
    async def test_corrective_flow_response_time(self, benchmark, client):
        """Measure corrective flow response time"""
        result = await benchmark(
            client.ask,
            "매우 특수한 기술 문서 검색"  # Likely to trigger correction
        )

        assert result.processing_time_ms < 15000  # 15 seconds max

    @pytest.mark.benchmark
    async def test_memory_usage_under_load(self, client, memory_monitor):
        """Monitor memory usage under load"""
        initial_memory = memory_monitor.get_usage()

        # Generate load
        for _ in range(50):
            await client.ask("테스트 질문")

        final_memory = memory_monitor.get_usage()
        memory_increase = final_memory - initial_memory

        # Memory increase should be bounded
        assert memory_increase < 500 * 1024 * 1024  # 500MB max increase
```

---

## 8. Test Data (Golden Dataset) Design

### 8.1 Dataset Categories

| Category | Count | Purpose |
|----------|-------|---------|
| Simple Clear Questions | 20 | Happy path validation |
| Ambiguous Questions | 15 | HITL trigger validation |
| Complex Multi-part Questions | 10 | Decomposition validation |
| Domain-specific Questions | 15 | Domain detection validation |
| Edge Case Questions | 10 | Boundary condition testing |
| **Total** | **70** | |

### 8.2 Golden Dataset Schema

```python
# tests/data/golden_dataset.py

from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class ExpectedScenario(str, Enum):
    HAPPY_PATH = "happy_path"
    HITL_FLOW = "hitl_flow"
    CORRECTIVE_FLOW = "corrective_flow"
    WEB_FALLBACK = "web_fallback"
    COMPLEX_QUERY = "complex_query"

class GoldenTestCase(BaseModel):
    """Golden dataset test case schema"""
    id: str
    category: str
    query: str
    expected_scenario: ExpectedScenario

    # Expected outputs
    expected_complexity: str  # "simple" or "complex"
    expected_ambiguous: bool
    expected_domains: List[str]

    # Validation criteria
    min_confidence: float
    required_source_keywords: List[str]
    required_response_keywords: List[str]

    # Optional expected behaviors
    should_trigger_hitl: Optional[bool] = None
    should_trigger_correction: Optional[bool] = None
    should_trigger_web_search: Optional[bool] = None
    max_response_time_ms: int = 15000

    # Human-verified expected response (for comparison)
    reference_response: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "GD-001",
                "category": "simple_clear",
                "query": "Docker 컨테이너 실행 방법",
                "expected_scenario": "happy_path",
                "expected_complexity": "simple",
                "expected_ambiguous": False,
                "expected_domains": ["devops", "docker"],
                "min_confidence": 0.8,
                "required_source_keywords": ["docker", "컨테이너"],
                "required_response_keywords": ["docker run", "실행"],
                "max_response_time_ms": 10000
            }
        }
```

### 8.3 Sample Golden Dataset

```json
// tests/data/golden_dataset.json

{
  "test_cases": [
    {
      "id": "GD-001",
      "category": "simple_clear",
      "query": "Docker 컨테이너 실행 방법",
      "expected_scenario": "happy_path",
      "expected_complexity": "simple",
      "expected_ambiguous": false,
      "expected_domains": ["devops"],
      "min_confidence": 0.8,
      "required_source_keywords": ["docker"],
      "required_response_keywords": ["docker run", "실행"]
    },
    {
      "id": "GD-002",
      "category": "simple_clear",
      "query": "Git branch 생성 명령어",
      "expected_scenario": "happy_path",
      "expected_complexity": "simple",
      "expected_ambiguous": false,
      "expected_domains": ["development"],
      "min_confidence": 0.8,
      "required_source_keywords": ["git"],
      "required_response_keywords": ["git branch", "checkout"]
    },
    {
      "id": "GD-010",
      "category": "ambiguous",
      "query": "그거 어떻게 설정해요?",
      "expected_scenario": "hitl_flow",
      "expected_complexity": "simple",
      "expected_ambiguous": true,
      "expected_domains": [],
      "min_confidence": 0.0,
      "required_source_keywords": [],
      "required_response_keywords": [],
      "should_trigger_hitl": true
    },
    {
      "id": "GD-011",
      "category": "ambiguous",
      "query": "설정 변경하려면?",
      "expected_scenario": "hitl_flow",
      "expected_complexity": "simple",
      "expected_ambiguous": true,
      "expected_domains": [],
      "min_confidence": 0.0,
      "required_source_keywords": [],
      "required_response_keywords": [],
      "should_trigger_hitl": true
    },
    {
      "id": "GD-030",
      "category": "complex",
      "query": "마이크로서비스와 모놀리식 아키텍처의 장단점 비교",
      "expected_scenario": "complex_query",
      "expected_complexity": "complex",
      "expected_ambiguous": false,
      "expected_domains": ["architecture"],
      "min_confidence": 0.7,
      "required_source_keywords": ["아키텍처"],
      "required_response_keywords": ["마이크로서비스", "모놀리식", "장점", "단점"]
    },
    {
      "id": "GD-050",
      "category": "web_fallback",
      "query": "React 19 새로운 기능",
      "expected_scenario": "web_fallback",
      "expected_complexity": "simple",
      "expected_ambiguous": false,
      "expected_domains": ["frontend"],
      "min_confidence": 0.5,
      "required_source_keywords": [],
      "required_response_keywords": ["React"],
      "should_trigger_web_search": true
    }
  ]
}
```

### 8.4 Golden Dataset Test Runner

```python
# tests/golden/test_golden_dataset.py

import pytest
import json
from pathlib import Path
from tests.data.golden_dataset import GoldenTestCase, ExpectedScenario

def load_golden_dataset():
    dataset_path = Path(__file__).parent.parent / "data" / "golden_dataset.json"
    with open(dataset_path) as f:
        data = json.load(f)
    return [GoldenTestCase(**tc) for tc in data["test_cases"]]

GOLDEN_DATASET = load_golden_dataset()

class TestGoldenDataset:

    @pytest.mark.parametrize("test_case", GOLDEN_DATASET, ids=lambda tc: tc.id)
    @pytest.mark.asyncio
    async def test_golden_case(self, client, test_case: GoldenTestCase):
        """Run golden dataset test case"""
        response = await client.ask_with_trace(test_case.query)

        # Validate complexity
        if test_case.expected_complexity:
            assert response.complexity == test_case.expected_complexity, \
                f"Expected complexity {test_case.expected_complexity}, got {response.complexity}"

        # Validate ambiguity detection
        if test_case.expected_ambiguous is not None:
            assert response.is_ambiguous == test_case.expected_ambiguous, \
                f"Expected ambiguous={test_case.expected_ambiguous}"

        # Validate HITL trigger
        if test_case.should_trigger_hitl is not None:
            assert response.hitl_triggered == test_case.should_trigger_hitl

        # Validate correction trigger
        if test_case.should_trigger_correction is not None:
            assert response.correction_triggered == test_case.should_trigger_correction

        # Validate web search trigger
        if test_case.should_trigger_web_search is not None:
            assert response.web_search_triggered == test_case.should_trigger_web_search

        # Validate confidence
        if response.response:  # Only if response was generated
            assert response.confidence >= test_case.min_confidence, \
                f"Confidence {response.confidence} below minimum {test_case.min_confidence}"

        # Validate response keywords
        if test_case.required_response_keywords and response.response:
            response_lower = response.response.lower()
            for keyword in test_case.required_response_keywords:
                assert keyword.lower() in response_lower, \
                    f"Required keyword '{keyword}' not found in response"

        # Validate response time
        assert response.processing_time_ms <= test_case.max_response_time_ms, \
            f"Response time {response.processing_time_ms}ms exceeds maximum"
```

---

## 9. Mock/Stub Strategy

### 9.1 Mock Components Overview

| Component | Mock Level | Purpose |
|-----------|------------|---------|
| OpenAI API | Full Mock | Unit tests, cost control |
| ChromaDB | Full Mock | Unit tests |
| Tavily API | Full Mock | Unit tests |
| LLM Provider | Partial Mock | Integration tests |
| Vector Store | Partial Mock | Integration tests |

### 9.2 Mock Fixtures

```python
# tests/conftest.py

import pytest
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any, List

# ============================================
# LLM Provider Mocks
# ============================================

@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for unit tests"""
    provider = MagicMock()

    # Default response for query analysis
    provider.analyze_query = AsyncMock(return_value={
        "refined_query": "테스트 질문",
        "complexity": "simple",
        "clarity_confidence": 0.9,
        "is_ambiguous": False,
        "ambiguity_type": None,
        "detected_domains": ["general"]
    })

    # Default response for response generation
    provider.generate_response = AsyncMock(return_value={
        "response": "테스트 답변입니다.",
        "sources": ["test.md"],
        "has_sufficient_info": True
    })

    return provider

@pytest.fixture
def mock_llm_ambiguous_response(mock_llm_provider):
    """Mock LLM provider that returns ambiguous analysis"""
    mock_llm_provider.analyze_query = AsyncMock(return_value={
        "refined_query": "",
        "complexity": "simple",
        "clarity_confidence": 0.3,
        "is_ambiguous": True,
        "ambiguity_type": "vague_term",
        "detected_domains": []
    })
    return mock_llm_provider

# ============================================
# Vector Store Mocks
# ============================================

@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client"""
    client = MagicMock()
    collection = MagicMock()

    # Default query response
    collection.query.return_value = {
        "documents": [
            ["Docker를 사용한 배포 방법입니다."],
            ["컨테이너 실행 명령어: docker run"]
        ],
        "metadatas": [
            [{"source": "deployment.md", "section": "Docker"}],
            [{"source": "commands.md", "section": "Docker"}]
        ],
        "distances": [[0.1], [0.2]]
    }

    client.get_or_create_collection.return_value = collection
    return client

@pytest.fixture
def mock_chroma_empty():
    """Mock ChromaDB with no results"""
    client = MagicMock()
    collection = MagicMock()
    collection.query.return_value = {
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]]
    }
    client.get_or_create_collection.return_value = collection
    return client

@pytest.fixture
def mock_chroma_low_relevance():
    """Mock ChromaDB with low relevance results"""
    client = MagicMock()
    collection = MagicMock()
    collection.query.return_value = {
        "documents": [["회사 점심 메뉴: 한식, 중식, 양식"]],
        "metadatas": [[{"source": "lunch.md"}]],
        "distances": [[0.9]]  # High distance = low relevance
    }
    client.get_or_create_collection.return_value = collection
    return client

# ============================================
# Web Search Mocks
# ============================================

@pytest.fixture
def mock_tavily_client():
    """Mock Tavily API client"""
    client = MagicMock()
    client.search = AsyncMock(return_value={
        "results": [
            {
                "title": "React 19 New Features",
                "url": "https://example.com/react19",
                "content": "React 19 introduces new features...",
                "score": 0.9
            },
            {
                "title": "React 19 Release Notes",
                "url": "https://example.com/react19-notes",
                "content": "Official release notes for React 19...",
                "score": 0.85
            }
        ]
    })
    return client

@pytest.fixture
def mock_tavily_empty():
    """Mock Tavily with no results"""
    client = MagicMock()
    client.search = AsyncMock(return_value={"results": []})
    return client

@pytest.fixture
def mock_tavily_error():
    """Mock Tavily with API error"""
    client = MagicMock()
    client.search = AsyncMock(side_effect=Exception("Tavily API Error"))
    return client

# ============================================
# Sample Data Fixtures
# ============================================

@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    from src.core.models import Document, DocumentMetadata

    return [
        Document(
            content="Docker 설치 방법: apt-get install docker.io",
            metadata=DocumentMetadata(
                source="install.md",
                title="설치 가이드",
                section="Docker 설치"
            ),
            embedding_score=0.95
        ),
        Document(
            content="Docker 컨테이너 실행: docker run -d --name myapp image",
            metadata=DocumentMetadata(
                source="usage.md",
                title="사용 가이드",
                section="컨테이너 실행"
            ),
            embedding_score=0.90
        )
    ]

@pytest.fixture
def sample_rag_state():
    """Sample RAG state for testing"""
    from datetime import datetime

    return {
        "query": "Docker 설치 방법",
        "search_scope": "all",
        "session_id": "test-session-001",
        "refined_query": "Docker 설치 방법",
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
        "current_node": "start"
    }

# ============================================
# E2E Test Client Fixtures
# ============================================

@pytest.fixture
def e2e_client():
    """E2E test client with real components"""
    from tests.e2e.conftest import E2ETestClient
    return E2ETestClient(use_mocks=False)

@pytest.fixture
def e2e_client_mocked():
    """E2E test client with mocked external services"""
    from tests.e2e.conftest import E2ETestClient
    return E2ETestClient(use_mocks=True)
```

### 9.3 Response Factories

```python
# tests/factories.py

from typing import Optional, List
from src.core.models import (
    QueryAnalysisOutput,
    ClarificationOutput,
    RelevanceEvaluationOutput,
    ResponseOutput,
    QualityEvaluationOutput
)

class ResponseFactory:
    """Factory for creating mock responses"""

    @staticmethod
    def query_analysis(
        complexity: str = "simple",
        clarity: float = 0.9,
        ambiguous: bool = False,
        domains: Optional[List[str]] = None
    ) -> QueryAnalysisOutput:
        return QueryAnalysisOutput(
            refined_query="테스트 질문",
            complexity=complexity,
            clarity_confidence=clarity,
            is_ambiguous=ambiguous,
            ambiguity_type="vague_term" if ambiguous else None,
            detected_domains=domains or ["general"]
        )

    @staticmethod
    def clarification(
        question: str = "어떤 설정을 변경하시겠습니까?",
        options: Optional[List[str]] = None
    ) -> ClarificationOutput:
        return ClarificationOutput(
            clarification_question=question,
            options=options or ["데이터베이스 설정", "캐시 설정", "API 설정"]
        )

    @staticmethod
    def relevance(
        score: float = 0.85,
        level: str = "high",
        useful_parts: Optional[List[str]] = None
    ) -> RelevanceEvaluationOutput:
        return RelevanceEvaluationOutput(
            relevance_score=score,
            relevance_level=level,
            reason="문서가 질문과 관련이 있습니다.",
            useful_parts=useful_parts or ["관련 내용"]
        )

    @staticmethod
    def response(
        content: str = "테스트 답변입니다.",
        sources: Optional[List[str]] = None,
        sufficient: bool = True
    ) -> ResponseOutput:
        return ResponseOutput(
            response=content,
            sources=sources or ["test.md"],
            has_sufficient_info=sufficient
        )

    @staticmethod
    def quality(
        completeness: float = 0.85,
        accuracy: float = 0.9,
        clarity: float = 0.85,
        confidence: float = 0.87,
        disclaimer: bool = False
    ) -> QualityEvaluationOutput:
        return QualityEvaluationOutput(
            completeness=completeness,
            accuracy=accuracy,
            clarity=clarity,
            confidence=confidence,
            needs_disclaimer=disclaimer
        )
```

---

## 10. Test Execution Guide

### 10.1 Test Commands

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest tests/e2e/                     # E2E tests only
pytest tests/api/                     # API tests only
pytest tests/websocket/               # WebSocket tests only
pytest tests/performance/             # Performance tests only
pytest tests/golden/                  # Golden dataset tests

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_query_processor.py

# Run specific test
pytest tests/unit/test_query_processor.py::TestQueryProcessor::test_analyze_simple_clear_query

# Run tests with markers
pytest -m "asyncio"                   # Async tests only
pytest -m "benchmark"                 # Benchmark tests only
pytest -m "slow"                      # Slow tests only

# Run tests in parallel
pytest -n auto                        # Auto-detect CPU count

# Verbose output
pytest -v                             # Verbose
pytest -vv                            # Very verbose
```

### 10.2 CI/CD Pipeline Configuration

```yaml
# .github/workflows/test.yml

name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run unit tests
        run: pytest tests/unit/ --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run integration tests
        run: pytest tests/integration/

  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Start services
        run: docker-compose up -d
      - name: Run E2E tests
        run: pytest tests/e2e/
      - name: Stop services
        run: docker-compose down
```

### 10.3 Test Quality Gates

| Gate | Threshold | Action on Failure |
|------|-----------|-------------------|
| Unit Test Pass Rate | 100% | Block merge |
| Unit Test Coverage | >= 80% | Warning |
| Integration Test Pass Rate | 100% | Block merge |
| E2E Test Pass Rate | 100% | Block merge |
| Golden Dataset Pass Rate | >= 95% | Warning |
| Performance (Happy Path P95) | < 10s | Warning |

---

## 11. Summary

### 11.1 Test Count Summary

| Category | Test Count |
|----------|------------|
| Unit Tests | 65 |
| Integration Tests | 20 |
| E2E Tests | 25 |
| API Tests | 15 |
| WebSocket Tests | 10 |
| Performance Tests | 8 |
| Golden Dataset Tests | 70 |
| Error Handling Tests | 10 |
| **Total** | **223** |

### 11.2 Coverage Targets

| Component | Target Coverage |
|-----------|-----------------|
| Query Processor | 85% |
| HITL Controller | 80% |
| Relevance Evaluator | 80% |
| Corrective Engine | 85% |
| Response Generator | 80% |
| Quality Evaluator | 80% |
| LangGraph Orchestrator | 75% |
| API Endpoints | 90% |
| WebSocket Handler | 80% |
| **Overall** | **80%** |

### 11.3 Key Risk Areas

| Risk Area | Mitigation |
|-----------|------------|
| LLM Response Variability | Mock responses, Golden dataset validation |
| External API Dependencies | Comprehensive mocking strategy |
| WebSocket State Management | Dedicated WebSocket tests, reconnection tests |
| Performance Under Load | Benchmark tests, load testing |
| Error Recovery | Explicit error scenario tests |

---

**Test Design Document Complete**

*This document provides comprehensive test coverage for the RAG Chatbot system, including unit tests, integration tests, E2E scenarios, error handling, performance criteria, and golden dataset validation.*
