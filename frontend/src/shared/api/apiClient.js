import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
})

export async function sendMessage(query, sessionId = null) {
  try {
    const response = await apiClient.post('/chat', {
      query,
      session_id: sessionId,
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

export async function sendClarificationResponse(sessionId, userResponse) {
  if (!sessionId) {
    throw new Error('세션 ID가 필요합니다.')
  }

  try {
    const response = await apiClient.post('/chat/clarify', {
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

export async function checkHealth() {
  try {
    const response = await axios.get('/health')
    return response.data
  } catch (error) {
    throw new Error('API 서버에 연결할 수 없습니다.')
  }
}
