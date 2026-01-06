# RAG Chatbot

LangGraph 기반의 Corrective RAG + HITL(Human-in-the-Loop) 챗봇 시스템입니다.

## Overview

내부 문서 검색을 위한 RAG 챗봇으로, 단순한 검색-응답 구조를 넘어 **자기 교정(Corrective RAG)** 메커니즘과 **사람 개입(HITL)** 기능을 통해 더 정확하고 신뢰성 있는 답변을 제공합니다.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      FastAPI Backend                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   LangGraph Orchestrator                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Query     │  │  Corrective │  │       HITL          │  │
│  │  Processor  │──│     RAG     │──│    Controller       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   ChromaDB    │ │  OpenAI API   │ │  Tavily API   │
│ (Vector Store)│ │    (LLM)      │ │ (Web Search)  │
└───────────────┘ └───────────────┘ └───────────────┘
```

## Key Features

### Corrective RAG
- 검색된 문서의 관련성을 자동으로 평가
- 관련성이 낮은 경우 쿼리를 재작성하여 재검색
- 내부 문서로 답변이 불가능한 경우 웹 검색으로 fallback

### Human-in-the-Loop (HITL)
- 모호하거나 불명확한 질문에 대해 사용자에게 명확화 요청
- 복잡한 질문은 하위 질문으로 분해하여 처리

### Agentic Query Decomposition
- 복잡한 질문을 여러 하위 질문으로 분해
- 각 하위 질문에 대한 답변을 종합하여 최종 응답 생성

## Tech Stack

| Layer | Technology |
|-------|------------|
| Orchestration | LangGraph |
| Vector DB | ChromaDB |
| LLM | OpenAI GPT-4o |
| Web Search | Tavily API |
| Backend | FastAPI |
| Frontend | React + Vite + Tailwind CSS |
| Language | Python 3.10+ |

## Project Structure

```
rag-chatbot/
├── src/
│   ├── agents/          # Query processor, HITL, Web search agent
│   ├── api/             # FastAPI endpoints
│   ├── config/          # Settings & constants
│   ├── core/            # LangGraph orchestrator & state
│   ├── llm/             # LLM provider & prompts
│   ├── rag/             # Corrective RAG engine
│   ├── utils/           # Logger, metrics, cache
│   └── vectorstore/     # ChromaDB management
├── frontend/            # React application
├── tests/               # Test suite
├── docker/              # Docker configurations
└── docs/                # Documentation
```

## License

MIT
