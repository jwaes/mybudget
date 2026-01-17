/**
 * Login page component.
 *
 * Provides user authentication with email and password.
 * Per FR-AUTH-001, FR-AUTH-003, FR-AUTH-004, FR-AUTH-005.
 */

import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/lib/auth-context'

interface LocationState {
  message?: string
}

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [validationErrors, setValidationErrors] = useState<{
    email?: string
    password?: string
  }>({})

  const { login, isLoading, error, clearError } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  // Get any message passed from redirect (e.g., session expired)
  const state = location.state as LocationState | null
  const redirectMessage = state?.message

  const validateForm = (): boolean => {
    const errors: { email?: string; password?: string } = {}

    if (!email.trim()) {
      errors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = 'Please enter a valid email address'
    }

    if (!password) {
      errors.password = 'Password is required'
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    clearError()

    if (!validateForm()) {
      return
    }

    try {
      await login({ email, password })
      // Redirect to dashboard on success
      navigate('/', { replace: true })
    } catch {
      // Error is handled by auth context
    }
  }

  return (
    <div className="login-page">
      <div className="login-container">
        <h1>Log In</h1>

        {redirectMessage && (
          <div className="info-message" role="status">
            {redirectMessage}
          </div>
        )}

        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                if (validationErrors.email) {
                  setValidationErrors((prev) => ({ ...prev, email: undefined }))
                }
              }}
              disabled={isLoading}
              autoComplete="email"
              autoFocus
              aria-invalid={!!validationErrors.email}
              aria-describedby={validationErrors.email ? 'email-error' : undefined}
            />
            {validationErrors.email && (
              <span id="email-error" className="field-error" role="alert">
                {validationErrors.email}
              </span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
                if (validationErrors.password) {
                  setValidationErrors((prev) => ({ ...prev, password: undefined }))
                }
              }}
              disabled={isLoading}
              autoComplete="current-password"
              aria-invalid={!!validationErrors.password}
              aria-describedby={validationErrors.password ? 'password-error' : undefined}
            />
            {validationErrors.password && (
              <span id="password-error" className="field-error" role="alert">
                {validationErrors.password}
              </span>
            )}
          </div>

          <button type="submit" disabled={isLoading} className="submit-button">
            {isLoading ? 'Logging in...' : 'Log In'}
          </button>
        </form>

        <p className="auth-link">
          Don&apos;t have an account? <Link to="/register">Register</Link>
        </p>
      </div>

      <style>{`
        .login-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 1rem;
          background-color: #f5f5f5;
        }

        .login-container {
          width: 100%;
          max-width: 400px;
          padding: 2rem;
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }

        .login-container h1 {
          margin: 0 0 1.5rem;
          text-align: center;
          font-size: 1.5rem;
          color: #333;
        }

        .info-message {
          padding: 0.75rem;
          margin-bottom: 1rem;
          background-color: #e7f3ff;
          border: 1px solid #b8daff;
          border-radius: 4px;
          color: #004085;
          font-size: 0.875rem;
        }

        .error-message {
          padding: 0.75rem;
          margin-bottom: 1rem;
          background-color: #fee;
          border: 1px solid #fcc;
          border-radius: 4px;
          color: #c00;
          font-size: 0.875rem;
        }

        .form-group {
          margin-bottom: 1rem;
        }

        .form-group label {
          display: block;
          margin-bottom: 0.25rem;
          font-weight: 500;
          color: #333;
        }

        .form-group input {
          width: 100%;
          padding: 0.625rem;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 1rem;
          box-sizing: border-box;
        }

        .form-group input:focus {
          outline: none;
          border-color: #0066cc;
          box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
        }

        .form-group input:disabled {
          background-color: #f5f5f5;
          cursor: not-allowed;
        }

        .form-group input[aria-invalid="true"] {
          border-color: #c00;
        }

        .field-error {
          display: block;
          margin-top: 0.25rem;
          color: #c00;
          font-size: 0.875rem;
        }

        .submit-button {
          width: 100%;
          padding: 0.75rem;
          background-color: #0066cc;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          margin-top: 0.5rem;
        }

        .submit-button:hover:not(:disabled) {
          background-color: #0055aa;
        }

        .submit-button:disabled {
          background-color: #ccc;
          cursor: not-allowed;
        }

        .auth-link {
          margin-top: 1.5rem;
          text-align: center;
          color: #666;
          font-size: 0.875rem;
        }

        .auth-link a {
          color: #0066cc;
          text-decoration: none;
        }

        .auth-link a:hover {
          text-decoration: underline;
        }
      `}</style>
    </div>
  )
}

export default LoginPage
