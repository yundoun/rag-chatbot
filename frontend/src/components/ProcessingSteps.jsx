const STEPS = [
  { key: 'analyzing', label: '질문 분석', icon: '🔍' },
  { key: 'searching', label: '문서 검색', icon: '📚' },
  { key: 'evaluating', label: '관련성 평가', icon: '⚖️' },
  { key: 'generating', label: '답변 생성', icon: '✍️' },
]

function ProcessingSteps({ currentStep, completedSteps = [] }) {
  const getStepStatus = (stepKey) => {
    if (completedSteps.includes(stepKey)) return 'completed'
    if (currentStep === stepKey) return 'current'
    return 'pending'
  }

  return (
    <div className="p-4 bg-white rounded-lg border border-gray-200">
      <h4 className="text-sm font-medium text-gray-500 mb-3">처리 진행 상황</h4>

      <div className="space-y-2">
        {STEPS.map((step, index) => {
          const status = getStepStatus(step.key)

          return (
            <div key={step.key} className="flex items-center space-x-3">
              {/* Step indicator */}
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs
                  ${
                    status === 'completed'
                      ? 'bg-green-500 text-white'
                      : status === 'current'
                      ? 'bg-primary-500 text-white animate-pulse'
                      : 'bg-gray-200 text-gray-400'
                  }`}
              >
                {status === 'completed' ? (
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                ) : (
                  index + 1
                )}
              </div>

              {/* Step icon and label */}
              <span className="text-lg">{step.icon}</span>
              <span
                className={`text-sm ${
                  status === 'completed'
                    ? 'text-green-600 font-medium'
                    : status === 'current'
                    ? 'text-primary-600 font-medium'
                    : 'text-gray-400'
                }`}
              >
                {step.label}
              </span>

              {/* Current step spinner */}
              {status === 'current' && (
                <div className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
              )}
            </div>
          )
        })}
      </div>

      {/* Progress bar */}
      <div className="mt-4 h-1 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-primary-500 transition-all duration-300"
          style={{
            width: `${((completedSteps.length + (currentStep ? 0.5 : 0)) / STEPS.length) * 100}%`,
          }}
        />
      </div>
    </div>
  )
}

export default ProcessingSteps
