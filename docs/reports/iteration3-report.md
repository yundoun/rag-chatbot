# Iteration 3: HITL & Web Search - 완료 보고서

**Project:** RAG Chatbot
**Iteration:** 3 - HITL & Web Search
**Date:** 2025-12-11
**Status:** ✅ 완료

---

## 1. 개요

Iteration 3에서는 Human-in-the-Loop (HITL) 명확화 대화 및 웹 검색 Fallback을 구현했습니다.

### 목표
- 모호한 질문에 대한 명확화 대화 트리거
- 사용자 선택지 제공 및 커스텀 입력 지원
- 내부 검색 실패 시 웹 검색 Fallback
- WebSocket 기반 실시간 HITL 통신
- 웹 검색 결과에 면책 문구 표시

---

## 2. 완료된 태스크

### Task 3.1: HITL Controller ✅
- `src/agents/hitl_controller.py` - HITL 로직 및 명확화 질문 생성
- `src/llm/prompts/clarification.py` - 명확화 프롬프트

**핵심 기능:**
- `should_clarify()`: clarity_confidence < 0.8 또는 is_ambiguous → 트리거
- `generate_clarification()`: ambiguity_type에 따른 질문 생성
- 2-5개 선택지 + '직접 입력' 옵션
- max_hitl_interactions = 2 제한
- `refine_query()`: 사용자 응답으로 쿼리 정제

### Task 3.2: Web Search Agent ✅
- `src/agents/web_search_agent.py` - Tavily API 통합
- `src/llm/prompts/web_integration.py` - 웹 검색 프롬프트

**핵심 기능:**
- Tavily API 연동
- 쿼리 최적화 (내부 용어 제거)
- 결과 관련성 필터링 (overall_score >= 0.3)
- 출처 신뢰도 평가 (trusted_domains)
- disclaimer_needed = true 자동 설정

### Task 3.3: Agentic Controller ✅
- `src/agents/agentic_controller.py` - 복잡 쿼리 분해
- `src/llm/prompts/decomposition.py` - 분해 프롬프트

**핵심 기능:**
- complexity == 'complex' → 분해 트리거
- sub_questions 생성 (2-5개)
- parallel_groups 정의
- synthesis_guide 제공
- 병렬 검색 실행

### Task 3.4: Update LangGraph Orchestrator ✅
- `src/core/orchestrator.py` - HITL 인터럽트 및 세션 관리
- `src/core/nodes.py` - HITL/웹검색 노드 추가
- `src/core/edges.py` - 라우팅 로직 확장

**새로운 노드:**
- `clarify_hitl` → 명확화 질문 생성
- `process_hitl_response` → 사용자 응답 처리
- `decompose_query` → 복잡 쿼리 분해
- `web_search` → Tavily 웹 검색

**라우팅 로직:**
```
route_after_analysis:
  - clarification_needed → clarify
  - complexity == complex → decompose
  - else → retrieve

route_after_evaluation:
  - sufficient relevance → generate
  - retry_count < 2 → rewrite
  - retry_count >= 2 → web_search
```

### Task 3.5: WebSocket for HITL ✅
- `src/api/websocket_manager.py` - 연결 관리
- `src/api/routes/websocket.py` - WebSocket 엔드포인트

**메시지 타입:**
- Client → Server: `question`, `clarification`
- Server → Client: `progress`, `clarification_request`, `response`, `error`

**엔드포인트:**
- `/ws/chat` - 새 세션
- `/ws/chat/{session_id}` - 기존 세션 재연결

### Task 3.6: React HITL UI ✅
- `frontend/src/components/ClarificationDialog.jsx` - 명확화 대화 UI
- `frontend/src/components/OptionButton.jsx` - 선택지 버튼
- `frontend/src/hooks/useWebSocket.js` - WebSocket 훅
- `frontend/src/components/ChatContainer.jsx` - 통합

**UI 기능:**
- 2-5개 선택지 버튼
- 직접 입력 옵션
- 실시간 WebSocket 통신
- 상태 관리 (pendingClarification)

### Task 3.7: Web Search Result Display ✅
- `frontend/src/components/WebSearchBanner.jsx` - 면책 배너
- `frontend/src/components/SourceList.jsx` - 출처 목록
- `frontend/src/components/MessageBubble.jsx` - 업데이트

**UI 기능:**
- 웹/내부 소스 구분 표시
- URL 링크 (새 탭)
- 신뢰도 배지
- 면책 문구 배너

### Task 3.8: HITL & Web Search Tests ✅
- `tests/unit/test_hitl_controller.py` - HITL 컨트롤러 테스트
- `tests/unit/test_web_search_agent.py` - 웹 검색 에이전트 테스트
- `tests/integration/test_hitl_flow.py` - HITL 플로우 통합 테스트
- `tests/integration/test_web_fallback.py` - 웹 Fallback 통합 테스트

---

## 3. 새로 추가된 파일

```
src/
├── agents/
│   ├── hitl_controller.py       # NEW
│   ├── web_search_agent.py      # NEW
│   └── agentic_controller.py    # NEW
├── api/
│   ├── websocket_manager.py     # NEW
│   └── routes/
│       └── websocket.py         # NEW
├── llm/prompts/
│   ├── clarification.py         # NEW
│   ├── web_integration.py       # NEW
│   └── decomposition.py         # NEW
frontend/src/
├── components/
│   ├── ClarificationDialog.jsx  # NEW
│   ├── OptionButton.jsx         # NEW
│   ├── WebSearchBanner.jsx      # NEW
│   └── SourceList.jsx           # NEW
├── hooks/
│   └── useWebSocket.js          # NEW
tests/
├── unit/
│   ├── test_hitl_controller.py  # NEW
│   └── test_web_search_agent.py # NEW
└── integration/
    ├── test_hitl_flow.py        # NEW
    └── test_web_fallback.py     # NEW
```

---

## 4. 아키텍처 플로우

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HITL & Web Search Flow                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User Query                                                         │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────────┐                                                   │
│  │analyze_query │                                                   │
│  └──────┬───────┘                                                   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────────────┐                          │
│  │         route_after_analysis          │                          │
│  │  clarification? │ complex? │ simple   │                          │
│  └────────┬────────┴────┬─────┴────┬─────┘                          │
│           │             │          │                                │
│           ▼             ▼          │                                │
│  ┌──────────────┐ ┌──────────────┐ │                                │
│  │ clarify_hitl │ │decompose_qry│ │                                │
│  └──────┬───────┘ └──────┬───────┘ │                                │
│         │                │          │                                │
│         ▼                │          │                                │
│  ┌──────────────┐       │          │                                │
│  │  [INTERRUPT] │       │          │                                │
│  │ Wait for     │       │          │                                │
│  │ user input   │       │          │                                │
│  └──────┬───────┘       │          │                                │
│         │ user_response │          │                                │
│         ▼               │          │                                │
│  ┌──────────────┐       │          │                                │
│  │process_hitl  │       │          │                                │
│  │  _response   │       │          │                                │
│  └──────┬───────┘       │          │                                │
│         │               │          │                                │
│         └───────────────┴──────────┘                                │
│                         │                                            │
│                         ▼                                            │
│                  ┌──────────────┐                                   │
│                  │   retrieve   │ ◄──────────────┐                  │
│                  └──────┬───────┘                │                  │
│                         │                         │                  │
│                         ▼                         │                  │
│                  ┌──────────────┐                │                  │
│                  │  evaluate    │                │                  │
│                  │  relevance   │                │                  │
│                  └──────┬───────┘                │                  │
│                         │                         │                  │
│       ┌─────────────────┼─────────────────┐     │                  │
│       │ sufficient      │ insufficient    │     │                  │
│       ▼                 ▼                 │     │                  │
│                 ┌──────────────┐          │     │                  │
│                 │ retry < 2?   │          │     │                  │
│                 └──────┬───────┘          │     │                  │
│              ┌─────────┴─────────┐        │     │                  │
│              │ YES               │ NO     │     │                  │
│              ▼                   ▼        │     │                  │
│       ┌──────────────┐   ┌──────────┐    │     │                  │
│       │rewrite_query │   │web_search│    │     │                  │
│       └──────┬───────┘   └────┬─────┘    │     │                  │
│              │                │           │     │                  │
│              └────────────────┘           │     │                  │
│                     │                      │     │                  │
│                     ▼                      │     │                  │
│              ┌──────────────┐             │     │                  │
│              │   generate   │ ◄───────────┘     │                  │
│              │   response   │                   │                  │
│              └──────┬───────┘                   │                  │
│                     │                            │                  │
│                     ▼                            │                  │
│              ┌──────────────┐                   │                  │
│              │  evaluate    │                   │                  │
│              │   quality    │                   │                  │
│              └──────────────┘                   │                  │
│                                                 │                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. 검증 기준 충족 여부

| 기준 | 상태 | 구현 |
|------|------|------|
| 모호한 질문 시 명확화 대화 트리거 | ✅ | route_after_analysis → clarify |
| 사용자가 선택지에서 선택 가능 | ✅ | ClarificationDialog + OptionButton |
| 직접 입력 옵션 제공 | ✅ | allowCustomInput = true |
| 최대 2회 연속 명확화 제한 | ✅ | max_hitl_interactions = 2 |
| 2회 재시도 실패 후 웹 검색 활성화 | ✅ | route_after_evaluation → web_search |
| 웹 검색 결과에 면책 문구 표시 | ✅ | WebSearchBanner + needs_disclaimer |

---

## 6. 주요 설정값

| Parameter | Value | Description |
|-----------|-------|-------------|
| MAX_HITL_INTERACTIONS | 2 | 최대 명확화 질문 횟수 |
| CLARITY_THRESHOLD | 0.8 | 명확화 트리거 기준 |
| TAVILY_MAX_RESULTS | 5 | Tavily 검색 최대 결과 |
| WEB_RESULT_MIN_SCORE | 0.3 | 웹 결과 포함 최소 점수 |
| WS_CONNECTION_TIMEOUT | 300 | WebSocket 타임아웃 (초) |

---

## 7. API 엔드포인트

### REST API
- `POST /api/chat` - 채팅 (HITL 포함, ChatResponse 반환)
- `POST /api/chat/clarify` - 명확화 응답 제출
- `POST /api/chat/simple` - 단순 RAG (HITL 없음)
- `GET /api/chat/sessions/{session_id}` - 세션 정보

### WebSocket
- `WS /ws/chat` - 새 채팅 세션
- `WS /ws/chat/{session_id}` - 기존 세션 재연결

---

## 8. 테스트 커버리지

```
tests/unit/
├── test_hitl_controller.py      (13 test cases)
│   ├── test_should_clarify_*
│   ├── test_generate_clarification_*
│   ├── test_refine_query_*
│   └── test_default_options_*
│
└── test_web_search_agent.py     (12 test cases)
    ├── test_optimize_query_*
    ├── test_tavily_search_*
    ├── test_evaluate_result_*
    └── test_source_reliability_*

tests/integration/
├── test_hitl_flow.py            (9 test cases)
│   ├── TestHITLFlow
│   ├── TestHITLOrchestration
│   ├── TestHITLAPI
│   └── TestMaxHITLInteractions
│
└── test_web_fallback.py         (10 test cases)
    ├── TestWebSearchFallback
    ├── TestWebSearchAgent
    ├── TestWebSearchNode
    ├── TestWebSearchResponseGeneration
    └── TestWebSearchDisclaimer
```

---

## 9. 다음 단계 (Iteration 4)

Iteration 4에서는 Polish & Production 준비를 진행합니다:
- Comprehensive Error Handling
- Logging & Metrics
- Caching Layer
- Document Indexing Script
- Accessibility & i18n
- Production Deployment

---

**완료 일시:** 2025-12-11
**개발자:** Developer Agent
