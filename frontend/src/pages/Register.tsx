/**
 * Registration page component.
 *
 * Provides new user account creation with email, password, and timezone.
 * Per FR-AUTH-002, FR-AUTH-008, FR-AUTH-009.
 */

import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/lib/auth-context'

// Common IANA timezones for the dropdown
const TIMEZONES = [
  'Africa/Cairo',
  'Africa/Johannesburg',
  'Africa/Lagos',
  'America/Anchorage',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'America/New_York',
  'America/Sao_Paulo',
  'America/Toronto',
  'Asia/Bangkok',
  'Asia/Dubai',
  'Asia/Hong_Kong',
  'Asia/Kolkata',
  'Asia/Seoul',
  'Asia/Shanghai',
  'Asia/Singapore',
  'Asia/Tokyo',
  'Australia/Melbourne',
  'Australia/Sydney',
  'Europe/Amsterdam',
  'Europe/Berlin',
  'Europe/Brussels',
  'Europe/Istanbul',
  'Europe/London',
  'Europe/Madrid',
  'Europe/Moscow',
  'Europe/Paris',
  'Europe/Rome',
  'Europe/Warsaw',
  'Pacific/Auckland',
  'Pacific/Honolulu',
  'UTC',
]

interface ValidationErrors {
  email?: string
  password?: string
  confirmPassword?: string
  timezone?: string
}

export function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [timezone, setTimezone] = useState('')
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({})

  const { register, isLoading, error, clearError } = useAuth()
  const navigate = useNavigate()

  const validateForm = (): boolean => {
    const errors: ValidationErrors = {}

    if (!email.trim()) {
      errors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = 'Please enter a valid email address'
    }

    if (!password) {
      errors.password = 'Password is required'
    } else if (password.length < 8) {
      errors.password = 'Password must be at least 8 characters'
    }

    if (!confirmPassword) {
      errors.confirmPassword = 'Please confirm your password'
    } else if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match'
    }

    if (!timezone) {
      errors.timezone = 'Please select a timezone'
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
      await register({ email, password, timezone })
      // Auto-login is handled by auth context, redirect to dashboard
      navigate('/', { replace: true })
    } catch {
      // Error is handled by auth context
    }
  }

  const clearFieldError = (field: keyof ValidationErrors) => {
    if (validationErrors[field]) {
      setValidationErrors((prev) => ({ ...prev, [field]: undefined }))
    }
  }

  return (
    <div className="register-page">
      <div className="register-container">
        <h1>Create Account</h1>

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
                clearFieldError('email')
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
                clearFieldError('password')
              }}
              disabled={isLoading}
              autoComplete="new-password"
              aria-invalid={!!validationErrors.password}
              aria-describedby={validationErrors.password ? 'password-error' : undefined}
            />
            {validationErrors.password && (
              <span id="password-error" className="field-error" role="alert">
                {validationErrors.password}
              </span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value)
                clearFieldError('confirmPassword')
              }}
              disabled={isLoading}
              autoComplete="new-password"
              aria-invalid={!!validationErrors.confirmPassword}
              aria-describedby={validationErrors.confirmPassword ? 'confirm-password-error' : undefined}
            />
            {validationErrors.confirmPassword && (
              <span id="confirm-password-error" className="field-error" role="alert">
                {validationErrors.confirmPassword}
              </span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="timezone">Timezone</label>
            <select
              id="timezone"
              value={timezone}
              onChange={(e) => {
                setTimezone(e.target.value)
                clearFieldError('timezone')
              }}
              disabled={isLoading}
              aria-invalid={!!validationErrors.timezone}
              aria-describedby={validationErrors.timezone ? 'timezone-error' : undefined}
            >
              <option value="">Select your timezone...</option>
              {TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>
                  {tz.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
            {validationErrors.timezone && (
              <span id="timezone-error" className="field-error" role="alert">
                {validationErrors.timezone}
              </span>
            )}
          </div>

          <button type="submit" disabled={isLoading} className="submit-button">
            {isLoading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <p className="auth-link">
          Already have an account? <Link to="/login">Log In</Link>
        </p>
      </div>

      <style>{`
        .register-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 1rem;
          background-color: #f5f5f5;
        }

        .register-container {
          width: 100%;
          max-width: 400px;
          padding: 2rem;
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }

        .register-container h1 {
          margin: 0 0 1.5rem;
          text-align: center;
          font-size: 1.5rem;
          color: #333;
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

        .form-group input,
        .form-group select {
          width: 100%;
          padding: 0.625rem;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 1rem;
          box-sizing: border-box;
        }

        .form-group input:focus,
        .form-group select:focus {
          outline: none;
          border-color: #0066cc;
          box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
        }

        .form-group input:disabled,
        .form-group select:disabled {
          background-color: #f5f5f5;
          cursor: not-allowed;
        }

        .form-group input[aria-invalid="true"],
        .form-group select[aria-invalid="true"] {
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

export default RegisterPage
