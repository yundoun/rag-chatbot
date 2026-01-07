/**
 * 메시지 전송 훅 (useSendMessage)
 *
 * 역할: 사용자 질문 전송 및 응답 처리 로직을 캡슐화
 *
 * 데이터 흐름:
 * ┌─────────────────────────────────────────────────────────────┐
 * │  ChatInput                                                  │
 * │     │ onSend(content)                                       │
 * │     ↓                                                       │
 * │  useSendMessage.sendMessage(content)                        │
 * │     │                                                       │
 * │     ├─→ 1. 세션 없으면 생성 (createSession)                 │
 * │     ├─→ 2. 사용자 메시지 저장 (addMessage)                  │
 * │     ├─→ 3. 로딩 시작 + 처리 단계 애니메이션                 │
 * │     ├─→ 4. API 요청 (sendMessage)                           │
 * │     │                                                       │
 * │     ↓                                                       │
 * │  [응답 분기]                                                │
 * │     ├─→ 명확화 필요: setPendingClarification                │
 * │     └─→ 일반 응답: addMessage(assistant)                    │
 * └─────────────────────────────────────────────────────────────┘
 *
 * 사용 예시:
 * const { sendMessage, sendClarification } = useSendMessage()
 * sendMessage('친구추천 기능이 뭐야?')
 */

import { useCallback } from 'react'
import { useSessionStore } from '@entities/session'
import { useMessageStore } from '@entities/message'
import { sendMessage, sendClarificationResponse } from '../api/sendMessage'

export function useSendMessage() {
  // ============================================================
  // 스토어 액션 및 상태 추출
  // ============================================================

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

  // ============================================================
  // 일반 메시지 전송 핸들러
  // ============================================================

  /**
   * 사용자 질문 전송
   * @param {string} content - 질문 내용
   */
  const handleSend = useCallback(async (content) => {
    // 1. 현재 세션 확인 및 생성
    let session = getCurrentSession()

    if (!session) {
      createSession()
      session = getCurrentSession()
    }

    if (!content.trim() || !session) return

    // 2. 사용자 메시지 객체 생성 및 저장
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: content.trim(),
      timestamp: new Date(),
    }

    addMessage(session.id, userMessage)

    // 3. UI 상태 업데이트 (로딩 시작)
    setLoading(true)
    resetSteps()

    // 4. 처리 단계 애니메이션 (1.5초 간격으로 단계 전환)
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
      // 5. API 요청
      const response = await sendMessage(content, backendSessionId)

      // 6. 애니메이션 정리 및 완료 처리
      clearInterval(stepInterval)
      steps.forEach(step => addCompletedStep(step))
      setCurrentStep(null)

      // 7. 백엔드 세션 ID 저장 (첫 요청 시)
      if (response.session_id && !backendSessionId) {
        setBackendSessionId(response.session_id)
      }

      // 8. 응답 분기 처리
      if (response.clarification_question) {
        // 명확화 필요 → 다이얼로그 표시
        setPendingClarification({
          question: response.clarification_question,
          options: response.options || [],
        })
        setLoading(false)
        return
      }

      // 9. 어시스턴트 응답 메시지 생성 및 저장
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.response,
        sources: response.sources || [],           // 참조 문서 목록
        confidence: response.confidence,            // 신뢰도 점수
        needsDisclaimer: response.needs_disclaimer, // 면책 조항 필요 여부
        retrievalSource: response.retrieval_source, // 'vector' | 'web' | 'hybrid'
        processingTime: response.processing_time_ms,
        timestamp: new Date(),
      }

      addMessage(session.id, assistantMessage)
    } catch (error) {
      // 에러 처리
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

  // ============================================================
  // 명확화 응답 핸들러
  // ============================================================

  /**
   * 명확화 질문에 대한 사용자 응답 전송
   * @param {string|null} selectedOption - 선택된 옵션
   * @param {string|null} customInput - 직접 입력 내용
   */
  const handleClarification = useCallback(async (selectedOption, customInput) => {
    const session = getCurrentSession()
    if (!session || !backendSessionId) return

    const userResponse = customInput || selectedOption

    // 1. 사용자 응답 메시지 저장 (명확화 표시 포함)
    const clarificationMessage = {
      id: Date.now(),
      type: 'user',
      content: userResponse,
      isClarification: true,  // 명확화 응답임을 표시
      timestamp: new Date(),
    }

    addMessage(session.id, clarificationMessage)
    clearClarification()
    setLoading(true)

    try {
      // 2. API 요청 (동일 세션 ID로 연속 대화)
      const response = await sendClarificationResponse(backendSessionId, userResponse)

      // 3. 추가 명확화 필요 시 재귀적 처리
      if (response.clarification_question) {
        setPendingClarification({
          question: response.clarification_question,
          options: response.options || [],
        })
        setLoading(false)
        return
      }

      // 4. 최종 응답 저장
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

  // ============================================================
  // 반환 인터페이스
  // ============================================================

  return {
    sendMessage: handleSend,           // 일반 질문 전송
    sendClarification: handleClarification,  // 명확화 응답 전송
  }
}
