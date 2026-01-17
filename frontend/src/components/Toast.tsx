/**
 * Toast notification component.
 *
 * Simple toast/snackbar for showing feedback messages.
 */

import { useState, useEffect, createContext, useContext, useCallback, type ReactNode } from 'react'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

interface Toast {
  id: string
  message: string
  type: ToastType
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType) => void
  showSuccess: (message: string) => void
  showError: (message: string) => void
  showInfo: (message: string) => void
  showWarning: (message: string) => void
}

const ToastContext = createContext<ToastContextType | null>(null)

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

interface ToastProviderProps {
  children: ReactNode
}

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const showToast = useCallback((message: string, type: ToastType = 'success') => {
    const id = Date.now().toString()
    setToasts((prev) => [...prev, { id, message, type }])
  }, [])

  const showSuccess = useCallback((message: string) => showToast(message, 'success'), [showToast])
  const showError = useCallback((message: string) => showToast(message, 'error'), [showToast])
  const showInfo = useCallback((message: string) => showToast(message, 'info'), [showToast])
  const showWarning = useCallback((message: string) => showToast(message, 'warning'), [showToast])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ showToast, showSuccess, showError, showInfo, showWarning }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  )
}

interface ToastContainerProps {
  toasts: Toast[]
  onRemove: (id: string) => void
}

function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}

      <style>{`
        .toast-container {
          position: fixed;
          bottom: 1rem;
          right: 1rem;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          z-index: 2000;
          pointer-events: none;
        }
      `}</style>
    </div>
  )
}

interface ToastItemProps {
  toast: Toast
  onRemove: (id: string) => void
}

function ToastItem({ toast, onRemove }: ToastItemProps) {
  const [isExiting, setIsExiting] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsExiting(true)
      setTimeout(() => onRemove(toast.id), 300)
    }, 3000)

    return () => clearTimeout(timer)
  }, [toast.id, onRemove])

  const handleClose = () => {
    setIsExiting(true)
    setTimeout(() => onRemove(toast.id), 300)
  }

  return (
    <div className={`toast toast-${toast.type} ${isExiting ? 'toast-exit' : ''}`}>
      <span className="toast-message">{toast.message}</span>
      <button className="toast-close" onClick={handleClose} aria-label="Close">
        &times;
      </button>

      <style>{`
        .toast {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem 1rem;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          pointer-events: auto;
          animation: slideIn 0.3s ease;
          min-width: 250px;
          max-width: 400px;
        }

        .toast-exit {
          animation: slideOut 0.3s ease forwards;
        }

        .toast-success {
          background: #22a722;
          color: white;
        }

        .toast-error {
          background: #c00;
          color: white;
        }

        .toast-info {
          background: #0066cc;
          color: white;
        }

        .toast-warning {
          background: #f59e0b;
          color: white;
        }

        .toast-message {
          flex: 1;
          font-size: 0.875rem;
          font-weight: 500;
        }

        .toast-close {
          background: none;
          border: none;
          color: inherit;
          font-size: 1.25rem;
          cursor: pointer;
          padding: 0;
          line-height: 1;
          opacity: 0.8;
        }

        .toast-close:hover {
          opacity: 1;
        }

        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }

        @keyframes slideOut {
          from {
            transform: translateX(0);
            opacity: 1;
          }
          to {
            transform: translateX(100%);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  )
}

export default ToastProvider
