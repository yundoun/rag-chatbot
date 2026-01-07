import { useState, useEffect } from 'react'

const LOADING_MESSAGES = [
  { key: 'analyzing', text: '질문을 분석하고 있습니다...', icon: '🔍' },
  { key: 'searching', text: '관련 문서를 검색하고 있습니다...', icon: '📚' },
  { key: 'evaluating', text: '검색 결과를 평가하고 있습니다...', icon: '⚖️' },
  { key: 'generating', text: '답변을 생성하고 있습니다...', icon: '✍️' },
]

export function LoadingIndicator({ isLoading, currentStep = null }) {
  const [messageIndex, setMessageIndex] = useState(0)

  useEffect(() => {
    if (!isLoading) {
      setMessageIndex(0)
      return
    }

    if (currentStep === null) {
      const interval = setInterval(() => {
        setMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length)
      }, 2000)

      return () => clearInterval(interval)
    }
  }, [isLoading, currentStep])

  if (!isLoading) return null

  const currentMessage = currentStep
    ? LOADING_MESSAGES.find((m) => m.key === currentStep) || LOADING_MESSAGES[0]
    : LOADING_MESSAGES[messageIndex]

  return (
    <div className="
      flex items-center gap-4 p-4
      bg-white
      rounded-xl border border-light-border
      shadow-sm animate-fade-in
    ">
      <div className="relative">
        <div className="w-10 h-10 border-4 border-light-border rounded-full" />
        <div className="
          absolute top-0 left-0 w-10 h-10
          border-4 border-accent-500 rounded-full
          border-t-transparent animate-spin
        " />
      </div>

      <div className="flex items-center gap-3">
        <span className="text-2xl">{currentMessage.icon}</span>
        <span className="text-light-text-secondary">{currentMessage.text}</span>
      </div>
    </div>
  )
}

export default LoadingIndicator
