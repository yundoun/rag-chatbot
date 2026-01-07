import { useState, useRef, useEffect } from 'react'
import { IconSend, IconSpinner } from '@shared/ui'

export function ChatInput({ onSend, disabled }) {
  const [input, setInput] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        120
      )}px`
    }
  }, [input])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (input.trim() && !disabled) {
      onSend(input)
      setInput('')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-light-border p-4 bg-light-surface/80 backdrop-blur-xl"
    >
      <div className="flex items-end gap-3">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="질문을 입력하세요... (Shift+Enter로 줄바꿈)"
          disabled={disabled}
          rows={1}
          className="
            flex-1 resize-none rounded-xl px-4 py-3
            bg-white border border-light-border
            text-light-text-primary placeholder-light-text-muted
            focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-transparent
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-all duration-200
            shadow-sm
          "
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="
            p-3 rounded-xl
            bg-gradient-to-r from-accent-500 to-accent-600
            text-white
            hover:shadow-glow-blue
            disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none
            transition-all duration-200
            flex items-center justify-center
          "
        >
          {disabled ? (
            <IconSpinner className="w-5 h-5" />
          ) : (
            <IconSend className="w-5 h-5" />
          )}
        </button>
      </div>
    </form>
  )
}

export default ChatInput
