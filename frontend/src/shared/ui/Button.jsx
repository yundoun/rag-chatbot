export function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  className = '',
  onClick,
  ...props
}) {
  const baseStyles = `
    inline-flex items-center justify-center font-medium rounded-lg
    transition-all duration-200 ease-in-out
    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white
    disabled:opacity-50 disabled:cursor-not-allowed
  `

  const variants = {
    primary: `
      bg-accent-500 text-white
      hover:bg-accent-600 hover:shadow-glow-blue
      focus:ring-accent-500
    `,
    secondary: `
      bg-light-elevated text-light-text-primary
      border border-light-border
      hover:bg-light-border hover:border-accent-500
      focus:ring-accent-500
    `,
    ghost: `
      bg-transparent text-light-text-secondary
      hover:bg-light-elevated hover:text-light-text-primary
      focus:ring-accent-500
    `,
    danger: `
      bg-red-50 text-red-600
      border border-red-200
      hover:bg-red-100 hover:border-red-300
      focus:ring-red-500
    `,
    mint: `
      bg-mint-500 text-white
      hover:bg-mint-600 hover:shadow-glow-mint
      focus:ring-mint-500
    `,
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-2',
    icon: 'p-2',
  }

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
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
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {children}
    </button>
  )
}

export default Button
