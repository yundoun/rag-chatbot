import { useState } from 'react'
import { IconDocument, IconGlobe } from '@shared/ui'

function isWebSource(source) {
  return source && (
    source.startsWith('http://') ||
    source.startsWith('https://') ||
    source.startsWith('www.')
  )
}

function getSourceDisplayName(source) {
  if (!source) return '알 수 없는 출처'

  if (isWebSource(source)) {
    try {
      const url = new URL(source.startsWith('www.') ? `https://${source}` : source)
      return url.hostname.replace('www.', '')
    } catch {
      return source.slice(0, 40) + (source.length > 40 ? '...' : '')
    }
  }

  const parts = source.split('/')
  return parts[parts.length - 1] || source
}

function SourceItem({ source }) {
  const isWeb = isWebSource(source)
  const displayName = getSourceDisplayName(source)

  const content = (
    <div className="flex items-center gap-2">
      {isWeb ? (
        <IconGlobe className="w-4 h-4 text-accent-500" />
      ) : (
        <IconDocument className="w-4 h-4 text-mint-500" />
      )}
      <span className="text-sm truncate">{displayName}</span>
      {isWeb && (
        <svg className="w-3 h-3 text-light-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      )}
    </div>
  )

  const baseClasses = `
    px-3 py-2 rounded-lg text-left transition-all duration-200
    ${isWeb
      ? 'bg-accent-50 hover:bg-accent-100 text-accent-700 border border-accent-200'
      : 'bg-mint-50 hover:bg-mint-100 text-mint-700 border border-mint-200'
    }
  `

  if (isWeb) {
    return (
      <a
        href={source.startsWith('www.') ? `https://${source}` : source}
        target="_blank"
        rel="noopener noreferrer"
        className={baseClasses}
        title={source}
      >
        {content}
      </a>
    )
  }

  return (
    <div className={baseClasses} title={source}>
      {content}
    </div>
  )
}

export function SourceList({ sources = [], retrievalSource = 'vector', maxVisible = 3 }) {
  const [expanded, setExpanded] = useState(false)

  if (!sources || sources.length === 0) {
    return null
  }

  const webSources = sources.filter(isWebSource)
  const internalSources = sources.filter(s => !isWebSource(s))
  const visibleSources = expanded ? sources : sources.slice(0, maxVisible)
  const hiddenCount = sources.length - maxVisible

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-xs font-medium text-light-text-muted uppercase tracking-wider">
          출처
          {retrievalSource === 'web' && (
            <span className="ml-2 text-accent-500">(웹 검색)</span>
          )}
          {retrievalSource === 'hybrid' && (
            <span className="ml-2 text-purple-500">(내부 + 웹)</span>
          )}
        </h4>

        <div className="flex gap-2">
          {internalSources.length > 0 && (
            <span className="text-xs bg-mint-50 text-mint-600 px-2 py-0.5 rounded border border-mint-200">
              내부 {internalSources.length}
            </span>
          )}
          {webSources.length > 0 && (
            <span className="text-xs bg-accent-50 text-accent-600 px-2 py-0.5 rounded border border-accent-200">
              웹 {webSources.length}
            </span>
          )}
        </div>
      </div>

      <div className="space-y-1">
        {visibleSources.map((source, index) => (
          <SourceItem key={index} source={source} />
        ))}
      </div>

      {hiddenCount > 0 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 text-xs text-light-text-muted hover:text-accent-500 flex items-center gap-1 transition-colors"
        >
          {expanded ? (
            <>
              <span>접기</span>
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              </svg>
            </>
          ) : (
            <>
              <span>+{hiddenCount}개 더 보기</span>
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </>
          )}
        </button>
      )}
    </div>
  )
}

export default SourceList
