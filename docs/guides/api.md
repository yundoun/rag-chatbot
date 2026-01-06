# RAG Chatbot API Documentation

## Overview

RAG Chatbot provides a REST API and WebSocket interface for document-based question answering.

**Base URL:** `http://localhost:8000`

---

## Authentication

API requests require authentication via API key in the request header:

```
Authorization: Bearer <API_KEY>
```

---

## REST API Endpoints

### Chat Endpoints

#### POST /api/chat

Submit a chat query with full RAG pipeline (HITL enabled).

**Request Body:**
```json
{
  "query": "RAG 시스템이란 무엇인가요?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "answer": "RAG(Retrieval-Augmented Generation)는...",
  "sources": [
    {
      "title": "RAG Guide",
      "source": "rag-guide.md",
      "relevance_score": 0.92
    }
  ],
  "session_id": "session-abc123",
  "needs_clarification": false,
  "needs_disclaimer": false,
  "trace_id": "abc12345"
}
```

**Response with Clarification:**
```json
{
  "needs_clarification": true,
  "clarification": {
    "question": "어떤 설정에 대해 알고 싶으신가요?",
    "options": [
      {"id": "1", "text": "시스템 환경 설정"},
      {"id": "2", "text": "API 키 설정"}
    ],
    "allow_custom_input": true
  },
  "session_id": "session-abc123"
}
```

---

#### POST /api/chat/clarify

Submit clarification response for HITL flow.

**Request Body:**
```json
{
  "session_id": "session-abc123",
  "selected_option": "1",
  "custom_input": null
}
```

**Response:** Same as `/api/chat`

---

#### POST /api/chat/simple

Simple RAG query without HITL (for quick queries).

**Request Body:**
```json
{
  "query": "벡터 데이터베이스란?",
  "top_k": 5
}
```

---

#### GET /api/chat/sessions/{session_id}

Get session information.

**Response:**
```json
{
  "session_id": "session-abc123",
  "created_at": "2024-01-01T00:00:00Z",
  "message_count": 5,
  "last_activity": "2024-01-01T00:05:00Z"
}
```

---

### Feedback Endpoints

#### POST /api/feedback/submit

Submit user feedback for a message.

**Request Body:**
```json
{
  "message_id": "msg-abc123",
  "session_id": "session-abc123",
  "feedback_type": "positive",
  "categories": [],
  "comment": null
}
```

**Negative Feedback Example:**
```json
{
  "message_id": "msg-abc123",
  "feedback_type": "negative",
  "categories": ["incorrect", "incomplete"],
  "comment": "정보가 오래되었습니다."
}
```

**Response:**
```json
{
  "success": true,
  "feedback_id": "fb_abc123456789",
  "message": "피드백이 성공적으로 저장되었습니다."
}
```

---

#### GET /api/feedback/stats

Get feedback statistics.

**Response:**
```json
{
  "total_feedback": 100,
  "positive_count": 85,
  "negative_count": 15,
  "positive_rate": 0.85,
  "top_categories": [
    {"category": "incomplete", "count": 8},
    {"category": "incorrect", "count": 5}
  ]
}
```

---

### Health & Metrics

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

#### GET /api/metrics

Get system metrics (requires admin access).

**Response:**
```json
{
  "response_time": {
    "avg": 1234.56,
    "p50": 1000,
    "p95": 2500,
    "p99": 4000
  },
  "llm_calls": {
    "count": 1000,
    "avg_tokens": 500
  },
  "cache": {
    "hits": 500,
    "misses": 200,
    "hit_rate": 0.71
  }
}
```

---

## WebSocket API

### Connection

Connect to WebSocket for real-time chat:

```
ws://localhost:8000/ws/chat
ws://localhost:8000/ws/chat/{session_id}  # Resume session
```

---

### Message Types

#### Client → Server

**Question Message:**
```json
{
  "type": "question",
  "query": "RAG 시스템이란?"
}
```

**Clarification Response:**
```json
{
  "type": "clarification",
  "selected_option": "1",
  "custom_input": null
}
```

---

#### Server → Client

**Progress Message:**
```json
{
  "type": "progress",
  "stage": "retrieving",
  "message": "관련 문서 검색 중..."
}
```

**Clarification Request:**
```json
{
  "type": "clarification_request",
  "question": "어떤 설정에 대해 알고 싶으신가요?",
  "options": [
    {"id": "1", "text": "시스템 환경 설정"}
  ],
  "allow_custom_input": true
}
```

**Response Message:**
```json
{
  "type": "response",
  "answer": "RAG는...",
  "sources": [...],
  "needs_disclaimer": false
}
```

**Error Message:**
```json
{
  "type": "error",
  "error_type": "timeout",
  "message": "응답 시간이 초과되었습니다.",
  "recoverable": true
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error_type": "validation",
  "user_message": "입력값이 올바르지 않습니다.",
  "recoverable": false,
  "fallback_action": "ask_user",
  "trace_id": "abc12345"
}
```

### Error Types

| Type | Description | Recoverable |
|------|-------------|-------------|
| `rate_limit` | Too many requests | Yes |
| `timeout` | Request timeout | Yes |
| `parsing` | Response parsing failed | Yes |
| `no_result` | No documents found | Yes (web search) |
| `vector_store` | Database error | No |
| `validation` | Invalid input | No |
| `authentication` | Auth failed | No |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/api/chat` | 60 requests/minute |
| `/api/chat/simple` | 120 requests/minute |
| `/api/feedback/*` | 30 requests/minute |
| WebSocket | 100 messages/minute |

---

## SDKs & Examples

### Python Example

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={"query": "RAG 시스템이란?"},
    headers={"Authorization": "Bearer <API_KEY>"}
)

data = response.json()
print(data["answer"])
```

### JavaScript Example

```javascript
const response = await fetch("http://localhost:8000/api/chat", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer <API_KEY>"
  },
  body: JSON.stringify({ query: "RAG 시스템이란?" })
});

const data = await response.json();
console.log(data.answer);
```

### WebSocket Example

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/chat");

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: "question",
    query: "RAG 시스템이란?"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "response") {
    console.log(data.answer);
  }
};
```
