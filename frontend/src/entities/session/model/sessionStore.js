import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const generateId = () => crypto.randomUUID()

const generateTitle = (content) => {
  if (!content) return '새 대화'
  const cleaned = content.replace(/[#*`\n]/g, ' ').trim()
  return cleaned.length > 50 ? cleaned.slice(0, 47) + '...' : cleaned
}

export const useSessionStore = create(
  persist(
    (set, get) => ({
      sessions: [],
      currentSessionId: null,

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

      selectSession: (sessionId) => {
        set({ currentSessionId: sessionId })
      },

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

      addMessage: (sessionId, message) => {
        set(state => {
          const session = state.sessions.find(s => s.id === sessionId)
          if (!session) return state

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

      getCurrentSession: () => {
        const { sessions, currentSessionId } = get()
        return sessions.find(s => s.id === currentSessionId) || null
      },

      getSessionMessages: (sessionId) => {
        const { sessions } = get()
        const session = sessions.find(s => s.id === sessionId)
        return session?.messages || []
      },

      clearAllSessions: () => {
        set({ sessions: [], currentSessionId: null })
      },
    }),
    {
      name: 'rag-chatbot-sessions',
      partialize: (state) => ({
        sessions: state.sessions,
        currentSessionId: state.currentSessionId,
      }),
    }
  )
)
