/**
 * Authentication context and hook for MyBudget.
 *
 * Provides authentication state and actions throughout the application.
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react'
import { authService } from '@/services/authService'
import { ApiError, onSessionExpired } from '@/services/api'
import type { User, LoginCredentials, RegisterData } from '@/types/auth'

interface AuthContextType {
  /** The currently authenticated user, or null if not authenticated */
  user: User | null
  /** Whether the authentication state is being loaded */
  isLoading: boolean
  /** The most recent authentication error, if any */
  error: string | null
  /** Login with email and password */
  login: (credentials: LoginCredentials) => Promise<void>
  /** Logout the current user */
  logout: () => Promise<void>
  /** Register a new user */
  register: (data: RegisterData) => Promise<void>
  /** Clear any authentication errors */
  clearError: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

/**
 * Authentication provider component.
 *
 * Wraps the application to provide authentication context.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const currentUser = await authService.getCurrentUser()
        setUser(currentUser)
      } catch (err) {
        // Not authenticated is not an error state
        if (err instanceof ApiError && err.status === 401) {
          setUser(null)
        } else {
          console.error('Failed to check authentication:', err)
        }
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  // Listen for session expiry events from API calls
  useEffect(() => {
    const unsubscribe = onSessionExpired(() => {
      // Clear user state - ProtectedRoute will handle redirect
      setUser(null)
      setError('Your session has expired. Please log in again.')
    })

    return unsubscribe
  }, [])

  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true)
    setError(null)
    try {
      await authService.login(credentials)
      // Fetch user data after successful login
      const currentUser = await authService.getCurrentUser()
      setUser(currentUser)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail)
      } else {
        setError('An unexpected error occurred')
      }
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      await authService.logout()
      setUser(null)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail)
      } else {
        setError('An unexpected error occurred')
      }
      // Even if logout fails on server, clear local state
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const register = useCallback(async (data: RegisterData) => {
    setIsLoading(true)
    setError(null)
    try {
      await authService.register(data)
      // Auto-login after registration
      await authService.login({ email: data.email, password: data.password })
      const currentUser = await authService.getCurrentUser()
      setUser(currentUser)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail)
      } else {
        setError('An unexpected error occurred')
      }
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const value: AuthContextType = {
    user,
    isLoading,
    error,
    login,
    logout,
    register,
    clearError,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/**
 * Hook to access the authentication context.
 *
 * @returns The authentication context
 * @throws Error if used outside of AuthProvider
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default AuthContext
