import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds for RAG processing
})

/**
 * Send a chat message and get RAG response
 * @param {string} query - The user's question
 * @param {string|null} sessionId - Optional session ID for conversation continuity
 * @returns {Promise<Object>} The RAG response
 */
export async function sendMessage(query, sessionId = null) {
  try {
    const response = await api.post('/chat', {
      query,
      session_id: sessionId,
    })
    return response.data
  } catch (error) {
    if (error.response) {
      // Server responded with error
      throw new Error(
        error.response.data?.detail || '서버 오류가 발생했습니다.'
      )
    } else if (error.request) {
      // No response received
      throw new Error('서버에 연결할 수 없습니다.')
    } else {
      // Request setup error
      throw new Error('요청 처리 중 오류가 발생했습니다.')
    }
  }
}

/**
 * Send a clarification response and continue the conversation
 * @param {string} sessionId - The session ID
 * @param {string} userResponse - The user's clarification response
 * @returns {Promise<Object>} The RAG response
 */
export async function sendClarificationResponse(sessionId, userResponse) {
  if (!sessionId) {
    throw new Error('세션 ID가 필요합니다.')
  }

  try {
    const response = await api.post('/chat/clarify', {
      session_id: sessionId,
      user_response: userResponse,
    })
    return response.data
  } catch (error) {
    if (error.response) {
      throw new Error(
        error.response.data?.detail || '서버 오류가 발생했습니다.'
      )
    } else if (error.request) {
      throw new Error('서버에 연결할 수 없습니다.')
    } else {
      throw new Error('요청 처리 중 오류가 발생했습니다.')
    }
  }
}

/**
 * Check API health status
 * @returns {Promise<Object>} Health status
 */
export async function checkHealth() {
  try {
    const response = await axios.get('/health')
    return response.data
  } catch (error) {
    throw new Error('API 서버에 연결할 수 없습니다.')
  }
}

export default api
