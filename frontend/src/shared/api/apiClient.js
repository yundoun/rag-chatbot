/**
 * API 클라이언트 (Axios)
 *
 * 역할: 백엔드 FastAPI 서버와의 HTTP 통신을 담당
 *
 * API 엔드포인트:
 * ┌─────────────────────────────────────────────────────────────┐
 * │  POST /api/chat                                             │
 * │    - 새로운 질문 전송                                       │
 * │    - Body: { query: string, session_id?: string }           │
 * │    - Response: ChatResponse                                 │
 * │                                                             │
 * │  POST /api/chat/clarify                                     │
 * │    - 명확화 질문에 대한 응답 전송                           │
 * │    - Body: { session_id: string, user_response: string }    │
 * │    - Response: ChatResponse                                 │
 * │                                                             │
 * │  GET /health                                                │
 * │    - 서버 상태 확인                                         │
 * └─────────────────────────────────────────────────────────────┘
 *
 * ChatResponse 구조:
 * {
 *   response: string,              // 응답 텍스트
 *   sources: string[],             // 참조 문서 목록
 *   confidence: number,            // 신뢰도 (0-1)
 *   session_id: string,            // 세션 ID
 *   needs_disclaimer: boolean,     // 면책 조항 필요 여부
 *   retrieval_source: string,      // 'vector' | 'web' | 'hybrid'
 *   processing_time_ms: number,    // 처리 시간 (ms)
 *   clarification_question?: string,  // 명확화 질문 (있는 경우)
 *   options?: string[],            // 명확화 옵션 (있는 경우)
 * }
 */

import axios from 'axios'

// 환경 변수에서 API URL 읽기 (기본값: /api → Vite proxy 사용)
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

/**
 * Axios 인스턴스 생성
 * - baseURL: API 기본 경로
 * - timeout: 60초 (RAG 처리 시간 고려)
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,  // 60초 타임아웃
})

/**
 * 새로운 질문 전송
 *
 * @param {string} query - 사용자 질문
 * @param {string|null} sessionId - 기존 세션 ID (있는 경우)
 * @returns {Promise<ChatResponse>} 챗봇 응답
 * @throws {Error} 서버 오류 또는 네트워크 오류
 */
export async function sendMessage(query, sessionId = null) {
  try {
    const response = await apiClient.post('/chat', {
      query,
      session_id: sessionId,
    })
    return response.data
  } catch (error) {
    // 오류 유형별 처리
    if (error.response) {
      // 서버가 응답을 반환한 경우 (4xx, 5xx)
      throw new Error(
        error.response.data?.detail || '서버 오류가 발생했습니다.'
      )
    } else if (error.request) {
      // 요청은 보냈지만 응답이 없는 경우 (네트워크 오류)
      throw new Error('서버에 연결할 수 없습니다.')
    } else {
      // 요청 생성 중 오류
      throw new Error('요청 처리 중 오류가 발생했습니다.')
    }
  }
}

/**
 * 명확화 질문에 대한 응답 전송
 *
 * 백엔드가 추가 정보가 필요하다고 판단한 경우,
 * 사용자의 명확화 응답을 동일 세션으로 전송
 *
 * @param {string} sessionId - 세션 ID (필수)
 * @param {string} userResponse - 사용자의 명확화 응답
 * @returns {Promise<ChatResponse>} 챗봇 응답
 * @throws {Error} 세션 ID 누락 또는 서버 오류
 */
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

/**
 * 서버 헬스체크
 *
 * @returns {Promise<Object>} 서버 상태 정보
 * @throws {Error} 연결 오류
 */
export async function checkHealth() {
  try {
    const response = await axios.get('/health')
    return response.data
  } catch (error) {
    throw new Error('API 서버에 연결할 수 없습니다.')
  }
}
