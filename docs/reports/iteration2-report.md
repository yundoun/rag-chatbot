# Iteration 2: Corrective RAG Engine - 완료 보고서

**Project:** RAG Chatbot
**Iteration:** 2 - Corrective RAG Engine
**Date:** 2025-12-11
**Status:** ✅ 완료

---

## 1. 개요

Iteration 2에서는 관련성 평가 및 교정 검색 루프를 구현하여 답변 품질을 향상시켰습니다.

### 목표
- 검색된 문서의 관련성 평가
- 관련성 낮을 때 쿼리 재작성 및 재검색
- LangGraph 기반 상태 머신으로 플로우 조율
- 응답 품질 평가 및 면책 문구 결정

---

## 2. 완료된 태스크

### Task 2.1: Relevance Evaluator ✅
- `src/rag/relevance_evaluator.py` - 하이브리드 관련성 평가 (임베딩 + LLM)
- `src/llm/prompts/relevance.py` - 관련성 평가 프롬프트

**핵심 기능:**
- 임베딩 유사도로 1차 필터링 (threshold: 0.5)
- LLM으로 정밀 평가 (0.0-1.0 점수)
- relevance_level: high(>=0.8), medium(0.5-0.8), low(<0.5)
- useful_parts 추출

### Task 2.2: Query Rewriter ✅
- `src/rag/query_rewriter.py` - 쿼리 재작성 엔진
- `src/llm/prompts/rewrite.py` - 재작성 프롬프트

**핵심 기능:**
- 4가지 전략: synonym_expansion, context_addition, generalize, specify
- 이전 시도 쿼리와 중복 방지
- 재시도 횟수에 따른 전략 자동 선택

### Task 2.3: Corrective RAG Engine ✅
- `src/rag/corrective_engine.py` - 교정 루프 오케스트레이션

**핵심 로직:**
- high_relevance_count >= 2 → 충분
- retry_count < 2 → 쿼리 재작성 후 재검색
- retry_count >= 2 → web_search 트리거
- CorrectionAction enum (PROCEED, REWRITE, WEB_SEARCH, FAIL)

### Task 2.4: LangGraph Orchestrator ✅
- `src/core/orchestrator.py` - LangGraph 워크플로우 오케스트레이터
- `src/core/nodes.py` - 개별 노드 구현
- `src/core/edges.py` - 라우팅 로직

**LangGraph 노드:**
- analyze_query → retrieve → evaluate_relevance
- rewrite_query (조건부)
- web_search (폴백)
- generate_response → evaluate_quality

### Task 2.5: Response Quality Evaluator ✅
- `src/rag/quality_evaluator.py` - 품질 평가기
- `src/llm/prompts/quality.py` - 품질 평가 프롬프트

**평가 기준:**
- completeness (0.4 가중치)
- accuracy (0.4 가중치)
- clarity (0.2 가중치)
- confidence < 0.8 → needs_disclaimer: true

### Task 2.6: Update API for Corrective Flow ✅
- `src/api/routes/chat.py` - LangGraph orchestrator 통합
- `/api/chat` - 전체 Corrective RAG 파이프라인
- `/api/chat/simple` - 기본 RAG (비교/폴백용)

### Task 2.7: React Loading States ✅
- `frontend/src/components/LoadingIndicator.jsx` - 로딩 인디케이터
- `frontend/src/components/ProcessingSteps.jsx` - 처리 단계 표시
- `frontend/src/components/ChatContainer.jsx` - 업데이트

**처리 단계:**
1. 질문 분석 (🔍)
2. 문서 검색 (📚)
3. 관련성 평가 (⚖️)
4. 답변 생성 (✍️)

### Task 2.8: Corrective RAG Tests ✅
- `tests/unit/test_relevance_evaluator.py` - 관련성 평가 테스트
- `tests/unit/test_corrective_engine.py` - 교정 엔진 테스트
- `tests/integration/test_corrective_flow.py` - 통합 테스트

---

## 3. 새로 추가된 파일

```
src/
├── core/
│   ├── orchestrator.py      # NEW - LangGraph orchestrator
│   ├── nodes.py             # NEW - Workflow nodes
│   └── edges.py             # NEW - Routing logic
├── rag/
│   ├── relevance_evaluator.py   # NEW
│   ├── query_rewriter.py        # NEW
│   ├── corrective_engine.py     # NEW
│   └── quality_evaluator.py     # NEW
├── llm/prompts/
│   ├── relevance.py         # NEW
│   ├── rewrite.py           # NEW
│   └── quality.py           # NEW
frontend/src/components/
├── LoadingIndicator.jsx     # NEW
└── ProcessingSteps.jsx      # NEW
tests/
├── unit/
│   ├── test_relevance_evaluator.py  # NEW
│   └── test_corrective_engine.py    # NEW
└── integration/
    └── test_corrective_flow.py      # NEW
```

---

## 4. 아키텍처 플로우

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Corrective RAG Flow                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User Query                                                         │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────────┐                                                   │
│  │analyze_query │ → complexity, clarity, domains                   │
│  └──────┬───────┘                                                   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │   retrieve   │ → vector similarity search                       │
│  └──────┬───────┘                                                   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────┐      ┌─────────────────┐                         │
│  │  evaluate    │──────│ sufficient?     │                         │
│  │  relevance   │      │ high_count >= 2 │                         │
│  └──────────────┘      └────────┬────────┘                         │
│                                 │                                   │
│              ┌──────────────────┼──────────────────┐               │
│              │ YES              │ NO               │               │
│              ▼                  ▼                  │               │
│      ┌──────────────┐   ┌──────────────┐         │               │
│      │   generate   │   │ retry < 2?   │         │               │
│      │   response   │   └──────┬───────┘         │               │
│      └──────────────┘          │                  │               │
│                         ┌──────┴──────┐          │               │
│                         │ YES         │ NO       │               │
│                         ▼             ▼          │               │
│                 ┌──────────────┐  ┌──────────┐  │               │
│                 │rewrite_query │  │web_search│──┘               │
│                 └──────┬───────┘  └────┬─────┘                   │
│                        │               │                          │
│                        └───────┬───────┘                          │
│                                │                                   │
│                                ▼                                   │
│                        ┌──────────────┐                           │
│                        │   generate   │                           │
│                        │   response   │                           │
│                        └──────┬───────┘                           │
│                               │                                    │
│                               ▼                                    │
│                        ┌──────────────┐                           │
│                        │  evaluate    │                           │
│                        │   quality    │ → confidence, disclaimer  │
│                        └──────────────┘                           │
│                                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. 검증 기준 충족 여부

| 기준 | 상태 | 구현 |
|------|------|------|
| 검색된 문서의 관련성이 평가됨 | ✅ | RelevanceEvaluator |
| 관련성 낮을 때 (< 0.8) 쿼리 재작성 수행 | ✅ | route_after_evaluation |
| 최대 2회 재시도 제한 적용 | ✅ | max_correction_retries=2 |
| 낮은 신뢰도 응답에 면책 문구 표시 | ✅ | QualityEvaluator.needs_disclaimer |
| 로딩 UI에 처리 단계 표시 | ✅ | ProcessingSteps 컴포넌트 |

---

## 6. 주요 설정값

| Parameter | Value | Description |
|-----------|-------|-------------|
| RELEVANCE_THRESHOLD | 0.8 | 충분한 관련성 기준 |
| MIN_HIGH_RELEVANCE_DOCS | 2 | 최소 높은 관련성 문서 수 |
| MAX_CORRECTION_RETRIES | 2 | 최대 재시도 횟수 |
| EMBEDDING_THRESHOLD | 0.5 | LLM 평가 전 임베딩 필터 |
| CONFIDENCE_THRESHOLD | 0.8 | 면책 문구 표시 기준 |

---

## 7. 테스트 커버리지

```
tests/unit/
├── test_relevance_evaluator.py  (8 test cases)
│   ├── test_evaluate_high_relevance
│   ├── test_evaluate_low_relevance
│   ├── test_score_to_level_mapping
│   ├── test_calculate_metrics
│   └── test_filter_relevant_documents
│
└── test_corrective_engine.py    (9 test cases)
    ├── test_should_correct_low_relevance
    ├── test_should_not_correct_sufficient
    ├── test_should_not_correct_max_retries
    ├── test_determine_action_*
    └── test_run_correction_loop_*

tests/integration/
└── test_corrective_flow.py      (10 test cases)
    ├── TestCorrectiveRAGFlow
    ├── TestCorrectiveEngineIntegration
    ├── TestQualityEvaluatorIntegration
    └── TestRouting
```

---

## 8. 다음 단계 (Iteration 3)

Iteration 3에서는 HITL & Web Search를 구현합니다:
- HITL Controller (명확화 질문 생성)
- Web Search Agent (Tavily 통합)
- Agentic Controller (복잡 쿼리 분해)
- WebSocket for HITL
- React HITL UI

---

**완료 일시:** 2025-12-11
**개발자:** Developer Agent
