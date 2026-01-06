import React, { useEffect, useState, useCallback } from 'react';
import '../styles/animations.css';

/**
 * Toast notification types
 */
const TOAST_TYPES = {
  success: {
    icon: '✓',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-800',
    iconBg: 'bg-green-100',
  },
  error: {
    icon: '✕',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-800',
    iconBg: 'bg-red-100',
  },
  warning: {
    icon: '!',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    textColor: 'text-yellow-800',
    iconBg: 'bg-yellow-100',
  },
  info: {
    icon: 'i',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-800',
    iconBg: 'bg-blue-100',
  },
};

/**
 * Single toast component
 */
function ToastItem({ id, type, message, onClose, duration = 5000 }) {
  const [isExiting, setIsExiting] = useState(false);
  const styles = TOAST_TYPES[type] || TOAST_TYPES.info;

  const handleClose = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => {
      onClose(id);
    }, 300);
  }, [id, onClose]);

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(handleClose, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, handleClose]);

  return (
    <div
      role="alert"
      aria-live="polite"
      className={`
        flex items-center gap-3 p-4 rounded-lg border shadow-lg
        ${styles.bgColor} ${styles.borderColor}
        ${isExiting ? 'toast-exit' : 'toast-enter'}
      `}
    >
      {/* Icon */}
      <div
        className={`
          flex items-center justify-center w-6 h-6 rounded-full
          ${styles.iconBg} ${styles.textColor}
          text-sm font-bold
        `}
      >
        {styles.icon}
      </div>

      {/* Message */}
      <p className={`flex-1 text-sm ${styles.textColor}`}>{message}</p>

      {/* Close button */}
      <button
        onClick={handleClose}
        className={`
          p-1 rounded hover:bg-black/5 transition-colors
          ${styles.textColor}
        `}
        aria-label="알림 닫기"
      >
        <svg
          className="w-4 h-4"
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
  );
}

/**
 * Toast container component
 */
function ToastContainer({ toasts, removeToast, position = 'top-right' }) {
  const positionClasses = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-center': 'top-4 left-1/2 -translate-x-1/2',
    'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2',
  };

  if (!toasts.length) return null;

  return (
    <div
      className={`fixed z-50 flex flex-col gap-2 ${positionClasses[position]}`}
      aria-live="polite"
      aria-label="알림"
    >
      {toasts.map((toast) => (
        <ToastItem
          key={toast.id}
          id={toast.id}
          type={toast.type}
          message={toast.message}
          duration={toast.duration}
          onClose={removeToast}
        />
      ))}
    </div>
  );
}

/**
 * Toast hook for managing toasts
 */
export function useToast() {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((type, message, duration = 5000) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, type, message, duration }]);
    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const success = useCallback(
    (message, duration) => addToast('success', message, duration),
    [addToast]
  );

  const error = useCallback(
    (message, duration) => addToast('error', message, duration),
    [addToast]
  );

  const warning = useCallback(
    (message, duration) => addToast('warning', message, duration),
    [addToast]
  );

  const info = useCallback(
    (message, duration) => addToast('info', message, duration),
    [addToast]
  );

  const clearAll = useCallback(() => {
    setToasts([]);
  }, []);

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    warning,
    info,
    clearAll,
  };
}

/**
 * Toast provider context
 */
const ToastContext = React.createContext(null);

export function ToastProvider({ children, position = 'top-right' }) {
  const toast = useToast();

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <ToastContainer
        toasts={toast.toasts}
        removeToast={toast.removeToast}
        position={position}
      />
    </ToastContext.Provider>
  );
}

export function useToastContext() {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error('useToastContext must be used within a ToastProvider');
  }
  return context;
}

export default ToastContainer;
