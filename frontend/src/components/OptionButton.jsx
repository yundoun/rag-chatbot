/**
 * Option button component for clarification dialog
 */

import React from 'react';

/**
 * OptionButton component for selectable options
 * @param {Object} props
 * @param {string} props.label - Button label text
 * @param {boolean} props.selected - Whether this option is selected
 * @param {Function} props.onClick - Click handler
 * @param {boolean} props.disabled - Whether button is disabled
 */
function OptionButton({ label, selected = false, onClick, disabled = false }) {
  const baseClasses = `
    w-full px-4 py-3 rounded-lg text-left transition-all duration-200
    border-2 font-medium
  `;

  const stateClasses = selected
    ? 'bg-blue-50 border-blue-500 text-blue-700'
    : disabled
      ? 'bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed'
      : 'bg-white border-gray-200 text-gray-700 hover:border-blue-300 hover:bg-blue-50';

  return (
    <button
      type="button"
      className={`${baseClasses} ${stateClasses}`}
      onClick={onClick}
      disabled={disabled}
    >
      <div className="flex items-center">
        <div className={`
          w-5 h-5 rounded-full border-2 mr-3 flex items-center justify-center
          ${selected ? 'border-blue-500 bg-blue-500' : 'border-gray-300'}
        `}>
          {selected && (
            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
          )}
        </div>
        <span>{label}</span>
      </div>
    </button>
  );
}

export default OptionButton;
