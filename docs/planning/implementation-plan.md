# RAG Chatbot Implementation Plan

**Project:** Internal Document Search RAG Chatbot (React UI + FastAPI)
**Version:** 1.0
**Date:** 2025-12-11
**Author:** Planner Agent

---

## Executive Summary

This implementation plan details the phased development of a RAG chatbot with React frontend and FastAPI backend. The system implements Corrective RAG, HITL (Human-in-the-Loop), and web search fallback capabilities using LangGraph orchestration.

### Tech Stack Summary

| Layer | Technology |
|-------|------------|
| Frontend | React + Tailwind CSS |
| Backend | FastAPI |
| RAG Framework | LangGraph |
| Vector DB | ChromaDB |
| LLM | OpenAI GPT-4o |
| Web Search | Tavily API |

---

## Iteration 1: Foundation (MVP Core)

### Goal
Establish project infrastructure and implement basic RAG query-response flow without advanced features.

### Tasks

- [ ] **Task 1.1: Project Setup & Configuration**
  - Description: Initialize project structure, create configuration management, and set up environment handling
  - Files:
    - `src/config/__init__.py`
    - `src/config/settings.py` - Pydantic settings for environment config
    - `src/config/constants.py` - Application constants
    - `.env.example` - Environment template
    - `requirements.txt` - Production dependencies
    - `requirements-dev.txt` - Development dependencies
  - Estimate: Low complexity
  - Dependencies: None

- [ ] **Task 1.2: LLM Provider Abstraction**
  - Description: Create abstraction layer for OpenAI integration with structured output support
  - Files:
    - `src/llm/__init__.py`
    - `src/llm/provider.py` - Abstract LLM interface
    - `src/llm/openai_provider.py` - OpenAI implementation
  - Estimate: Low complexity
  - Dependencies: Task 1.1

- [ ] **Task 1.3: Vector Store Manager (ChromaDB)**
  - Description: Implement ChromaDB connection, collection management, and basic CRUD operations
  - Files:
    - `src/vectorstore/__init__.py`
    - `src/vectorstore/manager.py` - ChromaDB operations
    - `src/vectorstore/embeddings.py` - Embedding provider abstraction
    - `src/vectorstore/indexer.py` - Document indexing utilities
  - Estimate: Medium complexity
  - Dependencies: Task 1.1, Task 1.2

- [ ] **Task 1.4: Core State Management**
  - Description: Define RAGState TypedDict and Pydantic models for data flow
  - Files:
    - `src/core/__init__.py`
    - `src/core/state.py` - LangGraph state definitions
    - `src/core/models.py` - Pydantic input/output models
    - `src/core/exceptions.py` - Custom exception hierarchy
  - Estimate: Medium complexity
  - Dependencies: Task 1.1

- [ ] **Task 1.5: Basic Query Processor**
  - Description: Implement query analysis (complexity, clarity, ambiguity detection)
  - Files:
    - `src/agents/__init__.py`
    - `src/agents/query_processor.py` - Query analysis logic
    - `src/llm/prompts/query_analysis.py` - Prompt #1
  - Estimate: Medium complexity
  - Dependencies: Task 1.2, Task 1.4

- [ ] **Task 1.6: Basic Document Retriever**
  - Description: Implement simple vector similarity search
  - Files:
    - `src/rag/__init__.py`
    - `src/rag/retriever.py` - Document retrieval logic
  - Estimate: Low complexity
  - Dependencies: Task 1.3, Task 1.4

- [ ] **Task 1.7: Response Generator (Basic)**
  - Description: Generate answers from retrieved documents with source citations
  - Files:
    - `src/rag/response_generator.py` - Answer generation
    - `src/llm/prompts/response.py` - Prompt #6
  - Estimate: Medium complexity
  - Dependencies: Task 1.2, Task 1.4, Task 1.6

- [ ] **Task 1.8: FastAPI Backend Setup**
  - Description: Create FastAPI application with basic RAG endpoint
  - Files:
    - `src/api/__init__.py`
    - `src/api/main.py` - FastAPI application entry point
    - `src/api/routes/__init__.py`
    - `src/api/routes/chat.py` - Chat endpoint
    - `src/api/schemas.py` - API request/response schemas
  - Estimate: Medium complexity
  - Dependencies: Task 1.5, Task 1.6, Task 1.7

- [ ] **Task 1.9: React Frontend (Basic Chat UI)**
  - Description: Create minimal chat interface with message display and input
  - Files:
    - `frontend/package.json`
    - `frontend/src/App.jsx` - Main application component
    - `frontend/src/components/ChatContainer.jsx` - Chat area
    - `frontend/src/components/MessageBubble.jsx` - Message display
    - `frontend/src/components/ChatInput.jsx` - User input
    - `frontend/src/services/api.js` - API client
    - `frontend/src/index.css` - Tailwind imports
    - `frontend/tailwind.config.js`
  - Estimate: Medium complexity
  - Dependencies: Task 1.8

- [ ] **Task 1.10: Basic Integration Test**
  - Description: End-to-end test of basic query-response flow
  - Files:
    - `tests/conftest.py` - Pytest fixtures
    - `tests/integration/test_basic_flow.py`
  - Estimate: Low complexity
  - Dependencies: Task 1.9

### Verification Criteria
- [ ] User can enter a question in React UI
- [ ] Backend processes query and retrieves relevant documents
- [ ] Response with sources is displayed in chat UI
- [ ] Configuration loads from environment variables
- [ ] API health check endpoint responds

### Done When
User can ask a simple question through React UI and receive an answer with document sources.

---

## Iteration 2: Corrective RAG Engine

### Goal
Implement relevance evaluation and corrective retrieval loop to improve answer quality.

### Tasks

- [ ] **Task 2.1: Relevance Evaluator**
  - Description: Implement hybrid relevance scoring (embedding + LLM evaluation)
  - Files:
    - `src/rag/relevance_evaluator.py` - Document relevance scoring
    - `src/llm/prompts/relevance.py` - Prompt #4
  - Estimate: High complexity
  - Dependencies: Iteration 1

- [ ] **Task 2.2: Query Rewriter**
  - Description: Implement query rewriting strategies for failed searches
  - Files:
    - `src/rag/query_rewriter.py` - Query rewriting logic
    - `src/llm/prompts/rewrite.py` - Prompt #5
  - Estimate: Medium complexity
  - Dependencies: Task 2.1

- [ ] **Task 2.3: Corrective RAG Engine**
  - Description: Orchestrate retrieval correction loop (evaluate → rewrite → re-retrieve)
  - Files:
    - `src/rag/corrective_engine.py` - Correction loop logic
  - Estimate: High complexity
  - Dependencies: Task 2.1, Task 2.2

- [ ] **Task 2.4: LangGraph Orchestrator (Basic)**
  - Description: Create LangGraph state machine for basic RAG flow
  - Files:
    - `src/core/orchestrator.py` - LangGraph workflow definition
    - `src/core/nodes.py` - Individual node implementations
    - `src/core/edges.py` - Routing logic
  - Estimate: High complexity
  - Dependencies: Task 2.3

- [ ] **Task 2.5: Response Quality Evaluator**
  - Description: Assess generated response quality and determine if disclaimer needed
  - Files:
    - `src/rag/quality_evaluator.py` - Quality assessment
    - `src/llm/prompts/quality.py` - Prompt #7
  - Estimate: Medium complexity
  - Dependencies: Task 2.4

- [ ] **Task 2.6: Update API for Corrective Flow**
  - Description: Integrate corrective RAG engine with FastAPI endpoints
  - Files:
    - `src/api/routes/chat.py` - Updated endpoint
  - Estimate: Low complexity
  - Dependencies: Task 2.4, Task 2.5

- [ ] **Task 2.7: React Loading States**
  - Description: Add progress indicators and step feedback during processing
  - Files:
    - `frontend/src/components/LoadingIndicator.jsx`
    - `frontend/src/components/ProcessingSteps.jsx`
  - Estimate: Low complexity
  - Dependencies: Task 2.6

- [ ] **Task 2.8: Corrective RAG Tests**
  - Description: Test relevance evaluation and correction loop behavior
  - Files:
    - `tests/unit/test_relevance_evaluator.py`
    - `tests/unit/test_corrective_engine.py`
    - `tests/integration/test_corrective_flow.py`
  - Estimate: Medium complexity
  - Dependencies: Task 2.6

### Verification Criteria
- [ ] System evaluates relevance of retrieved documents
- [ ] Queries are rewritten when relevance is low (< 0.8)
- [ ] Maximum 2 correction retries are enforced
- [ ] Low confidence responses show disclaimer banner
- [ ] Loading UI shows processing steps

### Done When
System automatically corrects low-quality retrievals and provides quality-assessed responses.

---

## Iteration 3: HITL & Web Search

### Goal
Add human-in-the-loop clarification and web search fallback for comprehensive coverage.

### Tasks

- [ ] **Task 3.1: HITL Controller**
  - Description: Implement clarification question generation and user response handling
  - Files:
    - `src/agents/hitl_controller.py` - HITL logic
    - `src/llm/prompts/clarification.py` - Prompt #2
  - Estimate: Medium complexity
  - Dependencies: Iteration 2

- [ ] **Task 3.2: Web Search Agent**
  - Description: Integrate Tavily API for web search fallback
  - Files:
    - `src/agents/web_search_agent.py` - Tavily integration
    - `src/llm/prompts/web_integration.py` - Prompt #8
  - Estimate: Medium complexity
  - Dependencies: Iteration 2

- [ ] **Task 3.3: Agentic Controller (Complex Queries)**
  - Description: Implement query decomposition for complex questions
  - Files:
    - `src/agents/agentic_controller.py` - Query decomposition
    - `src/llm/prompts/decomposition.py` - Prompt #3
  - Estimate: Medium complexity
  - Dependencies: Task 3.1

- [ ] **Task 3.4: Update LangGraph Orchestrator**
  - Description: Add HITL interrupt points and web search fallback paths
  - Files:
    - `src/core/orchestrator.py` - Extended workflow
    - `src/core/edges.py` - Updated routing
  - Estimate: High complexity
  - Dependencies: Task 3.1, Task 3.2, Task 3.3

- [ ] **Task 3.5: WebSocket for HITL**
  - Description: Implement WebSocket endpoint for real-time HITL communication
  - Files:
    - `src/api/routes/websocket.py` - WebSocket handler
    - `src/api/websocket_manager.py` - Connection management
  - Estimate: High complexity
  - Dependencies: Task 3.4

- [ ] **Task 3.6: React HITL UI**
  - Description: Add clarification dialog with option buttons
  - Files:
    - `frontend/src/components/ClarificationDialog.jsx`
    - `frontend/src/components/OptionButton.jsx`
    - `frontend/src/hooks/useWebSocket.js`
  - Estimate: Medium complexity
  - Dependencies: Task 3.5

- [ ] **Task 3.7: Web Search Result Display**
  - Description: Add UI for web search results with disclaimers
  - Files:
    - `frontend/src/components/WebSearchBanner.jsx`
    - `frontend/src/components/SourceList.jsx` - Enhanced with web sources
  - Estimate: Low complexity
  - Dependencies: Task 3.6

- [ ] **Task 3.8: HITL & Web Search Tests**
  - Description: Test clarification flow and web fallback scenarios
  - Files:
    - `tests/unit/test_hitl_controller.py`
    - `tests/unit/test_web_search_agent.py`
    - `tests/integration/test_hitl_flow.py`
    - `tests/integration/test_web_fallback.py`
  - Estimate: Medium complexity
  - Dependencies: Task 3.7

### Verification Criteria
- [ ] Ambiguous queries trigger clarification dialog
- [ ] User can select from options or provide custom input
- [ ] Maximum 2 consecutive clarifications enforced
- [ ] Web search activates after 2 failed corrections
- [ ] Web results display with appropriate disclaimer

### Done When
System can handle ambiguous queries interactively and fall back to web search when internal documents are insufficient.

---

## Iteration 4: Polish & Production

### Goal
Add error handling, monitoring, accessibility, and deployment readiness.

### Tasks

- [ ] **Task 4.1: Comprehensive Error Handling**
  - Description: Implement error handler with retry logic and graceful degradation
  - Files:
    - `src/utils/error_handler.py` - Central error handling
    - `src/core/exceptions.py` - Extended exception hierarchy
  - Estimate: Medium complexity
  - Dependencies: Iteration 3

- [ ] **Task 4.2: Logging & Metrics**
  - Description: Implement structured logging and performance metrics collection
  - Files:
    - `src/utils/logger.py` - Structured logging config
    - `src/utils/metrics.py` - Metrics collection
  - Estimate: Medium complexity
  - Dependencies: Task 4.1

- [ ] **Task 4.3: Caching Layer**
  - Description: Implement response caching for repeated queries
  - Files:
    - `src/utils/cache.py` - Caching utilities
  - Estimate: Low complexity
  - Dependencies: Task 4.2

- [ ] **Task 4.4: Document Indexing Script**
  - Description: Create CLI for batch document indexing
  - Files:
    - `scripts/index_documents.py` - Indexing CLI
    - `scripts/evaluate_prompts.py` - Prompt evaluation tool
  - Estimate: Medium complexity
  - Dependencies: Iteration 1

- [ ] **Task 4.5: React UI Polish**
  - Description: Add animations, transitions, and responsive design
  - Files:
    - `frontend/src/styles/animations.css`
    - `frontend/src/components/Toast.jsx`
    - `frontend/src/components/Header.jsx`
    - Update existing components for responsive design
  - Estimate: Medium complexity
  - Dependencies: Iteration 3

- [ ] **Task 4.6: Accessibility (A11y)**
  - Description: Implement keyboard navigation, ARIA labels, focus management
  - Files:
    - Update all React components with a11y attributes
    - `frontend/src/hooks/useKeyboardNavigation.js`
  - Estimate: Medium complexity
  - Dependencies: Task 4.5

- [ ] **Task 4.7: Feedback System**
  - Description: Implement thumbs up/down feedback with optional comments
  - Files:
    - `frontend/src/components/FeedbackButtons.jsx`
    - `frontend/src/components/FeedbackModal.jsx`
    - `src/api/routes/feedback.py`
  - Estimate: Low complexity
  - Dependencies: Task 4.5

- [ ] **Task 4.8: Docker Configuration**
  - Description: Create Docker and docker-compose setup for deployment
  - Files:
    - `docker/Dockerfile`
    - `docker/Dockerfile.frontend`
    - `docker/docker-compose.yml`
    - `docker/.dockerignore`
  - Estimate: Medium complexity
  - Dependencies: All previous tasks

- [ ] **Task 4.9: E2E Test Suite**
  - Description: Comprehensive end-to-end scenario tests
  - Files:
    - `tests/e2e/test_scenarios.py` - 5 core scenario tests
    - `tests/e2e/test_performance.py` - Performance benchmarks
  - Estimate: High complexity
  - Dependencies: Task 4.8

- [ ] **Task 4.10: Documentation**
  - Description: API documentation and deployment guide
  - Files:
    - `docs/api.md` - API reference
    - `docs/deployment.md` - Deployment guide
    - `docs/prompts.md` - Prompt documentation
    - `README.md` - Project overview
  - Estimate: Low complexity
  - Dependencies: Task 4.9

### Verification Criteria
- [ ] All API errors return user-friendly messages
- [ ] Response times logged and monitored
- [ ] Cache reduces repeated query latency
- [ ] UI works on mobile and desktop
- [ ] Keyboard navigation fully functional
- [ ] Docker containers build and run successfully
- [ ] All 5 E2E scenarios pass

### Done When
Application is production-ready with comprehensive error handling, monitoring, accessibility, and containerized deployment.

---

## Project Timeline

```
Phase 1: Foundation (Iteration 1)
├── Tasks 1.1-1.10
└── Deliverable: Basic RAG chatbot with React UI

Phase 2: Core RAG (Iteration 2)
├── Tasks 2.1-2.8
└── Deliverable: Corrective RAG with quality evaluation

Phase 3: Enhanced Features (Iteration 3)
├── Tasks 3.1-3.8
└── Deliverable: HITL + Web search integration

Phase 4: Production (Iteration 4)
├── Tasks 4.1-4.10
└── Deliverable: Production-ready application
```

---

## Risk Management

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM latency degrading UX | High | Medium | Implement streaming responses, show processing steps |
| Relevance evaluation inaccuracy | Medium | High | Tune threshold (0.8), build golden test dataset |
| WebSocket complexity for HITL | Medium | Medium | Consider polling fallback if WebSocket issues arise |
| API rate limiting | Medium | Medium | Implement exponential backoff, request queuing |
| React-FastAPI CORS issues | Low | Low | Configure CORS properly from start |
| Token limit exceeded | Medium | Medium | Implement document chunking, context truncation |

---

## Component Dependencies Graph

```
                    ┌─────────────────────┐
                    │  Config Manager     │
                    │     (Task 1.1)      │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌───────────────┐ ┌───────────┐ ┌───────────────┐
      │ LLM Provider  │ │  State    │ │ Vector Store  │
      │  (Task 1.2)   │ │ (Task 1.4)│ │  (Task 1.3)   │
      └───────┬───────┘ └─────┬─────┘ └───────┬───────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                    ┌─────────────────────┐
                    │  Query Processor    │
                    │     (Task 1.5)      │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌───────────────┐ ┌───────────┐ ┌───────────────┐
      │   Retriever   │ │ Relevance │ │ Response Gen  │
      │  (Task 1.6)   │ │ (Task 2.1)│ │  (Task 1.7)   │
      └───────────────┘ └───────────┘ └───────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                    ┌─────────────────────┐
                    │ Corrective Engine   │
                    │     (Task 2.3)      │
                    └─────────┬───────────┘
                              ▼
                    ┌─────────────────────┐
                    │  LangGraph Orch.    │
                    │     (Task 2.4)      │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌───────────────┐ ┌───────────┐ ┌───────────────┐
      │     HITL      │ │ Web Search│ │   Agentic     │
      │  (Task 3.1)   │ │ (Task 3.2)│ │  (Task 3.3)   │
      └───────────────┘ └───────────┘ └───────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                    ┌─────────────────────┐
                    │    FastAPI Server   │
                    │     (Task 1.8)      │
                    └─────────┬───────────┘
                              ▼
                    ┌─────────────────────┐
                    │    React Frontend   │
                    │     (Task 1.9)      │
                    └─────────────────────┘
```

---

## File Implementation Order

### Iteration 1 Files (Foundation)
```
1.  src/config/__init__.py
2.  src/config/settings.py
3.  src/config/constants.py
4.  .env.example
5.  requirements.txt
6.  src/llm/__init__.py
7.  src/llm/provider.py
8.  src/llm/openai_provider.py
9.  src/vectorstore/__init__.py
10. src/vectorstore/manager.py
11. src/vectorstore/embeddings.py
12. src/core/__init__.py
13. src/core/state.py
14. src/core/models.py
15. src/core/exceptions.py
16. src/agents/__init__.py
17. src/agents/query_processor.py
18. src/llm/prompts/query_analysis.py
19. src/rag/__init__.py
20. src/rag/retriever.py
21. src/rag/response_generator.py
22. src/llm/prompts/response.py
23. src/api/__init__.py
24. src/api/main.py
25. src/api/routes/chat.py
26. src/api/schemas.py
27. frontend/package.json
28. frontend/src/App.jsx
29. frontend/src/components/ChatContainer.jsx
30. frontend/src/components/MessageBubble.jsx
31. frontend/src/components/ChatInput.jsx
32. frontend/src/services/api.js
```

### Iteration 2 Files (Corrective RAG)
```
33. src/rag/relevance_evaluator.py
34. src/llm/prompts/relevance.py
35. src/rag/query_rewriter.py
36. src/llm/prompts/rewrite.py
37. src/rag/corrective_engine.py
38. src/core/orchestrator.py
39. src/core/nodes.py
40. src/core/edges.py
41. src/rag/quality_evaluator.py
42. src/llm/prompts/quality.py
43. frontend/src/components/LoadingIndicator.jsx
44. frontend/src/components/ProcessingSteps.jsx
```

### Iteration 3 Files (HITL & Web Search)
```
45. src/agents/hitl_controller.py
46. src/llm/prompts/clarification.py
47. src/agents/web_search_agent.py
48. src/llm/prompts/web_integration.py
49. src/agents/agentic_controller.py
50. src/llm/prompts/decomposition.py
51. src/api/routes/websocket.py
52. src/api/websocket_manager.py
53. frontend/src/components/ClarificationDialog.jsx
54. frontend/src/components/OptionButton.jsx
55. frontend/src/hooks/useWebSocket.js
56. frontend/src/components/WebSearchBanner.jsx
57. frontend/src/components/SourceList.jsx
```

### Iteration 4 Files (Production)
```
58. src/utils/error_handler.py
59. src/utils/logger.py
60. src/utils/metrics.py
61. src/utils/cache.py
62. scripts/index_documents.py
63. frontend/src/components/Toast.jsx
64. frontend/src/components/Header.jsx
65. frontend/src/components/FeedbackButtons.jsx
66. frontend/src/components/FeedbackModal.jsx
67. src/api/routes/feedback.py
68. docker/Dockerfile
69. docker/Dockerfile.frontend
70. docker/docker-compose.yml
71. tests/e2e/test_scenarios.py
72. docs/api.md
73. docs/deployment.md
74. README.md
```

---

## Complexity Summary

| Complexity | Task Count | Examples |
|------------|------------|----------|
| Low | 12 | Config setup, Basic API routes, Simple UI components |
| Medium | 21 | Query processor, Relevance evaluator, React components |
| High | 7 | Corrective engine, LangGraph orchestrator, E2E tests |

---

## Success Criteria Summary

| Phase | Key Metric | Target |
|-------|------------|--------|
| Iteration 1 | Basic query-response works | 100% |
| Iteration 2 | Correction improves relevance | avg > 0.8 |
| Iteration 3 | HITL reduces ambiguity failures | < 10% |
| Iteration 4 | Response time (Happy Path) | < 10s |
| Iteration 4 | E2E test pass rate | 100% |

---

**Implementation Plan Complete**

*This plan is based on the feasibility report, prompt review report, UX design proposal, and architecture proposal. Adjustments may be needed during implementation based on practical constraints.*
