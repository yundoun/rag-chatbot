import { useState, useRef, useEffect, useCallback } from 'react'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'
import LoadingIndicator from './LoadingIndicator'
import ProcessingSteps from './ProcessingSteps'
import ClarificationDialog from './ClarificationDialog'
import { sendMessage, sendClarificationResponse } from '../services/api'
import useWebSocket, { ConnectionState } from '../hooks/useWebSocket'

function ChatContainer() {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [showProcessingSteps, setShowProcessingSteps] = useState(false)
  const [currentStep, setCurrentStep] = useState(null)
  const [completedSteps, setCompletedSteps] = useState([])
  const [pendingClarification, setPendingClarification] = useState(null)
  const [useWebSocketMode, setUseWebSocketMode] = useState(false)
  const messagesEndRef = useRef(null)

  // WebSocket handlers
  const handleWsProgress = useCallback((data) => {
    setCurrentStep(data.step)
  }, [])

  const handleWsClarification = useCallback((data) => {
    setPendingClarification({
      question: data.question,
      options: data.options || [],
      allowCustomInput: data.allow_custom_input !== false,
    })
    setIsLoading(false)
  }, [])

  const handleWsResponse = useCallback((data) => {
    const assistantMessage = {
      id: Date.now(),
      type: 'assistant',
      content: data.response,
      sources: data.sources,
      confidence: data.confidence,
      needsDisclaimer: data.needs_disclaimer,
      retrievalSource: data.retrieval_source,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, assistantMessage])
    setIsLoading(false)
    setPendingClarification(null)
  }, [])

  const handleWsError = useCallback((error, detail) => {
    const errorMessage = {
      id: Date.now(),
      type: 'error',
      content: error || '오류가 발생했습니다.',
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, errorMessage])
    setIsLoading(false)
  }, [])

  // WebSocket hook
  const {
    connectionState,
    isConnected,
    sessionId: wsSessionId,
    connect: wsConnect,
    disconnect: wsDisconnect,
    sendQuestion: wsSendQuestion,
    sendClarification: wsSendClarification,
  } = useWebSocket({
    onProgress: handleWsProgress,
    onClarification: handleWsClarification,
    onResponse: handleWsResponse,
    onError: handleWsError,
  })

  // Use WebSocket session ID if available
  useEffect(() => {
    if (wsSessionId && !sessionId) {
      setSessionId(wsSessionId)
    }
  }, [wsSessionId, sessionId])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  // Simulate processing steps progression
  useEffect(() => {
    if (!isLoading) {
      setCurrentStep(null)
      setCompletedSteps([])
      return
    }

    const steps = ['analyzing', 'searching', 'evaluating', 'generating']
    let stepIndex = 0

    const advanceStep = () => {
      if (stepIndex < steps.length) {
        if (stepIndex > 0) {
          setCompletedSteps((prev) => [...prev, steps[stepIndex - 1]])
        }
        setCurrentStep(steps[stepIndex])
        stepIndex++
      }
    }

    // Start with first step
    advanceStep()

    // Advance through steps (simulated timing)
    const interval = setInterval(() => {
      if (stepIndex < steps.length) {
        advanceStep()
      }
    }, 1500)

    return () => clearInterval(interval)
  }, [isLoading])

  const handleSendMessage = async (content) => {
    if (!content.trim() || isLoading) return

    // Add user message
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: content,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    // Use WebSocket if connected, otherwise fall back to REST API
    if (useWebSocketMode && isConnected) {
      wsSendQuestion(content)
      return
    }

    try {
      // Send to API
      const response = await sendMessage(content, sessionId)

      // Update session ID
      if (response.session_id && !sessionId) {
        setSessionId(response.session_id)
      }

      // Check if clarification is needed
      if (response.clarification_question) {
        setPendingClarification({
          question: response.clarification_question,
          options: response.options || [],
          allowCustomInput: true,
        })
        setIsLoading(false)
        return
      }

      // Add assistant message with debug info if available
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.response,
        sources: response.sources,
        confidence: response.confidence,
        needsDisclaimer: response.needs_disclaimer,
        processingTime: response.processing_time_ms,
        retrievalSource: response.retrieval_source,
        debug: response.debug,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: error.message || '오류가 발생했습니다. 다시 시도해 주세요.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  // Handle clarification response
  const handleClarificationSubmit = async (selectedOption, customInput) => {
    const responseText = customInput || selectedOption
    if (!responseText) return

    // Add user's clarification as a message
    const clarificationMessage = {
      id: Date.now(),
      type: 'user',
      content: responseText,
      isClarification: true,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, clarificationMessage])
    setIsLoading(true)
    setPendingClarification(null)

    // Use WebSocket if connected
    if (useWebSocketMode && isConnected) {
      wsSendClarification(selectedOption, customInput)
      return
    }

    try {
      // Send clarification response via REST API
      const response = await sendClarificationResponse(sessionId, responseText)

      // Check if another clarification is needed
      if (response.clarification_question) {
        setPendingClarification({
          question: response.clarification_question,
          options: response.options || [],
          allowCustomInput: true,
        })
        setIsLoading(false)
        return
      }

      // Add assistant message
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.response,
        sources: response.sources,
        confidence: response.confidence,
        needsDisclaimer: response.needs_disclaimer,
        processingTime: response.processing_time_ms,
        retrievalSource: response.retrieval_source,
        debug: response.debug,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: error.message || '오류가 발생했습니다.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const toggleProcessingSteps = () => {
    setShowProcessingSteps((prev) => !prev)
  }

  return (
    <div className="bg-white rounded-lg shadow-lg flex flex-col h-[calc(100vh-200px)]">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <svg
              className="w-16 h-16 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            <p className="text-lg font-medium">질문을 입력하세요</p>
            <p className="text-sm">내부 문서를 검색하여 답변해 드립니다</p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {/* Clarification Dialog */}
            {pendingClarification && (
              <div className="py-4">
                <ClarificationDialog
                  question={pendingClarification.question}
                  options={pendingClarification.options}
                  allowCustomInput={pendingClarification.allowCustomInput}
                  onSubmit={handleClarificationSubmit}
                  disabled={isLoading}
                />
              </div>
            )}

            {isLoading && (
              <div className="space-y-3">
                <LoadingIndicator isLoading={isLoading} currentStep={currentStep} />

                {/* Toggle for detailed steps */}
                <button
                  onClick={toggleProcessingSteps}
                  className="text-xs text-gray-400 hover:text-gray-600 flex items-center space-x-1"
                >
                  <span>{showProcessingSteps ? '상세 숨기기' : '상세 보기'}</span>
                  <svg
                    className={`w-4 h-4 transform transition-transform ${
                      showProcessingSteps ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>

                {showProcessingSteps && (
                  <ProcessingSteps
                    currentStep={currentStep}
                    completedSteps={completedSteps}
                  />
                )}
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <ChatInput onSend={handleSendMessage} disabled={isLoading} />
    </div>
  )
}

export default ChatContainer
