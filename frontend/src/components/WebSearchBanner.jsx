/**
 * Web Search Banner component for displaying disclaimer
 */

import React from 'react';

/**
 * WebSearchBanner displays a disclaimer when web search results are used
 * @param {Object} props
 * @param {boolean} props.show - Whether to show the banner
 * @param {string} props.type - Type of banner: 'info' | 'warning'
 */
function WebSearchBanner({ show = false, type = 'warning' }) {
  if (!show) return null;

  const styles = {
    warning: {
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      icon: 'text-amber-500',
      text: 'text-amber-800',
    },
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      icon: 'text-blue-500',
      text: 'text-blue-800',
    },
  };

  const style = styles[type] || styles.warning;

  return (
    <div
      className={`
        ${style.bg} ${style.border} border rounded-lg px-4 py-3 mb-3
        flex items-start space-x-3
      `}
    >
      {/* Warning Icon */}
      <div className={`flex-shrink-0 ${style.icon}`}>
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
      </div>

      {/* Message */}
      <div className={`flex-1 ${style.text}`}>
        <p className="font-medium text-sm">외부 웹 검색 결과 포함</p>
        <p className="text-xs mt-1">
          이 답변은 내부 문서에서 충분한 정보를 찾지 못해 웹 검색 결과를 포함하고 있습니다.
          정확성을 위해 공식 문서를 확인해 주세요.
        </p>
      </div>
    </div>
  );
}

export default WebSearchBanner;
