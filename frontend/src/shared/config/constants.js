export const APP_NAME = 'RAG 챗봇'
export const APP_VERSION = '1.0.0'

export const PROCESSING_STEPS = [
  { key: 'analyzing', label: '질문 분석' },
  { key: 'searching', label: '문서 검색' },
  { key: 'evaluating', label: '관련성 평가' },
  { key: 'generating', label: '답변 생성' },
]

export const MESSAGE_TYPES = {
  USER: 'user',
  ASSISTANT: 'assistant',
  ERROR: 'error',
}

export const RETRIEVAL_SOURCES = {
  VECTOR: 'vector',
  WEB: 'web',
  HYBRID: 'hybrid',
}

export const CONFIDENCE_THRESHOLDS = {
  HIGH: 0.8,
  MEDIUM: 0.5,
}
