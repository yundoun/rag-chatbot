import { useState, useEffect } from 'react'

const LOADING_MESSAGES = [
  { key: 'analyzing', text: '질문을 분석하고 있습니다...', icon: '🔍' },
  { key: 'searching', text: '관련 문서를 검색하고 있습니다...', icon: '📚' },
  { key: 'evaluating', text: '검색 결과를 평가하고 있습니다...', icon: '⚖️' },
  { key: 'generating', text: '답변을 생성하고 있습니다...', icon: '✍️' },
]

function LoadingIndicator({ isLoading, currentStep = null }) {
  const [messageIndex, setMessageIndex] = useState(0)

  useEffect(() => {
    if (!isLoading) {
      setMessageIndex(0)
      return
    }

    // Rotate through messages if no specific step provided
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
    <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
      {/* Spinner */}
      <div className="relative">
        <div className="w-8 h-8 border-4 border-primary-200 rounded-full"></div>
        <div className="absolute top-0 left-0 w-8 h-8 border-4 border-primary-500 rounded-full border-t-transparent animate-spin"></div>
      </div>

      {/* Message */}
      <div className="flex items-center space-x-2">
        <span className="text-xl">{currentMessage.icon}</span>
        <span className="text-gray-600">{currentMessage.text}</span>
      </div>
    </div>
  )
}

export default LoadingIndicator
