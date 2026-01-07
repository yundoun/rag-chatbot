import { useCallback } from 'react'
import { useSessionStore } from '@entities/session'
import { useMessageStore } from '@entities/message'
import { sendMessage, sendClarificationResponse } from '../api/sendMessage'

export function useSendMessage() {
  const {
    getCurrentSession,
    addMessage,
    createSession,
    currentSessionId
  } = useSessionStore()

  const {
    setLoading,
    setPendingClarification,
    clearClarification,
    setBackendSessionId,
    backendSessionId,
    setCurrentStep,
    addCompletedStep,
    resetSteps
  } = useMessageStore()

  const handleSend = useCallback(async (content) => {
    let session = getCurrentSession()

    if (!session) {
      createSession()
      session = getCurrentSession()
    }

    if (!content.trim() || !session) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: content.trim(),
      timestamp: new Date(),
    }

    addMessage(session.id, userMessage)
    setLoading(true)
    resetSteps()

    const steps = ['analyzing', 'searching', 'evaluating', 'generating']
    let stepIndex = 0

    const stepInterval = setInterval(() => {
      if (stepIndex < steps.length) {
        if (stepIndex > 0) {
          addCompletedStep(steps[stepIndex - 1])
        }
        setCurrentStep(steps[stepIndex])
        stepIndex++
      }
    }, 1500)

    try {
      const response = await sendMessage(content, backendSessionId)

      clearInterval(stepInterval)
      steps.forEach(step => addCompletedStep(step))
      setCurrentStep(null)

      if (response.session_id && !backendSessionId) {
        setBackendSessionId(response.session_id)
      }

      if (response.clarification_question) {
        setPendingClarification({
          question: response.clarification_question,
          options: response.options || [],
        })
        setLoading(false)
        return
      }

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.response,
        sources: response.sources || [],
        confidence: response.confidence,
        needsDisclaimer: response.needs_disclaimer,
        retrievalSource: response.retrieval_source,
        processingTime: response.processing_time_ms,
        timestamp: new Date(),
      }

      addMessage(session.id, assistantMessage)
    } catch (error) {
      clearInterval(stepInterval)

      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: error.message || '오류가 발생했습니다.',
        timestamp: new Date(),
      }

      addMessage(session.id, errorMessage)
    } finally {
      setLoading(false)
      resetSteps()
    }
  }, [
    getCurrentSession,
    addMessage,
    createSession,
    setLoading,
    setPendingClarification,
    clearClarification,
    setBackendSessionId,
    backendSessionId,
    setCurrentStep,
    addCompletedStep,
    resetSteps
  ])

  const handleClarification = useCallback(async (selectedOption, customInput) => {
    const session = getCurrentSession()
    if (!session || !backendSessionId) return

    const userResponse = customInput || selectedOption

    const clarificationMessage = {
      id: Date.now(),
      type: 'user',
      content: userResponse,
      isClarification: true,
      timestamp: new Date(),
    }

    addMessage(session.id, clarificationMessage)
    clearClarification()
    setLoading(true)

    try {
      const response = await sendClarificationResponse(backendSessionId, userResponse)

      if (response.clarification_question) {
        setPendingClarification({
          question: response.clarification_question,
          options: response.options || [],
        })
        setLoading(false)
        return
      }

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.response,
        sources: response.sources || [],
        confidence: response.confidence,
        needsDisclaimer: response.needs_disclaimer,
        retrievalSource: response.retrieval_source,
        processingTime: response.processing_time_ms,
        timestamp: new Date(),
      }

      addMessage(session.id, assistantMessage)
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: error.message || '오류가 발생했습니다.',
        timestamp: new Date(),
      }

      addMessage(session.id, errorMessage)
    } finally {
      setLoading(false)
    }
  }, [
    getCurrentSession,
    addMessage,
    backendSessionId,
    clearClarification,
    setLoading,
    setPendingClarification
  ])

  return {
    sendMessage: handleSend,
    sendClarification: handleClarification,
  }
}
