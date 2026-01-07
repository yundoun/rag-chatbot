/**
 * 세션 상태 관리 스토어 (Zustand + LocalStorage Persist)
 *
 * 역할: 채팅 세션과 메시지 히스토리를 관리하고 브라우저에 영속화
 *
 * 데이터 구조:
 * ┌─────────────────────────────────────────────────────────────┐
 * │ Session {                                                   │
 * │   id: string (UUID)        - 고유 식별자                    │
 * │   title: string            - 세션 제목 (첫 질문에서 생성)   │
 * │   messages: Message[]      - 대화 메시지 배열               │
 * │   createdAt: ISO string    - 생성 시각                      │
 * │   updatedAt: ISO string    - 최종 수정 시각                 │
 * │ }                                                           │
 * │                                                             │
 * │ Message {                                                   │
 * │   id: number               - 메시지 ID (timestamp)          │
 * │   type: 'user'|'assistant'|'error'                          │
 * │   content: string          - 메시지 내용                    │
 * │   sources?: string[]       - 참조 문서 목록 (assistant)     │
 * │   confidence?: number      - 신뢰도 점수 (assistant)        │
 * │   timestamp: Date          - 전송 시각                      │
 * │ }                                                           │
 * └─────────────────────────────────────────────────────────────┘
 *
 * LocalStorage 키: 'rag-chatbot-sessions'
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * UUID 생성 유틸리티
 * @returns {string} 랜덤 UUID
 */
const generateId = () => crypto.randomUUID()

/**
 * 세션 제목 생성
 * 첫 번째 사용자 메시지에서 최대 50자까지 추출
 * @param {string} content - 메시지 내용
 * @returns {string} 생성된 제목
 */
const generateTitle = (content) => {
  if (!content) return '새 대화'
  // 마크다운 기호 제거 후 50자로 제한
  const cleaned = content.replace(/[#*`\n]/g, ' ').trim()
  return cleaned.length > 50 ? cleaned.slice(0, 47) + '...' : cleaned
}

export const useSessionStore = create(
  persist(
    (set, get) => ({
      // ============================================================
      // 상태 (State)
      // ============================================================

      /** @type {Session[]} 전체 세션 목록 (최신순 정렬) */
      sessions: [],

      /** @type {string|null} 현재 선택된 세션 ID */
      currentSessionId: null,

      // ============================================================
      // 액션 (Actions)
      // ============================================================

      /**
       * 새 세션 생성
       * - 새 세션을 목록 맨 앞에 추가
       * - 자동으로 현재 세션으로 선택
       * @returns {string} 생성된 세션 ID
       */
      createSession: () => {
        const newSession = {
          id: generateId(),
          title: '새 대화',
          messages: [],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }
        set(state => ({
          sessions: [newSession, ...state.sessions],
          currentSessionId: newSession.id,
        }))
        return newSession.id
      },

      /**
       * 세션 선택 (사이드바에서 클릭 시)
       * @param {string} sessionId - 선택할 세션 ID
       */
      selectSession: (sessionId) => {
        set({ currentSessionId: sessionId })
      },

      /**
       * 세션 삭제
       * - 삭제된 세션이 현재 세션이면 첫 번째 세션으로 자동 전환
       * @param {string} sessionId - 삭제할 세션 ID
       */
      deleteSession: (sessionId) => {
        set(state => {
          const newSessions = state.sessions.filter(s => s.id !== sessionId)
          const newCurrentId = state.currentSessionId === sessionId
            ? (newSessions[0]?.id || null)
            : state.currentSessionId
          return {
            sessions: newSessions,
            currentSessionId: newCurrentId,
          }
        })
      },

      /**
       * 세션 제목 업데이트
       * @param {string} sessionId - 대상 세션 ID
       * @param {string} content - 제목 생성에 사용할 내용
       */
      updateSessionTitle: (sessionId, content) => {
        const title = generateTitle(content)
        set(state => ({
          sessions: state.sessions.map(s =>
            s.id === sessionId
              ? { ...s, title, updatedAt: new Date().toISOString() }
              : s
          )
        }))
      },

      /**
       * 메시지 추가
       * - 첫 번째 사용자 메시지인 경우 세션 제목 자동 생성
       * @param {string} sessionId - 대상 세션 ID
       * @param {Message} message - 추가할 메시지 객체
       */
      addMessage: (sessionId, message) => {
        set(state => {
          const session = state.sessions.find(s => s.id === sessionId)
          if (!session) return state

          // 첫 사용자 메시지로 세션 제목 자동 설정
          const isFirstUserMessage =
            session.messages.length === 0 && message.type === 'user'

          const updatedSession = {
            ...session,
            messages: [...session.messages, message],
            updatedAt: new Date().toISOString(),
            title: isFirstUserMessage ? generateTitle(message.content) : session.title,
          }

          return {
            sessions: state.sessions.map(s =>
              s.id === sessionId ? updatedSession : s
            )
          }
        })
      },

      /**
       * 마지막 메시지 업데이트 (스트리밍 응답 시 사용)
       * @param {string} sessionId - 대상 세션 ID
       * @param {Partial<Message>} updates - 업데이트할 필드
       */
      updateLastMessage: (sessionId, updates) => {
        set(state => ({
          sessions: state.sessions.map(s => {
            if (s.id !== sessionId || s.messages.length === 0) return s
            const messages = [...s.messages]
            messages[messages.length - 1] = {
              ...messages[messages.length - 1],
              ...updates,
            }
            return { ...s, messages, updatedAt: new Date().toISOString() }
          })
        }))
      },

      // ============================================================
      // 선택자 (Selectors)
      // ============================================================

      /**
       * 현재 선택된 세션 조회
       * @returns {Session|null}
       */
      getCurrentSession: () => {
        const { sessions, currentSessionId } = get()
        return sessions.find(s => s.id === currentSessionId) || null
      },

      /**
       * 특정 세션의 메시지 목록 조회
       * @param {string} sessionId - 세션 ID
       * @returns {Message[]}
       */
      getSessionMessages: (sessionId) => {
        const { sessions } = get()
        const session = sessions.find(s => s.id === sessionId)
        return session?.messages || []
      },

      /**
       * 모든 세션 초기화 (디버깅/테스트용)
       */
      clearAllSessions: () => {
        set({ sessions: [], currentSessionId: null })
      },
    }),
    {
      // LocalStorage 영속화 설정
      name: 'rag-chatbot-sessions',  // 저장 키

      // 저장할 상태 필드 선택 (함수 제외)
      partialize: (state) => ({
        sessions: state.sessions,
        currentSessionId: state.currentSessionId,
      }),
    }
  )
)
