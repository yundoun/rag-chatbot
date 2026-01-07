/**
 * 앱 루트 컴포넌트
 *
 * FSD 아키텍처의 최상위 레이어 (app)
 * - 전역 프로바이더 설정
 * - 라우팅 설정 (현재는 단일 페이지)
 * - 전역 스타일 적용
 *
 * 레이아웃 구조:
 * ┌─────────────────────────────────────────────────────────────┐
 * │  App                                                        │
 * │  └─ ChatPage                                                │
 * │      ├─ Sidebar (세션 목록)                                 │
 * │      └─ ChatPanel (채팅 영역)                               │
 * │          ├─ ChatHeader                                      │
 * │          ├─ MessageList                                     │
 * │          └─ ChatInput                                       │
 * └─────────────────────────────────────────────────────────────┘
 */

import { ChatPage } from '@pages/chat'

function App() {
  return <ChatPage />
}

export default App
