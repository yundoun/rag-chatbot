import { useSessionStore } from '@entities/session'
import { useMessageStore } from '@entities/message'
import { NewSessionButton } from '@features/session-management'
import { SessionList } from './SessionList'
import { IconClose } from '@shared/ui'
import { APP_NAME } from '@shared/config'

export function Sidebar({ isOpen, onClose }) {
  const sessions = useSessionStore(state => state.sessions)
  const currentSessionId = useSessionStore(state => state.currentSessionId)
  const selectSession = useSessionStore(state => state.selectSession)
  const deleteSession = useSessionStore(state => state.deleteSession)
  const reset = useMessageStore(state => state.reset)

  const handleSelectSession = (sessionId) => {
    reset()
    selectSession(sessionId)
    onClose?.()
  }

  const handleDeleteSession = (sessionId) => {
    if (confirm('이 대화를 삭제하시겠습니까?')) {
      deleteSession(sessionId)
    }
  }

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside className={`
        fixed inset-y-0 left-0 z-50 w-72
        bg-light-surface border-r border-light-border
        flex flex-col shadow-lg
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static lg:z-auto lg:shadow-none
      `}>
        <div className="p-4 border-b border-light-border">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-500 to-mint-500 flex items-center justify-center">
                <span className="text-white text-sm">📚</span>
              </div>
              <h1 className="text-lg font-semibold text-light-text-primary">
                {APP_NAME}
              </h1>
            </div>
            <button
              onClick={onClose}
              className="lg:hidden p-2 rounded-lg hover:bg-light-elevated text-light-text-muted"
            >
              <IconClose className="w-5 h-5" />
            </button>
          </div>

          <NewSessionButton />
        </div>

        <div className="flex-1 overflow-y-auto py-4">
          <SessionList
            sessions={sessions}
            currentSessionId={currentSessionId}
            onSelectSession={handleSelectSession}
            onDeleteSession={handleDeleteSession}
          />
        </div>

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
