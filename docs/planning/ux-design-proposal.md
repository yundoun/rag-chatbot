# RAG Chatbot UX Design Proposal

## Project Overview

| Item | Description |
|------|-------------|
| **Purpose** | Internal document search and Q&A chatbot |
| **Target Users** | Developers and general employees |
| **UI Framework** | Streamlit |
| **Response Time** | Happy path: 8-9s, Complex: 13-15s, HITL: 10s + user response |

---

## 1. User Personas

### Persona A: Developer (김개발)
- **Role**: Backend Developer, 3 years experience
- **Characteristics**: Tech-savvy, prefers detailed technical answers, values efficiency
- **Goals**: Quickly find API documentation, code examples, and internal guidelines
- **Pain Points**:
  - Scattered documentation across multiple platforms
  - Outdated or conflicting information
  - Time wasted searching through Confluence/Wiki pages
- **Usage Pattern**: 15-20 queries per day, expects precise answers

### Persona B: General Employee (이사원)
- **Role**: Marketing team member, non-technical background
- **Characteristics**: Prefers simple language, needs step-by-step guidance
- **Goals**: Find HR policies, company procedures, and general information
- **Pain Points**:
  - Technical jargon in documentation
  - Unclear navigation structure
  - Long documents without summaries
- **Usage Pattern**: 3-5 queries per week, expects easy-to-understand answers

---

## 2. User Flow Diagrams

### 2.1 Main Query Flow (Happy Path)
```
[Landing Page]
      ↓
[User enters question in input field]
      ↓
[Click "질문하기" or press Enter]
      ↓
[Loading state: "답변을 생성하고 있습니다..."]
      ↓ (8-9 seconds)
[Display Answer]
├── Answer (Markdown formatted)
├── Sources (collapsible list)
├── Confidence indicator (if low)
└── Feedback buttons (👍/👎)
      ↓
[User provides feedback or asks follow-up]
```

### 2.2 HITL Clarification Flow
```
[User enters ambiguous question]
      ↓
[System detects ambiguity]
      ↓
[Display clarification prompt]
"질문을 명확히 해주세요. 다음 중 어떤 것에 대해 알고 싶으신가요?"
├── [선택지 1] ← clickable button
├── [선택지 2] ← clickable button
└── [선택지 3] ← clickable button
      ↓
[User selects option]
      ↓
[Loading state]
      ↓ (10 seconds)
[Display refined answer]
      ↓
(Max 2 consecutive clarifications)
```

### 2.3 Error Handling Flow
```
[Query submission]
      ↓
[Error occurs]
      ├── Network error → "네트워크 오류가 발생했습니다. 다시 시도해주세요." + [재시도] button
      ├── No results → "관련 문서를 찾을 수 없습니다. 다른 키워드로 검색해보세요."
      ├── Timeout → "응답 시간이 초과되었습니다. 질문을 더 간단히 해보세요."
      └── Server error → "일시적인 오류입니다. 잠시 후 다시 시도해주세요."
```

### 2.4 Low Confidence Flow
```
[Answer generated with low confidence]
      ↓
[Display warning banner]
⚠️ "이 답변은 신뢰도가 낮습니다. 검증이 필요할 수 있습니다."
      ↓
[Show answer with sources]
      ↓
[Optionally show web search results with disclaimer]
"* 웹 검색 결과가 포함되어 있습니다. 정확성을 확인해주세요."
```

---

## 3. Wireframes

### 3.1 Main Chat Interface (Desktop)
```
+------------------------------------------------------------------+
|  🤖 사내 문서 검색 챗봇                              [도움말] [설정]  |
+------------------------------------------------------------------+
|                                                                  |
|  +------------------------------------------------------------+  |
|  |                    Chat History Area                       |  |
|  |  (scrollable)                                              |  |
|  |                                                            |  |
|  |  ┌─────────────────────────────────────────────────────┐  |  |
|  |  │ 👤 User                                              │  |  |
|  |  │ "REST API 인증 방법에 대해 알려주세요"                  │  |  |
|  |  └─────────────────────────────────────────────────────┘  |  |
|  |                                                            |  |
|  |  ┌─────────────────────────────────────────────────────┐  |  |
|  |  │ 🤖 Assistant                                         │  |  |
|  |  │                                                      │  |  |
|  |  │ ## REST API 인증 방법                                │  |  |
|  |  │                                                      │  |  |
|  |  │ 사내 REST API는 다음 인증 방식을 지원합니다:          │  |  |
|  |  │                                                      │  |  |
|  |  │ 1. **Bearer Token** (권장)                           │  |  |
|  |  │    - Header: `Authorization: Bearer <token>`         │  |  |
|  |  │                                                      │  |  |
|  |  │ 2. **API Key**                                       │  |  |
|  |  │    - Header: `X-API-Key: <key>`                      │  |  |
|  |  │                                                      │  |  |
|  |  │ ▼ 출처 보기 (2건)                                    │  |  |
|  |  │ ┌──────────────────────────────────────────────────┐ │  |  |
|  |  │ │ 📄 API-Gateway-Guide.pdf (p.12)                  │ │  |  |
|  |  │ │ 📄 Security-Handbook.md (Section 3.2)            │ │  |  |
|  |  │ └──────────────────────────────────────────────────┘ │  |  |
|  |  │                                                      │  |  |
|  |  │ 이 답변이 도움이 되었나요?  [👍] [👎]                  │  |  |
|  |  └─────────────────────────────────────────────────────┘  |  |
|  |                                                            |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  💬 질문을 입력하세요...                         [질문하기] |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  💡 추천 질문: [연차 신청 방법] [VPN 설정] [코드 리뷰 가이드]      |
|                                                                  |
+------------------------------------------------------------------+
```

### 3.2 HITL Clarification UI
```
+------------------------------------------------------------------+
|                                                                  |
|  ┌─────────────────────────────────────────────────────────────┐ |
|  │ 🤖 Assistant                                                │ |
|  │                                                             │ |
|  │ 질문을 더 명확히 해주시면 정확한 답변을 드릴 수 있습니다.    │ |
|  │                                                             │ |
|  │ "배포"에 대해 어떤 정보를 원하시나요?                        │ |
|  │                                                             │ |
|  │ +---------------------------+                               │ |
|  │ | 🚀 프로덕션 배포 절차      | ← hover: highlight          │ |
|  │ +---------------------------+                               │ |
|  │ +---------------------------+                               │ |
|  │ | 🧪 스테이징 환경 배포      |                              │ |
|  │ +---------------------------+                               │ |
|  │ +---------------------------+                               │ |
|  │ | 🔧 CI/CD 파이프라인 설정   |                              │ |
|  │ +---------------------------+                               │ |
|  │ +---------------------------+                               │ |
|  │ | ✏️ 직접 입력하기           |                              │ |
|  │ +---------------------------+                               │ |
|  │                                                             │ |
|  └─────────────────────────────────────────────────────────────┘ |
|                                                                  |
+------------------------------------------------------------------+
```

### 3.3 Loading State
```
+------------------------------------------------------------------+
|                                                                  |
|  ┌─────────────────────────────────────────────────────────────┐ |
|  │ 🤖 Assistant                                                │ |
|  │                                                             │ |
|  │ ⏳ 답변을 생성하고 있습니다...                               │ |
|  │                                                             │ |
|  │ ████████████░░░░░░░░░░░░░░░░░░░░  35%                       │ |
|  │                                                             │ |
|  │ ✓ 관련 문서 검색 중...                                      │ |
|  │ ○ 답변 생성 중...                                           │ |
|  │ ○ 출처 확인 중...                                           │ |
|  │                                                             │ |
|  │ 예상 소요 시간: 약 8초                                      │ |
|  │                                                             │ |
|  └─────────────────────────────────────────────────────────────┘ |
|                                                                  |
+------------------------------------------------------------------+
```

### 3.4 Low Confidence Warning
```
+------------------------------------------------------------------+
|                                                                  |
|  ┌─────────────────────────────────────────────────────────────┐ |
|  │ ⚠️ 신뢰도 안내                                    [닫기 ✕] │ |
|  │ 이 답변은 관련 문서가 충분하지 않아 신뢰도가 낮을 수 있습니다.│ |
|  │ 중요한 결정에 사용하기 전에 담당자에게 확인을 권장합니다.    │ |
|  └─────────────────────────────────────────────────────────────┘ |
|                                                                  |
|  ┌─────────────────────────────────────────────────────────────┐ |
|  │ 🤖 Assistant                                                │ |
|  │                                                             │ |
|  │ [Answer content here...]                                    │ |
|  │                                                             │ |
|  │ ℹ️ *이 답변에는 웹 검색 결과가 포함되어 있습니다.            │ |
|  │    정확성을 확인해주세요.*                                  │ |
|  │                                                             │ |
|  └─────────────────────────────────────────────────────────────┘ |
|                                                                  |
+------------------------------------------------------------------+
```

### 3.5 Mobile Layout (Responsive)
```
+-------------------------+
| 🤖 사내 문서 챗봇   [≡] |
+-------------------------+
|                         |
| ┌─────────────────────┐ |
| │ 👤 REST API 인증    │ |
| │ 방법에 대해         │ |
| │ 알려주세요          │ |
| └─────────────────────┘ |
|                         |
| ┌─────────────────────┐ |
| │ 🤖 ## REST API 인증 │ |
| │                     │ |
| │ 사내 REST API는...  │ |
| │                     │ |
| │ [더보기 ▼]          │ |
| │                     │ |
| │ ▶ 출처 (2건)        │ |
| │                     │ |
| │ [👍] [👎]           │ |
| └─────────────────────┘ |
|                         |
+-------------------------+
| 💬 질문 입력...    [➤] |
+-------------------------+
| 추천: [연차] [VPN]      |
+-------------------------+
```

---

## 4. Interaction Specifications

### 4.1 Input Interactions
| Action | Trigger | Response |
|--------|---------|----------|
| Submit question | Click "질문하기" or Enter key | Show loading state, disable input |
| Clear input | Click X icon or Escape key | Clear text, focus input |
| Voice input | Click 🎤 icon | Activate speech recognition |
| Select suggestion | Click recommendation chip | Auto-fill input and submit |

### 4.2 HITL Interactions
| Action | Trigger | Response |
|--------|---------|----------|
| Select clarification option | Click option button | Submit selected option as refined query |
| Custom input | Click "직접 입력하기" | Show text input for custom clarification |
| Skip clarification | Press Escape or click outside | Proceed with original ambiguous query |

### 4.3 Feedback Interactions
| Action | Trigger | Response |
|--------|---------|----------|
| Positive feedback | Click 👍 | Highlight button, show "감사합니다!" toast |
| Negative feedback | Click 👎 | Show feedback form modal |
| Feedback form | Submit form | Send to feedback API, close modal |

### 4.4 Visual Feedback
| State | Visual Indicator |
|-------|------------------|
| Typing | Cursor blink in input field |
| Processing | Animated progress bar + step indicators |
| Success | Green checkmark animation |
| Error | Red warning icon + shake animation |
| Low confidence | Yellow warning banner |

### 4.5 Transition Animations
| Transition | Animation | Duration |
|------------|-----------|----------|
| Message appear | Fade in + slide up | 200ms |
| Sources expand | Accordion expand | 150ms |
| Button hover | Scale up 1.05x | 100ms |
| Modal open | Fade in + scale | 200ms |
| Toast notification | Slide in from top | 300ms |

---

## 5. Accessibility (A11y) Guidelines

### 5.1 Keyboard Navigation
| Key | Action |
|-----|--------|
| Tab | Navigate between interactive elements |
| Shift+Tab | Navigate backwards |
| Enter | Submit form / activate button |
| Escape | Close modal / clear input |
| Arrow Up/Down | Navigate chat history |
| Ctrl+Enter | Submit with newline support |

### 5.2 Screen Reader Support
```html
<!-- ARIA labels example -->
<button aria-label="질문 제출하기">질문하기</button>
<div role="status" aria-live="polite">답변을 생성하고 있습니다...</div>
<div role="alert" aria-live="assertive">오류가 발생했습니다</div>
<button aria-label="이 답변이 도움이 됨" aria-pressed="false">👍</button>
```

### 5.3 Focus Management
- Focus returns to input field after answer is displayed
- Modal focus trap when clarification dialog opens
- Skip link to main content for screen readers
- Visible focus indicators (2px solid outline)

### 5.4 Color Contrast
| Element | Foreground | Background | Ratio |
|---------|------------|------------|-------|
| Body text | #1a1a1a | #ffffff | 17.1:1 ✓ |
| Link text | #0066cc | #ffffff | 7.0:1 ✓ |
| Error text | #d32f2f | #ffffff | 5.9:1 ✓ |
| Warning | #f57c00 | #fff8e1 | 4.5:1 ✓ |
| Success | #388e3c | #ffffff | 4.5:1 ✓ |

### 5.5 Color Blindness Considerations
- Don't rely on color alone to convey information
- Use icons alongside color indicators
  - ✓ Success (green + checkmark)
  - ⚠️ Warning (yellow + warning icon)
  - ✕ Error (red + X icon)
- Provide text labels for status indicators

---

## 6. Responsive Design Specifications

### 6.1 Breakpoints
| Device | Width | Layout |
|--------|-------|--------|
| Mobile | < 640px | Single column, stacked |
| Tablet | 640px - 1024px | Single column, wider margins |
| Desktop | > 1024px | Centered container, max-width 800px |

### 6.2 Component Adaptations

#### Chat Container
| Device | Specifications |
|--------|----------------|
| Mobile | Full width, 8px padding |
| Tablet | 16px padding, rounded corners |
| Desktop | max-width 800px, centered, 24px padding |

#### Input Field
| Device | Specifications |
|--------|----------------|
| Mobile | Full width, fixed bottom, 48px height |
| Tablet | Full width, 52px height |
| Desktop | Full width within container, 56px height |

#### Message Bubbles
| Device | Specifications |
|--------|----------------|
| Mobile | Max 90% width, 12px padding |
| Tablet | Max 80% width, 16px padding |
| Desktop | Max 70% width, 20px padding |

#### Buttons
| Device | Specifications |
|--------|----------------|
| Mobile | Min 44px touch target, full width CTAs |
| Tablet | 48px touch target |
| Desktop | 40px height, hover states enabled |

### 6.3 Touch vs. Mouse
| Interaction | Touch | Mouse |
|-------------|-------|-------|
| Primary action | Tap | Click |
| Secondary action | Long press | Right click |
| Scroll | Swipe | Scroll wheel |
| Hover preview | N/A | On hover |
| Button feedback | Ripple effect | Hover highlight |

---

## 7. Streamlit Implementation Recommendations

### 7.1 Layout Components
```python
# Recommended Streamlit structure
import streamlit as st

# Page config
st.set_page_config(
    page_title="사내 문서 검색 챗봇",
    page_icon="🤖",
    layout="centered"
)

# Custom CSS for styling
st.markdown("""
<style>
    .stChatMessage { border-radius: 12px; }
    .stButton > button { border-radius: 8px; }
    .source-card { background: #f5f5f5; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# Chat container
chat_container = st.container()

# Input at bottom
with st.container():
    user_input = st.chat_input("질문을 입력하세요...")
```

### 7.2 Chat Message Pattern
```python
# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg.get("sources"):
            with st.expander("📚 출처 보기"):
                for source in msg["sources"]:
                    st.markdown(f"- {source}")

        if msg["role"] == "assistant":
            col1, col2, _ = st.columns([1, 1, 8])
            with col1:
                st.button("👍", key=f"up_{msg['id']}")
            with col2:
                st.button("👎", key=f"down_{msg['id']}")
```

### 7.3 HITL Clarification Pattern
```python
# HITL clarification UI
if st.session_state.needs_clarification:
    st.info("🤔 질문을 명확히 해주세요")

    options = st.session_state.clarification_options

    cols = st.columns(len(options))
    for i, option in enumerate(options):
        with cols[i]:
            if st.button(option["label"], key=f"opt_{i}"):
                handle_clarification_selection(option)

    custom = st.text_input("또는 직접 입력:", key="custom_clarification")
    if custom:
        handle_clarification_selection({"text": custom})
```

### 7.4 Loading State Pattern
```python
# Progress indicator during processing
with st.status("답변을 생성하고 있습니다...", expanded=True) as status:
    st.write("📚 관련 문서 검색 중...")
    # ... search documents

    st.write("🤖 답변 생성 중...")
    # ... generate response

    st.write("✅ 출처 확인 중...")
    # ... verify sources

    status.update(label="답변 완료!", state="complete")
```

### 7.5 Error Handling Pattern
```python
# Error display
try:
    response = get_chatbot_response(query)
except NetworkError:
    st.error("🔌 네트워크 오류가 발생했습니다.")
    if st.button("🔄 다시 시도"):
        st.rerun()
except TimeoutError:
    st.warning("⏱️ 응답 시간이 초과되었습니다. 질문을 더 간단히 해보세요.")
except NoResultsError:
    st.info("🔍 관련 문서를 찾을 수 없습니다. 다른 키워드로 검색해보세요.")
```

---

## 8. Component States Summary

### 8.1 Input Field States
| State | Visual | Behavior |
|-------|--------|----------|
| Empty | Placeholder visible | Submit disabled |
| Typing | Text visible, placeholder hidden | Submit enabled |
| Submitting | Disabled, spinner | Submit disabled |
| Error | Red border | Show error message |

### 8.2 Message States
| State | Visual | Behavior |
|-------|--------|----------|
| Sending | Dimmed, loading indicator | Non-interactive |
| Delivered | Full opacity | Interactive |
| Error | Red border, retry icon | Click to retry |

### 8.3 Button States
| State | Visual | Behavior |
|-------|--------|----------|
| Default | Normal color | Clickable |
| Hover | Highlighted | - |
| Active | Pressed effect | - |
| Disabled | Grayed out | Not clickable |
| Selected | Filled/highlighted | Toggle state |

---

## 9. Quick Reference Card

### Essential Flows
1. **Happy Path**: Input → Submit → Loading (8-9s) → Answer + Sources → Feedback
2. **HITL Path**: Input → Clarification Options → Select → Loading (10s) → Answer
3. **Error Path**: Input → Error → Error Message → Retry/Refine

### Key UI Elements (Korean Labels)
- Header: "사내 문서 검색 챗봇"
- Input placeholder: "질문을 입력하세요..."
- Submit button: "질문하기"
- Loading: "답변을 생성하고 있습니다..."
- Sources: "출처 보기"
- Feedback: "이 답변이 도움이 되었나요?"
- Error messages:
  - Network: "네트워크 오류가 발생했습니다"
  - No results: "관련 문서를 찾을 수 없습니다"
  - Timeout: "응답 시간이 초과되었습니다"
  - Low confidence: "이 답변은 신뢰도가 낮습니다"

### Timing Guidelines
| Operation | Expected Time | Max Time |
|-----------|---------------|----------|
| Simple query | 8-9 seconds | 15 seconds |
| Complex query | 13-15 seconds | 20 seconds |
| With HITL | 10s + user time | 30 seconds |

---

*Document generated by UX Designer Agent*
*Last updated: 2025-12-11*
