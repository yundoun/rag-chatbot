"""Application constants"""

# === Domain Categories ===
VALID_DOMAINS = [
    "development",
    "operations",
    "security",
    "infrastructure",
    "api",
    "database",
    "frontend",
    "backend",
    "devops",
    "general",
]

# === Relevance Score Mapping ===
RELEVANCE_LEVELS = {
    "high": (0.8, 1.0),
    "medium": (0.5, 0.8),
    "low": (0.0, 0.5),
}

# === Token Limits ===
MAX_CONTEXT_TOKENS = 8000
MAX_RESPONSE_TOKENS = 2000
MAX_DOCUMENT_CHUNK_SIZE = 1000

# === UI Messages (Korean) ===
DISCLAIMER_MESSAGE = (
    "⚠️ 이 답변은 검색된 정보가 충분하지 않아 "
    "정확성이 보장되지 않습니다. 중요한 결정에는 "
    "추가 확인을 권장합니다."
)

WEB_SEARCH_DISCLAIMER = (
    "ℹ️ 내부 문서에서 관련 정보를 찾지 못하여 " "웹 검색 결과를 포함합니다."
)

# === Error Messages (Korean) ===
ERROR_MESSAGES = {
    "no_results": "관련 문서를 찾을 수 없습니다.",
    "api_error": "API 호출 중 오류가 발생했습니다.",
    "timeout": "요청 시간이 초과되었습니다.",
    "rate_limit": "API 호출 한도에 도달했습니다. 잠시 후 다시 시도해주세요.",
    "invalid_query": "질문을 이해할 수 없습니다. 다시 입력해주세요.",
    "connection_error": "서버 연결에 실패했습니다.",
    "unknown_error": "알 수 없는 오류가 발생했습니다.",
}

# === Response Status Messages (Korean) ===
STATUS_MESSAGES = {
    "analyzing": "질문을 분석하고 있습니다...",
    "searching": "관련 문서를 검색하고 있습니다...",
    "evaluating": "검색 결과를 평가하고 있습니다...",
    "generating": "답변을 생성하고 있습니다...",
    "complete": "완료되었습니다.",
}
