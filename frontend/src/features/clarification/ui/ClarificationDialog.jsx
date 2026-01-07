import { useState } from 'react'
import { OptionButton } from './OptionButton'
import { Button } from '@shared/ui'

export function ClarificationDialog({
  question,
  options = [],
  allowCustomInput = true,
  onSubmit,
  disabled = false,
}) {
  const [selectedOption, setSelectedOption] = useState(null)
  const [customInput, setCustomInput] = useState('')
  const [isCustomMode, setIsCustomMode] = useState(false)

  const handleOptionClick = (option) => {
    if (disabled) return
    setSelectedOption(option)
    setIsCustomMode(false)
    setCustomInput('')
  }

  const handleCustomClick = () => {
    if (disabled) return
    setIsCustomMode(true)
    setSelectedOption(null)
  }

  const handleSubmit = () => {
    if (disabled) return

    if (isCustomMode && customInput.trim()) {
      onSubmit?.(null, customInput.trim())
    } else if (selectedOption) {
      onSubmit?.(selectedOption, null)
    }
  }

  const canSubmit = (isCustomMode && customInput.trim()) || selectedOption

  return (
    <div className="
      bg-white
      rounded-2xl border border-light-border
      shadow-lg p-6 max-w-md mx-auto
      animate-fade-in
    ">
      <div className="flex items-start mb-5">
        <div className="
          flex-shrink-0 w-10 h-10
          bg-accent-50 rounded-xl
          flex items-center justify-center mr-3
          border border-accent-200
        ">
          <svg className="w-5 h-5 text-accent-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <div>
          <h3 className="text-xs font-medium text-light-text-muted mb-1 uppercase tracking-wider">
            명확화 질문
          </h3>
          <p className="text-light-text-primary font-medium">{question}</p>
        </div>
      </div>

      <div className="space-y-2 mb-5">
        {options.map((option, index) => (
          <OptionButton
            key={index}
            label={option}
            selected={selectedOption === option}
            onClick={() => handleOptionClick(option)}
            disabled={disabled}
          />
        ))}

        {allowCustomInput && (
          <OptionButton
            label="직접 입력"
            selected={isCustomMode}
            onClick={handleCustomClick}
            disabled={disabled}
          />
        )}
      </div>

      {isCustomMode && (
        <div className="mb-5">
          <textarea
            className="
              w-full px-4 py-3 rounded-xl
              bg-light-elevated border-2 border-light-border
              text-light-text-primary placeholder-light-text-muted
              focus:outline-none focus:border-accent-500
              transition-colors disabled:opacity-50
            "
            placeholder="직접 입력해 주세요..."
            rows={3}
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            disabled={disabled}
            autoFocus
          />
        </div>
      )}

      <Button
        variant="primary"
        className="w-full"
        onClick={handleSubmit}
        disabled={!canSubmit || disabled}
        loading={disabled}
      >
        {disabled ? '처리 중...' : '확인'}
      </Button>

      <p className="text-xs text-light-text-muted text-center mt-4">
        위 선택지 중 하나를 선택하거나 직접 입력해 주세요
      </p>
    </div>
  )
}

export default ClarificationDialog
