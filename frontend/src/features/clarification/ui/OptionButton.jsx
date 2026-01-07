export function OptionButton({ label, selected, onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`
        w-full px-4 py-3 rounded-xl text-left transition-all duration-200
        border-2 flex items-center gap-3
        ${selected
          ? 'bg-accent-50 border-accent-500 text-accent-700'
          : 'bg-light-elevated border-light-border text-light-text-secondary hover:border-accent-500/50 hover:bg-white'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      <div className={`
        w-5 h-5 rounded-full border-2 flex items-center justify-center
        ${selected
          ? 'border-accent-500 bg-accent-500'
          : 'border-light-border'
        }
      `}>
        {selected && (
          <div className="w-2 h-2 rounded-full bg-white" />
        )}
      </div>
      <span className="flex-1">{label}</span>
    </button>
  )
}

export default OptionButton
