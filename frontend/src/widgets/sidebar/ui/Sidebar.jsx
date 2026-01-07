/**
 * 사이드바 위젯 컴포넌트
 *
 * FSD 아키텍처의 widgets 레이어
 * - 세션 목록 표시 및 관리
 * - 새 대화 생성 버튼
 * - 반응형 슬라이드 동작
 *
 * 구조:
 * ┌─────────────────────────────────────────┐
 * │  ┌─────────────────────────────────┐    │
 * │  │  로고 + 앱 이름     [닫기 버튼] │    │  ← 헤더 (모바일에서 닫기 버튼 표시)
 * │  │  [+ 새 대화] 버튼              │    │
 * │  └─────────────────────────────────┘    │
 * │  ┌─────────────────────────────────┐    │
 * │  │  SessionList                   │    │  ← 세션 목록 (스크롤 가능)
 * │  │    ├─ SessionItem              │    │
 * │  │    ├─ SessionItem              │    │
 * │  │    └─ ...                      │    │
 * │  └─────────────────────────────────┘    │
 * │  ┌─────────────────────────────────┐    │
 * │  │  안내 문구                      │    │  ← 푸터
 * │  └─────────────────────────────────┘    │
 * └─────────────────────────────────────────┘
 *
 * 반응형:
 * - 모바일: 오버레이 + 슬라이드 애니메이션
 * - 데스크탑: 항상 표시, 정적 위치
 */

import { useSessionStore } from '@entities/session'
import { useMessageStore } from '@entities/message'
import { NewSessionButton } from '@features/session-management'
import { SessionList } from './SessionList'
import { IconClose } from '@shared/ui'
import { APP_NAME } from '@shared/config'

export function Sidebar({ isOpen, onClose }) {
  // ============================================================
  // 스토어 상태 및 액션
  // ============================================================

  const sessions = useSessionStore(state => state.sessions)
  const currentSessionId = useSessionStore(state => state.currentSessionId)
  const selectSession = useSessionStore(state => state.selectSession)
  const deleteSession = useSessionStore(state => state.deleteSession)
  const reset = useMessageStore(state => state.reset)

  // ============================================================
  // 이벤트 핸들러
  // ============================================================

  /**
   * 세션 선택 시
   * - 메시지 스토어 초기화 (이전 세션의 UI 상태 제거)
   * - 새 세션 선택
   * - 모바일에서 사이드바 닫기
   */
  const handleSelectSession = (sessionId) => {
    reset()
    selectSession(sessionId)
    onClose?.()
  }

  /**
   * 세션 삭제 시 확인 다이얼로그
   */
  const handleDeleteSession = (sessionId) => {
    if (confirm('이 대화를 삭제하시겠습니까?')) {
      deleteSession(sessionId)
    }
  }

  // ============================================================
  // 렌더링
  // ============================================================

  return (
    <>
      {/* 모바일 오버레이 배경 */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* 사이드바 본체 */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-72
        bg-light-surface border-r border-light-border
        flex flex-col shadow-lg
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static lg:z-auto lg:shadow-none
      `}>
        {/* 헤더 영역 */}
        <div className="p-4 border-b border-light-border">
          <div className="flex items-center justify-between mb-4">
            {/* 로고 및 앱 이름 */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-500 to-mint-500 flex items-center justify-center">
                <span className="text-white text-sm">📚</span>
              </div>
              <h1 className="text-lg font-semibold text-light-text-primary">
                {APP_NAME}
              </h1>
            </div>

            {/* 모바일 닫기 버튼 */}
            <button
              onClick={onClose}
              className="lg:hidden p-2 rounded-lg hover:bg-light-elevated text-light-text-muted"
            >
              <IconClose className="w-5 h-5" />
            </button>
          </div>

          {/* 새 대화 버튼 */}
          <NewSessionButton />
        </div>

        {/* 세션 목록 (스크롤 영역) */}
        <div className="flex-1 overflow-y-auto py-4">
          <SessionList
            sessions={sessions}
            currentSessionId={currentSessionId}
            onSelectSession={handleSelectSession}
            onDeleteSession={handleDeleteSession}
          />
        </div>

        {/* 푸터 안내 문구 */}
        <div className="p-4 border-t border-light-border">
          <p className="text-xs text-light-text-muted text-center">
            내부 문서를 검색하여 질문에 답변합니다
          </p>
        </div>
      </aside>
    </>
  )
}

export default Sidebar
