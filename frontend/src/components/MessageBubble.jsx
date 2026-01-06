import WebSearchBanner from './WebSearchBanner'
import SourceList from './SourceList'

function MessageBubble({ message }) {
  const isUser = message.type === 'user'
  const isError = message.type === 'error'
  const isClarification = message.isClarification

  // Check if web search was used
  const isWebSearch = message.retrievalSource === 'web'
  const isHybrid = message.retrievalSource === 'hybrid'
  const hasWebResults = isWebSearch || isHybrid

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-3 ${
          isUser
            ? isClarification
              ? 'bg-blue-500 text-white'
              : 'bg-primary-500 text-white'
            : isError
            ? 'bg-red-100 text-red-700 border border-red-200'
            : 'bg-gray-100 text-gray-800'
        }`}
      >
        {/* Clarification indicator */}
        {isClarification && (
          <div className="text-xs text-blue-200 mb-1">명확화 응답</div>
        )}

        {/* Web Search Banner */}
        {hasWebResults && !isUser && !isError && (
          <WebSearchBanner show={true} type={isWebSearch ? 'warning' : 'info'} />
        )}

        {/* Message Content */}
        <div className="whitespace-pre-wrap">{message.content}</div>

        {/* Disclaimer Banner */}
        {message.needsDisclaimer && !hasWebResults && (
          <div className="mt-2 p-2 bg-yellow-100 rounded text-yellow-700 text-sm">
            ⚠️ 이 답변은 검색된 정보가 충분하지 않아 정확성이 보장되지 않습니다.
          </div>
        )}

        {/* Sources with enhanced display */}
        {message.sources && message.sources.length > 0 && (
          <SourceList
            sources={message.sources}
            retrievalSource={message.retrievalSource}
            maxVisible={3}
          />
        )}

        {/* Metadata */}
        {!isUser && !isError && (
          <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
            <div className="flex items-center space-x-2">
              <span>
                {message.timestamp?.toLocaleTimeString('ko-KR', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
              {message.confidence !== undefined && (
                <span className={`
                  px-1.5 py-0.5 rounded
                  ${message.confidence >= 0.8
                    ? 'bg-green-100 text-green-600'
                    : message.confidence >= 0.5
                    ? 'bg-yellow-100 text-yellow-600'
                    : 'bg-red-100 text-red-600'
                  }
                `}>
                  신뢰도 {Math.round(message.confidence * 100)}%
                </span>
              )}
            </div>
            {message.processingTime && (
              <span>{message.processingTime}ms</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default MessageBubble
