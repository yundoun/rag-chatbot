/**
 * Clarification dialog component for HITL interactions
 */

import React, { useState } from 'react';
import OptionButton from './OptionButton';

/**
 * ClarificationDialog component for selecting options or providing custom input
 * @param {Object} props
 * @param {string} props.question - The clarification question
 * @param {Array<string>} props.options - Available options to choose from
 * @param {boolean} props.allowCustomInput - Whether to allow custom text input
 * @param {Function} props.onSubmit - Callback when user submits response (selectedOption, customInput)
 * @param {boolean} props.disabled - Whether the dialog is disabled
 */
function ClarificationDialog({
  question,
  options = [],
  allowCustomInput = true,
  onSubmit,
  disabled = false,
}) {
  const [selectedOption, setSelectedOption] = useState(null);
  const [customInput, setCustomInput] = useState('');
  const [isCustomMode, setIsCustomMode] = useState(false);

  const handleOptionClick = (option) => {
    if (disabled) return;
    setSelectedOption(option);
    setIsCustomMode(false);
    setCustomInput('');
  };

  const handleCustomClick = () => {
    if (disabled) return;
    setIsCustomMode(true);
    setSelectedOption(null);
  };

  const handleSubmit = () => {
    if (disabled) return;

    if (isCustomMode && customInput.trim()) {
      onSubmit?.(null, customInput.trim());
    } else if (selectedOption) {
      onSubmit?.(selectedOption, null);
    }
  };

  const canSubmit = (isCustomMode && customInput.trim()) || selectedOption;

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6 max-w-md mx-auto">
      {/* Question Header */}
      <div className="flex items-start mb-4">
        <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-3">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-1">명확화 질문</h3>
          <p className="text-gray-900 font-medium">{question}</p>
        </div>
      </div>

      {/* Options */}
      <div className="space-y-2 mb-4">
        {options.map((option, index) => (
          <OptionButton
            key={index}
            label={option}
            selected={selectedOption === option}
            onClick={() => handleOptionClick(option)}
            disabled={disabled}
          />
        ))}

        {/* Custom Input Option */}
        {allowCustomInput && (
          <OptionButton
            label="직접 입력"
            selected={isCustomMode}
            onClick={handleCustomClick}
            disabled={disabled}
          />
        )}
      </div>

      {/* Custom Input Field */}
      {isCustomMode && (
        <div className="mb-4">
          <textarea
            className={`
              w-full px-4 py-3 rounded-lg border-2 transition-colors
              focus:outline-none focus:border-blue-500
              ${disabled ? 'bg-gray-100 border-gray-200' : 'border-gray-200'}
            `}
            placeholder="직접 입력해 주세요..."
            rows={3}
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            disabled={disabled}
            autoFocus
          />
        </div>
      )}

      {/* Submit Button */}
      <button
        type="button"
        className={`
          w-full py-3 rounded-lg font-medium transition-colors
          ${canSubmit && !disabled
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }
        `}
        onClick={handleSubmit}
        disabled={!canSubmit || disabled}
      >
        {disabled ? '처리 중...' : '확인'}
      </button>

      {/* Hint */}
      <p className="text-xs text-gray-400 text-center mt-3">
        위 선택지 중 하나를 선택하거나 직접 입력해 주세요
      </p>
    </div>
  );
}

export default ClarificationDialog;
