# RAG 챗봇 시스템 구현 가능성 보고서

**프로젝트명:** 사내 문서 검색용 RAG 챗봇
**작성일:** 2025-12-11
**작성자:** Requirement Analyst Agent
**문서 버전:** 1.0

---

## 1. 개요

### 1.1 프로젝트 목적
꿀스테이를 포함한 여러 서비스에서 프로젝트 히스토리 부재 및 방대한 문서 자료로 인해 개발 외 시간이 과도하게 소요되는 문제를 해결하기 위한 RAG 기반 챗봇 시스템 구축

### 1.2 분석 범위
- 기술적 구현 가능성 평가
- LangGraph 기반 구현의 적합성
- 컴포넌트 간 의존성 검토
- 잠재적 리스크 및 도전 과제 식별
- 개선 제안 사항

---

## 2. 기술 스택 구현 가능성 평가

### 2.1 핵심 기술 스택

| 기술 | 버전/상태 | 성숙도 | 구현 가능성 |
|------|----------|--------|------------|
| LangGraph | 안정 릴리스 | ★★★★☆ | **높음** |
| ChromaDB | 안정 릴리스 | ★★★★☆ | **높음** |
| OpenAI GPT-4o | Production | ★★★★★ | **높음** |
| Tavily API | Production | ★★★★☆ | **높음** |
| Streamlit | 안정 릴리스 | ★★★★★ | **높음** |

### 2.2 기술별 상세 분석

#### LangGraph
- **장점:** 상태 기반 워크플로우 관리에 최적화, 조건부 분기 지원 우수
- **적합성:** Corrective RAG의 반복 로직과 HITL 분기 처리에 매우 적합
- **주의점:** 러닝 커브 존재, 디버깅 복잡성

#### ChromaDB
- **장점:** 설치 용이, 메타데이터 필터링 지원, 로컬 실행 가능
- **적합성:** MVP 단계의 단일 컬렉션 구조에 적합
- **주의점:** 대용량 스케일 시 성능 검증 필요

#### OpenAI GPT-4o
- **장점:** 높은 품질, 안정적인 API, 추상화 레이어로 교체 가능 설계
- **적합성:** 질문 분석, 관련성 평가, 답변 생성 모두 커버
- **주의점:** API 비용, 레이턴시, Rate Limit 관리

---

## 3. 아키텍처 구현 가능성 분석

### 3.1 경량화 단일 에이전트 + Corrective RAG + HITL 구조

**평가: ✅ 구현 가능 (적절한 복잡도)**

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Orchestrator                         │
│                   (LangGraph 기반)                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Query     │→ │   HITL      │→ │     Agentic         │ │
│  │  Processor  │  │ Controller  │  │    Controller       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│         ↓                                    ↓              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Corrective RAG Engine                   │   │
│  │   검색 → 평가 → (재작성) → 재검색 (최대 2회)          │   │
│  └─────────────────────────────────────────────────────┘   │
│         ↓                                    ↓              │
│  ┌─────────────┐                    ┌─────────────────┐    │
│  │ Web Search  │   (Fallback)       │    Response     │    │
│  │   Agent     │ ←─────────────────→│   Generator     │    │
│  └─────────────┘                    └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 10개 컴포넌트 의존성 분석

| 컴포넌트 | 의존 대상 | 복잡도 | 구현 난이도 |
|----------|----------|--------|------------|
| RAG Orchestrator | 모든 컴포넌트 | 높음 | ★★★★☆ |
| Query Processor | LLM Provider | 중간 | ★★★☆☆ |
| HITL Controller | Orchestrator | 중간 | ★★★☆☆ |
| Agentic Controller | LLM Provider | 중간 | ★★★☆☆ |
| Corrective RAG Engine | Vector Store, LLM | 높음 | ★★★★☆ |
| Web Search Agent | Tavily API | 낮음 | ★★☆☆☆ |
| Response Generator | LLM Provider | 중간 | ★★★☆☆ |
| Vector Store Manager | ChromaDB | 중간 | ★★★☆☆ |
| LLM Provider | OpenAI API | 낮음 | ★★☆☆☆ |
| Config Manager | 없음 | 낮음 | ★☆☆☆☆ |

### 3.3 핵심 기능 구현 가능성

#### 질문 분석 (Query Analysis)
```
complexity: simple | complex → ✅ LLM 프롬프팅으로 구현 용이
clarity_confidence: 0.0~1.0 → ✅ LLM 출력 파싱으로 구현 가능
ambiguity_detection → ✅ 구조화된 출력으로 구현 가능
```
**평가:** 구현 가능 - LangChain의 StructuredOutput 활용 권장

#### Corrective RAG
```
하이브리드 관련성 평가 → ✅ 구현 가능 (임베딩 + LLM 이중 검증)
임계값 0.8 + 최소 2개 문서 → ✅ 명확한 기준, 구현 용이
쿼리 재작성 → ✅ LLM 프롬프팅으로 구현
최대 2회 재시도 → ✅ LangGraph 루프로 자연스럽게 구현
```
**평가:** 구현 가능 - LangGraph의 conditional_edges 활용

#### HITL (Human-in-the-Loop)
```
트리거 조건 (모호성, 검색 실패, 불완전) → ✅ 조건 분기로 구현
최대 연속 2회 제한 → ✅ State 카운터로 관리
피드백 수집 → ✅ Streamlit 위젯 활용
```
**평가:** 구현 가능 - interrupt_before 또는 커스텀 노드 활용

#### Web Search Fallback
```
내부 검색 2회 실패 후 Tavily 호출 → ✅ 조건부 분기로 구현
```
**평가:** 구현 용이

---

## 4. State Schema 검토

### 4.1 상태 구조 적절성 평가

**총평: ✅ 잘 설계됨**

```python
# 제안된 State 구조 (TypedDict 기반)
class RAGState(TypedDict):
    # Input
    query: str
    search_scope: str
    session_id: str

    # Query Analysis
    refined_query: str
    complexity: Literal["simple", "complex"]
    clarity_confidence: float
    is_ambiguous: bool
    ambiguity_type: Optional[str]
    detected_domains: List[str]

    # HITL
    clarification_needed: bool
    clarification_question: Optional[str]
    user_response: Optional[str]
    interaction_count: int

    # Retrieval
    retrieved_docs: List[Document]
    relevance_scores: List[float]
    avg_relevance: float
    high_relevance_count: int
    retrieval_source: Literal["vector", "web", "hybrid"]

    # Correction
    retry_count: int
    rewritten_queries: List[str]
    correction_triggered: bool

    # Web Search
    web_search_triggered: bool
    web_results: List[Document]
    web_confidence: float

    # Response
    generated_response: str
    response_confidence: float
    sources: List[str]
    needs_disclaimer: bool

    # Metadata
    start_time: datetime
    end_time: Optional[datetime]
    total_llm_calls: int
    error_log: List[str]
```

### 4.2 개선 제안

1. **Optional 필드 명시:** 초기 None 상태 필드들은 Optional로 명시 권장
2. **Enum 활용:** `complexity`, `retrieval_source` 등은 Enum으로 타입 안전성 확보
3. **불변성 고려:** 디버깅을 위해 상태 변경 히스토리 추적 기능 고려

---

## 5. 리스크 및 도전 과제

### 5.1 기술적 리스크

| 리스크 | 발생 가능성 | 영향도 | 완화 전략 |
|--------|------------|--------|----------|
| LLM 레이턴시로 인한 UX 저하 | 높음 | 중간 | 스트리밍 응답, 로딩 인디케이터 |
| 관련성 평가 정확도 미달 | 중간 | 높음 | 임계값 조정, 평가 로직 고도화 |
| 쿼리 재작성 무한 루프 | 낮음 | 높음 | max_retries=2로 이미 대응됨 |
| ChromaDB 성능 한계 | 낮음 | 중간 | 문서 수 모니터링, 필요시 마이그레이션 |
| API Rate Limit | 중간 | 중간 | 백오프 로직, 캐싱 적용 |

### 5.2 운영적 리스크

| 리스크 | 발생 가능성 | 영향도 | 완화 전략 |
|--------|------------|--------|----------|
| 문서 최신성 유지 | 높음 | 중간 | 정기 인덱싱 파이프라인 구축 |
| 사용자 기대치 불일치 | 중간 | 중간 | 명확한 기능 범위 안내, 피드백 반영 |
| 민감 정보 노출 | 낮음 | 높음 | 접근 권한 관리, 문서 분류 체계 |

### 5.3 주요 도전 과제

1. **관련성 평가의 정확도**
   - 하이브리드 평가(임베딩 + LLM)의 적절한 가중치 설정
   - 도메인별 관련성 기준 차이 처리

2. **HITL 인터랙션 품질**
   - 유용한 명확화 질문 생성
   - 사용자 피로도 최소화 (최대 2회 제한은 적절)

3. **컨텍스트 윈도우 관리**
   - 검색된 문서가 많을 경우 토큰 제한 관리
   - 적절한 청킹 전략 필요

---

## 6. 종합 평가

### 6.1 구현 가능성 점수

| 평가 항목 | 점수 | 비고 |
|----------|------|------|
| 기술 스택 성숙도 | 9/10 | 모든 기술이 Production Ready |
| 아키텍처 적절성 | 8/10 | 경량화 설계가 MVP에 적합 |
| 컴포넌트 의존성 | 8/10 | 명확한 책임 분리 |
| State 설계 | 9/10 | 포괄적이고 체계적 |
| 리스크 관리 | 8/10 | 주요 리스크 대응 방안 존재 |
| **종합** | **8.4/10** | **구현 적극 권장** |

### 6.2 최종 결론

**✅ 구현 가능 - 적극 권장**

제안된 RAG 챗봇 시스템은 기술적으로 충분히 구현 가능하며, 설계가 잘 되어 있습니다.

#### 강점
- LangGraph 기반 설계가 복잡한 RAG 워크플로우에 매우 적합
- Corrective RAG + HITL 조합이 답변 품질 향상에 효과적
- MVP 범위가 적절하게 정의됨 (Phase 분리)
- 상태 스키마가 포괄적이고 확장 가능

#### 개선 권장 사항
1. **응답 스트리밍:** UX 개선을 위해 LLM 응답 스트리밍 구현 권장
2. **캐싱 레이어:** 동일/유사 질문에 대한 캐싱으로 비용 및 레이턴시 절감
3. **모니터링:** LangSmith 또는 유사 도구로 파이프라인 추적 구현
4. **테스트 데이터셋:** 관련성 평가 정확도 측정을 위한 골든 데이터셋 구축

---

## 7. 다음 단계 제안

### Phase 1: MVP 구현 권장 순서

```
1. Config Manager + LLM Provider (기반 인프라)
2. Vector Store Manager (ChromaDB 연동)
3. Query Processor (질문 분석)
4. Corrective RAG Engine (핵심 검색 로직)
5. Response Generator (답변 생성)
6. RAG Orchestrator (LangGraph 워크플로우)
7. HITL Controller (사용자 상호작용)
8. Web Search Agent (Fallback)
9. Streamlit UI
10. 통합 테스트 및 최적화
```

---

**보고서 작성 완료**

*본 보고서는 제공된 설계 문서를 기반으로 작성되었으며, 실제 구현 시 추가적인 기술 검토가 필요할 수 있습니다.*
