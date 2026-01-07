/**
 * 채팅 패널 위젯 컴포넌트
 *
 * FSD 아키텍처의 widgets 레이어
 * - 채팅 메시지 표시 및 입력 영역 통합
 * - 로딩 상태 및 명확화 다이얼로그 관리
 *
 * 구조:
 * ┌─────────────────────────────────────────────────────────────┐
 * │  ChatHeader (세션 제목 + 메뉴 버튼)                          │
 * ├─────────────────────────────────────────────────────────────┤
 * │                                                             │
 * │  MessageList 또는 EmptyState                                │
 * │    ├─ MessageBubble (user)                                  │
 * │    ├─ MessageBubble (assistant)                             │
 * │    ├─ ClarificationDialog (명확화 필요 시)                  │
 * │    └─ LoadingIndicator + ProcessingSteps (로딩 시)          │
 * │                                                             │
 * ├─────────────────────────────────────────────────────────────┤
 * │  ChatInput (메시지 입력)                                    │
 * └─────────────────────────────────────────────────────────────┘
 *
 * 데이터 흐름:
 * - sessionStore: 현재 세션 및 메시지 데이터
 * - messageStore: 로딩, 처리 단계, 명확화 상태
 * - useSendMessage: 메시지 전송 로직
 */

import { useSessionStore } from '@entities/session'
import { useMessageStore } from '@entities/message'
import { ChatInput, useSendMessage } from '@features/send-message'
import { ClarificationDialog } from '@features/clarification'
import { LoadingIndicator, ProcessingSteps } from '@features/processing-status'
import { ChatHeader } from './ChatHeader'
import { MessageList } from './MessageList'
import { EmptyState } from './EmptyState'

export function ChatPanel({ onMenuClick }) {
  // ============================================================
  // 스토어 상태
  // ============================================================

  // 현재 세션 데이터
  const currentSession = useSessionStore(state => state.getCurrentSession())

  // UI 상태 (로딩, 명확화, 처리 단계)
  const {
    isLoading,
    pendingClarification,
    currentStep,
    completedSteps
  } = useMessageStore()

  // 메시지 전송 훅
  const { sendMessage, sendClarification } = useSendMessage()

  // 현재 세션의 메시지 목록
  const messages = currentSession?.messages || []

  // ============================================================
  // 렌더링
  // ============================================================

  return (
    <div className="flex flex-col h-full bg-light-bg">
      {/* 헤더: 세션 제목 + 모바일 메뉴 버튼 */}
      <ChatHeader
        title={currentSession?.title}
        onMenuClick={onMenuClick}
      />

      {/* 메시지 영역 (스크롤) */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && !isLoading ? (
          // 메시지 없음: 빈 상태 + 추천 질문
          <EmptyState />
        ) : (
          // 메시지 목록
          <div className="max-w-3xl mx-auto">
            <MessageList messages={messages} />

            {/* 명확화 다이얼로그 (백엔드가 추가 정보 요청 시) */}
            {pendingClarification && (
              <div className="mt-4">
                <ClarificationDialog
                  question={pendingClarification.question}
                  options={pendingClarification.options}
                  onSubmit={sendClarification}
                  disabled={isLoading}
                />
              </div>
            )}

            {/* 로딩 인디케이터 및 처리 단계 표시 */}
            {isLoading && (
              <div className="mt-4 space-y-4">
                <LoadingIndicator
                  isLoading={isLoading}
                  currentStep={currentStep}
                />
                {currentStep && (
                  <ProcessingSteps
                    currentStep={currentStep}
                    completedSteps={completedSteps}
                  />
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 메시지 입력 영역 */}
      <ChatInput
        onSend={sendMessage}
        disabled={isLoading}
      />
    </div>
  )
}

export default ChatPanel
