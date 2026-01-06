import React, { useState } from 'react';
import '../styles/animations.css';

/**
 * Feedback buttons component (thumbs up/down)
 */
function FeedbackButtons({
  messageId,
  onFeedback,
  onDetailedFeedback,
  disabled = false,
  size = 'medium',
}) {
  const [feedback, setFeedback] = useState(null); // 'positive', 'negative', or null
  const [showThankYou, setShowThankYou] = useState(false);

  const sizeClasses = {
    small: 'w-6 h-6',
    medium: 'w-8 h-8',
    large: 'w-10 h-10',
  };

  const iconSizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-5 h-5',
    large: 'w-6 h-6',
  };

  const handleFeedback = async (type) => {
    if (disabled || feedback === type) return;

    setFeedback(type);
    setShowThankYou(true);

    if (onFeedback) {
      await onFeedback(messageId, type);
    }

    // Show thank you message briefly
    setTimeout(() => setShowThankYou(false), 2000);

    // If negative, prompt for detailed feedback
    if (type === 'negative' && onDetailedFeedback) {
      setTimeout(() => onDetailedFeedback(messageId), 500);
    }
  };

  return (
    <div className="flex items-center gap-2">
      {/* Thumbs up button */}
      <button
        onClick={() => handleFeedback('positive')}
        disabled={disabled}
        className={`
          ${sizeClasses[size]}
          flex items-center justify-center rounded-full
          transition-all duration-200
          ${
            feedback === 'positive'
              ? 'bg-green-100 text-green-600'
              : 'text-gray-400 hover:text-green-600 hover:bg-green-50'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2
        `}
        aria-label="도움이 되었어요"
        aria-pressed={feedback === 'positive'}
      >
        <svg
          className={iconSizeClasses[size]}
          fill={feedback === 'positive' ? 'currentColor' : 'none'}
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={feedback === 'positive' ? 0 : 2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"
          />
        </svg>
      </button>

      {/* Thumbs down button */}
      <button
        onClick={() => handleFeedback('negative')}
        disabled={disabled}
        className={`
          ${sizeClasses[size]}
          flex items-center justify-center rounded-full
          transition-all duration-200
          ${
            feedback === 'negative'
              ? 'bg-red-100 text-red-600'
              : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
        `}
        aria-label="도움이 안 되었어요"
        aria-pressed={feedback === 'negative'}
      >
        <svg
          className={iconSizeClasses[size]}
          fill={feedback === 'negative' ? 'currentColor' : 'none'}
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={feedback === 'negative' ? 0 : 2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5"
          />
        </svg>
      </button>

      {/* Thank you message */}
      {showThankYou && (
        <span className="text-sm text-gray-500 animate-fade-in">
          피드백 감사합니다!
        </span>
      )}
    </div>
  );
}

export default FeedbackButtons;
