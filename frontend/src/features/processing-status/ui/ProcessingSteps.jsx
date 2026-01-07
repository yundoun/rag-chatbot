import { PROCESSING_STEPS } from '@shared/config'
import { IconCheck } from '@shared/ui'

const STEP_ICONS = {
  analyzing: '🔍',
  searching: '📚',
  evaluating: '⚖️',
  generating: '✍️',
}

export function ProcessingSteps({ currentStep, completedSteps = [] }) {
  const getStepStatus = (stepKey) => {
    if (completedSteps.includes(stepKey)) return 'completed'
    if (currentStep === stepKey) return 'current'
    return 'pending'
  }

  const progress = ((completedSteps.length + (currentStep ? 0.5 : 0)) / PROCESSING_STEPS.length) * 100

  return (
    <div className="
      p-4 bg-white
      rounded-xl border border-light-border
      shadow-sm animate-fade-in
    ">
      <h4 className="text-xs font-medium text-light-text-muted mb-4 uppercase tracking-wider">
        처리 진행 상황
      </h4>

      <div className="space-y-3">
        {PROCESSING_STEPS.map((step, index) => {
          const status = getStepStatus(step.key)

          return (
            <div key={step.key} className="flex items-center gap-3">
              <div
                className={`
                  w-7 h-7 rounded-lg flex items-center justify-center text-xs font-medium
                  transition-all duration-300
                  ${status === 'completed'
                    ? 'bg-mint-500 text-white'
                    : status === 'current'
                    ? 'bg-accent-500 text-white animate-pulse'
                    : 'bg-light-elevated text-light-text-muted border border-light-border'
                  }
                `}
              >
                {status === 'completed' ? (
                  <IconCheck className="w-4 h-4" />
                ) : (
                  index + 1
                )}
              </div>

              <span className="text-lg">{STEP_ICONS[step.key]}</span>

              <span
                className={`
                  text-sm transition-colors
                  ${status === 'completed'
                    ? 'text-mint-600 font-medium'
                    : status === 'current'
                    ? 'text-accent-600 font-medium'
                    : 'text-light-text-muted'
                  }
                `}
              >
                {step.label}
              </span>

              {status === 'current' && (
                <div className="w-4 h-4 border-2 border-accent-500 border-t-transparent rounded-full animate-spin" />
              )}
            </div>
          )
        })}
      </div>

      <div className="mt-4 h-1.5 bg-light-elevated rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-accent-500 to-mint-500 transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  )
}

export default ProcessingSteps
