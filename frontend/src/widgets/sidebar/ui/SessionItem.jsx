import { IconChat, IconTrash } from '@shared/ui'

export function SessionItem({
  session,
  isActive,
  onClick,
  onDelete
}) {
  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))

    if (diffDays === 0) {
      return date.toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit'
      })
    } else if (diffDays === 1) {
      return '어제'
    } else if (diffDays < 7) {
      return `${diffDays}일 전`
    } else {
      return date.toLocaleDateString('ko-KR', {
        month: 'short',
        day: 'numeric'
      })
    }
  }

  const handleDelete = (e) => {
    e.stopPropagation()
    onDelete?.(session.id)
  }

  return (
    <div
      onClick={onClick}
      className={`
        group relative px-3 py-3 rounded-xl cursor-pointer
        transition-all duration-200
        ${isActive
          ? 'bg-accent-500/10 border border-accent-500/30'
          : 'hover:bg-light-elevated border border-transparent'
        }
      `}
    >
      <div className="flex items-start gap-3">
        <div className={`
          p-2 rounded-lg
          ${isActive ? 'bg-accent-500/20' : 'bg-light-elevated'}
        `}>
          <IconChat className={`w-4 h-4 ${isActive ? 'text-accent-500' : 'text-light-text-muted'}`} />
        </div>

        <div className="flex-1 min-w-0">
          <h3 className={`
            text-sm font-medium truncate
            ${isActive ? 'text-accent-600' : 'text-light-text-primary'}
          `}>
            {session.title}
          </h3>
          <p className="text-xs text-light-text-muted mt-0.5">
            {formatDate(session.updatedAt)}
            {session.messages.length > 0 && (
              <span className="ml-2">· {session.messages.length}개 메시지</span>
            )}
          </p>
        </div>

        <button
          onClick={handleDelete}
          className="
            opacity-0 group-hover:opacity-100
            p-1.5 rounded-lg
            text-light-text-muted hover:text-red-500
            hover:bg-red-500/10
            transition-all duration-200
          "
        >
          <IconTrash className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

export default SessionItem
