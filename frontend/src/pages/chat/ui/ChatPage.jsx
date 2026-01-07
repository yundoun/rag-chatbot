/**
 * 채팅 페이지 컴포넌트
 *
 * FSD 아키텍처의 pages 레이어
 * - 페이지 레벨 레이아웃 구성
 * - 사이드바 토글 상태 관리
 *
 * 레이아웃:
 * ┌─────────────────────────────────────────────────────────────┐
 * │  ┌──────────────┬────────────────────────────────────────┐  │
 * │  │              │                                        │  │
 * │  │   Sidebar    │           ChatPanel                    │  │
 * │  │   (세션)     │           (메시지)                     │  │
 * │  │              │                                        │  │
 * │  │   w-72       │           flex-1                       │  │
 * │  │              │                                        │  │
 * │  └──────────────┴────────────────────────────────────────┘  │
 * └─────────────────────────────────────────────────────────────┘
 *
 * 반응형 동작:
 * - 모바일 (< lg): 사이드바 슬라이드 오버레이
 * - 데스크탑 (>= lg): 사이드바 항상 표시
 */

import { useState } from 'react'
import { Sidebar } from '@widgets/sidebar'
import { ChatPanel } from '@widgets/chat-panel'

export function ChatPage() {
  // 모바일에서 사이드바 열림/닫힘 상태
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen bg-light-bg text-light-text-primary">
      {/* 세션 목록 사이드바 */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* 메인 채팅 영역 */}
      <main className="flex-1 flex flex-col min-w-0">
        <ChatPanel
          onMenuClick={() => setSidebarOpen(true)}
        />
      </main>
    </div>
  )
}

export default ChatPage
