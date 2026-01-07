/**
 * 메시지 처리 상태 관리 스토어 (Zustand)
 *
 * 역할: 메시지 전송/수신 과정의 UI 상태를 관리
 * - 세션 데이터는 sessionStore에서 영속 관리
 * - 이 스토어는 일시적인 UI 상태만 관리 (새로고침 시 초기화됨)
 *
 * 상태 흐름:
 * ┌─────────────────────────────────────────────────────────────┐
 * │  [사용자 질문]                                              │
 * │       ↓                                                     │
 * │  isLoading: true                                            │
 * │       ↓                                                     │
 * │  currentStep: analyzing → searching → evaluating → generating
 * │       ↓                                                     │
 * │  [명확화 필요?] ─Yes→ pendingClarification 설정             │
 * │       │No                                                   │
 * │       ↓                                                     │
 * │  [응답 완료] → isLoading: false                             │
 * └─────────────────────────────────────────────────────────────┘
 */

import { create } from 'zustand'

export const useMessageStore = create((set, get) => ({
  // ============================================================
  // 상태 (State)
  // ============================================================

  /** @type {boolean} API 요청 진행 중 여부 */
  isLoading: false,

  /** @type {string|null} 현재 처리 단계 (analyzing, searching, evaluating, generating) */
  currentStep: null,

  /** @type {string[]} 완료된 처리 단계 목록 */
  completedSteps: [],

  /**
   * @type {Object|null} 명확화 요청 정보
   * { question: string, options: string[] }
   */
  pendingClarification: null,

  /** @type {string|null} 백엔드 세션 ID (명확화 대화 연속성 유지용) */
  backendSessionId: null,

  // ============================================================
  // 액션 (Actions)
  // ============================================================

  /**
   * 로딩 상태 설정
   * @param {boolean} isLoading
   */
  setLoading: (isLoading) => set({ isLoading }),

  /**
   * 현재 처리 단계 설정 (ProcessingSteps UI 표시용)
   * @param {string|null} step - 'analyzing' | 'searching' | 'evaluating' | 'generating' | null
   */
  setCurrentStep: (step) => set({ currentStep: step }),

  /**
   * 완료된 단계 추가 (체크 표시용)
   * @param {string} step
   */
  addCompletedStep: (step) => set(state => ({
    completedSteps: [...state.completedSteps, step]
  })),

  /**
   * 처리 단계 초기화 (새 질문 시작 시)
   */
  resetSteps: () => set({
    currentStep: null,
    completedSteps: [],
  }),

  /**
   * 명확화 요청 설정 (ClarificationDialog 표시)
   * @param {Object} clarification - { question: string, options: string[] }
   */
  setPendingClarification: (clarification) => set({
    pendingClarification: clarification
  }),

  /**
   * 명확화 요청 해제 (사용자 응답 후)
   */
  clearClarification: () => set({ pendingClarification: null }),

  /**
   * 백엔드 세션 ID 설정
   * - 첫 요청 시 백엔드에서 발급받은 세션 ID 저장
   * - 명확화 대화 시 동일 세션 유지에 필요
   * @param {string} sessionId
   */
  setBackendSessionId: (sessionId) => set({ backendSessionId: sessionId }),

  /**
   * 전체 상태 초기화 (세션 전환 시)
   */
  reset: () => set({
    isLoading: false,
    currentStep: null,
    completedSteps: [],
    pendingClarification: null,
    backendSessionId: null,
  }),
}))
