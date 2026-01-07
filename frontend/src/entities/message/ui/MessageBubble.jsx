import { SourceList } from './SourceList'

function WebSearchBanner({ type = 'info' }) {
  const isWarning = type === 'warning'

  return (
    <div className={`
      mb-3 p-2 rounded-lg text-xs flex items-center gap-2
      ${isWarning
        ? 'bg-amber-50 text-amber-700 border border-amber-200'
        : 'bg-accent-50 text-accent-700 border border-accent-200'
      }
    `}>
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
      </svg>
      <span>
        {isWarning
          ? '외부 웹 검색 결과 포함'
          : '내부 문서에서 충분한 정보를 찾지 못해 웹 검색 결과를 포함하고 있습니다. 정확성을 위해 공식 문서를 확인해 주세요.'
        }
      </span>
    </div>
  )
}

export function MessageBubble({ message }) {
  const isUser = message.type === 'user'
  const isError = message.type === 'error'
  const isClarification = message.isClarification

  const isWebSearch = message.retrievalSource === 'web'
  const isHybrid = message.retrievalSource === 'hybrid'
  const hasWebResults = isWebSearch || isHybrid

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
      <div
        className={`
          max-w-[80%] rounded-2xl px-4 py-3
          ${isUser
            ? isClarification
              ? 'bg-purple-500 text-white'
              : 'bg-gradient-to-r from-accent-500 to-accent-600 text-white shadow-lg'
            : isError
            ? 'bg-red-50 text-red-700 border border-red-200'
            : 'bg-white border border-light-border text-light-text-primary shadow-sm'
          }
        `}
      >
        {isClarification && (
          <div className="text-xs text-purple-200 mb-1 opacity-80">명확화 응답</div>
        )}

        {hasWebResults && !isUser && !isError && (
          <WebSearchBanner type={isWebSearch ? 'warning' : 'info'} />
        )}

        <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>

        {message.needsDisclaimer && !hasWebResults && (
          <div className="mt-3 p-2 bg-amber-50 rounded-lg text-amber-700 text-sm border border-amber-200">
            ⚠️ 이 답변은 검색된 정보가 충분하지 않아 정확성이 보장되지 않습니다.
          </div>
        )}

        {message.sources && message.sources.length > 0 && (
          <SourceList
            sources={message.sources}
            retrievalSource={message.retrievalSource}
            maxVisible={3}
          />
        )}

        {!isUser && !isError && (
          <div className="mt-3 pt-3 border-t border-light-border/50 flex items-center justify-between text-xs text-light-text-muted">
            <div className="flex items-center gap-3">
              <span>
                {message.timestamp && new Date(message.timestamp).toLocaleTimeString('ko-KR', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
              {message.confidence !== undefined && (
                <span className={`
                  px-2 py-0.5 rounded-full font-medium
                  ${message.confidence >= 0.8
                    ? 'bg-mint-50 text-mint-600 border border-mint-200'
                    : message.confidence >= 0.5
                    ? 'bg-amber-50 text-amber-600 border border-amber-200'
                    : 'bg-red-50 text-red-600 border border-red-200'
                  }
                `}>
                  신뢰도 {Math.round(message.confidence * 100)}%
                </span>
              )}
            </div>
            {message.processingTime && (
              <span className="text-light-text-muted">{message.processingTime}ms</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default MessageBubble
