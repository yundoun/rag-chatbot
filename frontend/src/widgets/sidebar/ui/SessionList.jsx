import { SessionItem } from './SessionItem'

export function SessionList({
  sessions,
  currentSessionId,
  onSelectSession,
  onDeleteSession
}) {
  if (sessions.length === 0) {
    return (
      <div className="px-4 py-8 text-center">
        <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-dark-elevated flex items-center justify-center">
          <svg className="w-6 h-6 text-dark-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <p className="text-sm text-dark-text-muted">
          아직 대화가 없습니다
        </p>
        <p className="text-xs text-dark-text-muted mt-1">
          새 대화를 시작해보세요
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-1 px-2">
      {sessions.map(session => (
        <SessionItem
          key={session.id}
          session={session}
          isActive={session.id === currentSessionId}
          onClick={() => onSelectSession(session.id)}
          onDelete={onDeleteSession}
        />
      ))}
    </div>
  )
}

export default SessionList
