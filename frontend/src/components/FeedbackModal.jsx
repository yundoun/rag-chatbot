import React, { useState, useRef, useEffect } from 'react';
import { useFocusTrap } from '../hooks/useKeyboardNavigation';
import '../styles/animations.css';

/**
 * Feedback categories for detailed feedback
 */
const FEEDBACK_CATEGORIES = [
  { id: 'incorrect', label: '정보가 부정확해요' },
  { id: 'incomplete', label: '정보가 부족해요' },
  { id: 'irrelevant', label: '질문과 관련 없는 답변이에요' },
  { id: 'confusing', label: '이해하기 어려워요' },
  { id: 'other', label: '기타' },
];

/**
 * Detailed feedback modal component
 */
function FeedbackModal({ isOpen, onClose, onSubmit, messageId }) {
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const modalRef = useRef(null);

  // Focus trap for modal
  useFocusTrap(modalRef, { enabled: isOpen });

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setSelectedCategories([]);
      setComment('');
      setSubmitted(false);
    }
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  const toggleCategory = (categoryId) => {
    setSelectedCategories((prev) =>
      prev.includes(categoryId)
        ? prev.filter((id) => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  const handleSubmit = async () => {
    if (selectedCategories.length === 0 && !comment.trim()) {
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit({
        messageId,
        categories: selectedCategories,
        comment: comment.trim(),
        timestamp: new Date().toISOString(),
      });

      setSubmitted(true);

      // Close modal after showing success
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="feedback-modal-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 modal-overlay-enter"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal content */}
      <div
        ref={modalRef}
        className="
          relative z-10 w-full max-w-md mx-4
          bg-white rounded-xl shadow-2xl
          modal-content-enter
        "
      >
        {submitted ? (
          // Success state
          <div className="p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-100 flex items-center justify-center">
              <svg
                className="w-8 h-8 text-green-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">
              피드백이 제출되었습니다
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              소중한 의견 감사합니다. 서비스 개선에 반영하겠습니다.
            </p>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h2
                id="feedback-modal-title"
                className="text-lg font-semibold text-gray-900"
              >
                피드백 보내기
              </h2>
              <button
                onClick={onClose}
                className="
                  p-2 rounded-lg text-gray-400 hover:text-gray-600
                  hover:bg-gray-100 transition-colors
                  focus:outline-none focus:ring-2 focus:ring-blue-500
                "
                aria-label="닫기"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            {/* Body */}
            <div className="px-6 py-4">
              <p className="text-sm text-gray-600 mb-4">
                어떤 점이 아쉬웠나요? (복수 선택 가능)
              </p>

              {/* Category buttons */}
              <div className="flex flex-wrap gap-2 mb-4">
                {FEEDBACK_CATEGORIES.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => toggleCategory(category.id)}
                    className={`
                      px-3 py-2 rounded-lg text-sm font-medium
                      transition-all duration-200
                      ${
                        selectedCategories.includes(category.id)
                          ? 'bg-blue-100 text-blue-700 border-2 border-blue-300'
                          : 'bg-gray-100 text-gray-700 border-2 border-transparent hover:bg-gray-200'
                      }
                      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                    `}
                    aria-pressed={selectedCategories.includes(category.id)}
                  >
                    {category.label}
                  </button>
                ))}
              </div>

              {/* Comment textarea */}
              <div>
                <label
                  htmlFor="feedback-comment"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  추가 의견 (선택사항)
                </label>
                <textarea
                  id="feedback-comment"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="더 나은 서비스를 위해 의견을 남겨주세요..."
                  rows={3}
                  className="
                    w-full px-3 py-2 rounded-lg border border-gray-300
                    text-sm text-gray-900 placeholder-gray-400
                    resize-none
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                  "
                  maxLength={500}
                />
                <p className="mt-1 text-xs text-gray-500 text-right">
                  {comment.length}/500
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-xl">
              <button
                onClick={onClose}
                className="
                  px-4 py-2 rounded-lg text-sm font-medium
                  text-gray-700 hover:bg-gray-200
                  transition-colors
                  focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2
                "
              >
                취소
              </button>
              <button
                onClick={handleSubmit}
                disabled={
                  isSubmitting ||
                  (selectedCategories.length === 0 && !comment.trim())
                }
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium
                  text-white
                  transition-colors
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                  ${
                    isSubmitting ||
                    (selectedCategories.length === 0 && !comment.trim())
                      ? 'bg-blue-300 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700'
                  }
                `}
              >
                {isSubmitting ? (
                  <span className="flex items-center gap-2">
                    <svg
                      className="w-4 h-4 animate-spin"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                    제출 중...
                  </span>
                ) : (
                  '피드백 보내기'
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default FeedbackModal;
