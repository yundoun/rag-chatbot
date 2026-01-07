import { useSessionStore } from '@entities/session'
import { useMessageStore } from '@entities/message'
import { Button, IconPlus } from '@shared/ui'

export function NewSessionButton({ className = '' }) {
  const createSession = useSessionStore(state => state.createSession)
  const reset = useMessageStore(state => state.reset)

  const handleNewSession = () => {
    reset()
    createSession()
  }

  return (
    <Button
      variant="primary"
      onClick={handleNewSession}
      className={`w-full ${className}`}
    >
      <IconPlus className="w-4 h-4" />
      <span>새 대화</span>
    </Button>
  )
}

export default NewSessionButton
