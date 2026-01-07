export function EmptyState() {
  const suggestions = [
    '친구추천이라는 기능은 뭘 의미하는거지?',
    '부킹닷컴 연락처 노출 개선 개발건에 대해 알려줘',
    '최근 개발된 기능에 대해 설명해줘',
  ]

  return (
    <div className="flex flex-col items-center justify-center h-full px-4">
      <div className="
        w-20 h-20 mb-6 rounded-2xl
        bg-gradient-to-br from-accent-500/10 to-mint-500/10
        border border-accent-500/20
        flex items-center justify-center
      ">
        <span className="text-4xl">📚</span>
      </div>

      <h2 className="text-xl font-semibold text-light-text-primary mb-2">
        무엇이든 물어보세요
      </h2>

      <p className="text-light-text-secondary text-center max-w-md mb-8">
        내부 문서를 기반으로 질문에 답변해 드립니다.
        기획서, 개발 문서 등에서 필요한 정보를 찾아보세요.
      </p>

      <div className="w-full max-w-md space-y-2">
        <p className="text-xs text-light-text-muted uppercase tracking-wider mb-3">
          추천 질문
        </p>
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            className="
              w-full px-4 py-3 text-left rounded-xl
              bg-white border border-light-border
              text-light-text-secondary text-sm
              hover:bg-light-elevated hover:border-accent-500/50
              hover:text-light-text-primary
              transition-all duration-200
              shadow-sm
            "
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  )
}

export default EmptyState
