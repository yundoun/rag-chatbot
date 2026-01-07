import { IconMenu } from '@shared/ui'

export function ChatHeader({ title, onMenuClick }) {
  return (
    <header className="
      px-4 py-3
      bg-light-surface/80 backdrop-blur-xl
      border-b border-light-border
      flex items-center gap-3
    ">
      <button
        onClick={onMenuClick}
        className="lg:hidden p-2 rounded-lg hover:bg-light-elevated text-light-text-muted"
      >
        <IconMenu className="w-5 h-5" />
      </button>

      <h2 className="text-lg font-medium text-light-text-primary truncate">
        {title || '새 대화'}
      </h2>
    </header>
  )
}

export default ChatHeader
