/**
 * SourceList component for displaying document sources
 */

import React, { useState } from 'react';

/**
 * Check if a source is a web URL
 * @param {string} source - Source string
 * @returns {boolean}
 */
function isWebSource(source) {
  return source && (
    source.startsWith('http://') ||
    source.startsWith('https://') ||
    source.startsWith('www.')
  );
}

/**
 * Get display name for a source
 * @param {string} source - Source string
 * @returns {string}
 */
function getSourceDisplayName(source) {
  if (!source) return '알 수 없는 출처';

  if (isWebSource(source)) {
    try {
      const url = new URL(source.startsWith('www.') ? `https://${source}` : source);
      return url.hostname.replace('www.', '');
    } catch {
      return source.slice(0, 40) + (source.length > 40 ? '...' : '');
    }
  }

  // Internal document - show filename
  const parts = source.split('/');
  return parts[parts.length - 1] || source;
}

/**
 * SourceItem component for individual source
 */
function SourceItem({ source, index }) {
  const isWeb = isWebSource(source);
  const displayName = getSourceDisplayName(source);

  const content = (
    <div className="flex items-center space-x-2">
      {/* Icon */}
      {isWeb ? (
        <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
          />
        </svg>
      ) : (
        <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      )}

      {/* Source name */}
      <span className="text-sm truncate">{displayName}</span>

      {/* External link indicator */}
      {isWeb && (
        <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
          />
        </svg>
      )}
    </div>
  );

  const baseClasses = `
    px-3 py-2 rounded-lg text-left
    ${isWeb
      ? 'bg-blue-50 hover:bg-blue-100 text-blue-700'
      : 'bg-gray-50 hover:bg-gray-100 text-gray-700'
    }
    transition-colors
  `;

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
    );
  }

  return (
    <div className={baseClasses} title={source}>
      {content}
    </div>
  );
}

/**
 * SourceList component for displaying list of sources
 * @param {Object} props
 * @param {Array<string>} props.sources - List of source strings
 * @param {string} props.retrievalSource - Source type: 'vector' | 'web' | 'hybrid'
 * @param {number} props.maxVisible - Maximum sources to show before collapsing
 */
function SourceList({ sources = [], retrievalSource = 'vector', maxVisible = 3 }) {
  const [expanded, setExpanded] = useState(false);

  if (!sources || sources.length === 0) {
    return null;
  }

  // Separate internal and web sources
  const webSources = sources.filter(isWebSource);
  const internalSources = sources.filter(s => !isWebSource(s));

  // Determine which sources to show
  const visibleSources = expanded ? sources : sources.slice(0, maxVisible);
  const hiddenCount = sources.length - maxVisible;

  return (
    <div className="mt-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          출처
          {retrievalSource === 'web' && (
            <span className="ml-2 text-blue-500">(웹 검색)</span>
          )}
          {retrievalSource === 'hybrid' && (
            <span className="ml-2 text-purple-500">(내부 + 웹)</span>
          )}
        </h4>

        {/* Source count badges */}
        <div className="flex space-x-2">
          {internalSources.length > 0 && (
            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
              내부 {internalSources.length}
            </span>
          )}
          {webSources.length > 0 && (
            <span className="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded">
              웹 {webSources.length}
            </span>
          )}
        </div>
      </div>

      {/* Source list */}
      <div className="space-y-1">
        {visibleSources.map((source, index) => (
          <SourceItem key={index} source={source} index={index} />
        ))}
      </div>

      {/* Expand/Collapse button */}
      {hiddenCount > 0 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 text-xs text-gray-500 hover:text-gray-700 flex items-center space-x-1"
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
  );
}

export default SourceList;
