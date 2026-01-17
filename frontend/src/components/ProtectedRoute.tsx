/**
 * Protected route component.
 *
 * Wraps routes that require authentication.
 * Redirects to login page if user is not authenticated.
 * Per FR-AUTH-003.
 */

import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/lib/auth-context'

const SESSION_EXPIRED_MESSAGE = 'Your session has expired. Please log in again.'

interface ProtectedRouteProps {
  children: React.ReactNode
}

/**
 * Component that protects routes requiring authentication.
 *
 * - Shows a loading spinner while checking authentication status
 * - Redirects to /login if user is not authenticated
 * - Renders children if user is authenticated
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, isLoading, error } = useAuth()
  const location = useLocation()

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" aria-label="Loading">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>

        <style>{`
          .loading-container {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #f5f5f5;
          }

          .loading-spinner {
            text-align: center;
            color: #666;
          }

          .spinner {
            width: 40px;
            height: 40px;
            margin: 0 auto 1rem;
            border: 3px solid #e0e0e0;
            border-top-color: #0066cc;
            border-radius: 50%;
            animation: spin 1s linear infinite;
          }

          @keyframes spin {
            to {
              transform: rotate(360deg);
            }
          }
        `}</style>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!user) {
    // Check if this was a session expiry (error message will be set)
    const message = error === SESSION_EXPIRED_MESSAGE ? error : undefined
    // Save the attempted URL to redirect back after login
    return <Navigate to="/login" state={{ from: location, message }} replace />
  }

  // User is authenticated, render the protected content
  return <>{children}</>
}

export default ProtectedRoute
