import { useSessionStore } from '@entities/session'
import { useMessageStore } from '@entities/message'
import { ChatInput, useSendMessage } from '@features/send-message'
import { ClarificationDialog } from '@features/clarification'
import { LoadingIndicator, ProcessingSteps } from '@features/processing-status'
import { ChatHeader } from './ChatHeader'
import { MessageList } from './MessageList'
import { EmptyState } from './EmptyState'

export function ChatPanel({ onMenuClick }) {
  const currentSession = useSessionStore(state => state.getCurrentSession())
  const {
    isLoading,
    pendingClarification,
    currentStep,
    completedSteps
  } = useMessageStore()

  const { sendMessage, sendClarification } = useSendMessage()

  const messages = currentSession?.messages || []

  return (
    <div className="flex flex-col h-full bg-light-bg">
      <ChatHeader
        title={currentSession?.title}
        onMenuClick={onMenuClick}
      />

      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && !isLoading ? (
          <EmptyState />
        ) : (
          <div className="max-w-3xl mx-auto">
            <MessageList messages={messages} />

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

      <ChatInput
        onSend={sendMessage}
        disabled={isLoading}
      />
    </div>
  )
}

export default ChatPanel
