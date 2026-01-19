/**
 * Unit tests for auth-context.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from '@/lib/auth-context'
import { ApiError } from '@/services/api'
import type { User } from '@/types/auth'

// Mock the authService
vi.mock('@/services/authService', () => ({
  authService: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
  },
}))

// Mock onSessionExpired
vi.mock('@/services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/api')>()
  return {
    ...actual,
    onSessionExpired: vi.fn(() => vi.fn()), // Return unsubscribe function
  }
})

import { authService } from '@/services/authService'
import { onSessionExpired } from '@/services/api'

const mockAuthService = vi.mocked(authService)
const mockOnSessionExpired = vi.mocked(onSessionExpired)

const mockUser: User = {
  id: 'user-123',
  email: 'test@example.com',
  name: 'Test User',
  created_at: '2026-01-01T00:00:00Z',
}

// Test component to use the hook
function AuthConsumer({ onRender }: { onRender?: (auth: ReturnType<typeof useAuth>) => void }) {
  const auth = useAuth()
  onRender?.(auth)

  return (
    <div>
      <span data-testid="user">{auth.user?.email || 'no user'}</span>
      <span data-testid="loading">{auth.isLoading ? 'loading' : 'not loading'}</span>
      <span data-testid="error">{auth.error || 'no error'}</span>
      <button onClick={() => auth.login({ email: 'test@example.com', password: 'password' })}>
        Login
      </button>
      <button onClick={() => auth.logout()}>Logout</button>
      <button onClick={() => auth.register({ email: 'new@example.com', password: 'password', name: 'New User' })}>
        Register
      </button>
      <button onClick={() => auth.clearError()}>Clear Error</button>
    </div>
  )
}

describe('auth-context', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockOnSessionExpired.mockReturnValue(vi.fn())
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('AuthProvider', () => {
    it('should check auth on mount and set user if authenticated', async () => {
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser)

      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not loading')
      })

      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
    })

    it('should handle 401 on initial auth check gracefully', async () => {
      mockAuthService.getCurrentUser.mockRejectedValue(new ApiError(401, 'Not authenticated'))

      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not loading')
      })

      expect(screen.getByTestId('user')).toHaveTextContent('no user')
      expect(screen.getByTestId('error')).toHaveTextContent('no error')
    })

    it('should handle other errors on initial auth check', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Network error'))

      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not loading')
      })

      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })

    it('should subscribe to session expiry events', () => {
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser)

      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      )

      expect(mockOnSessionExpired).toHaveBeenCalled()
    })
  })

  describe('login', () => {
    it('should login successfully and set user', async () => {
      const user = userEvent.setup()
      mockAuthService.getCurrentUser.mockResolvedValueOnce(null as unknown as User)
      mockAuthService.login.mockResolvedValue(undefined)
      mockAuthService.getCurrentUser.mockResolvedValueOnce(mockUser)

      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not loading')
      })

      await user.click(screen.getByText('Login'))

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      })

      expect(mockAuthService.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password',
      })
    })

    it('should handle login error with ApiError', async () => {
      const user = userEvent.setup()
      mockAuthService.getCurrentUser.mockResolvedValueOnce(null as unknown as User)
      mockAuthService.login.mockRejectedValue(new ApiError(401, 'Invalid credentials'))

      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not loading')
      })

      await user.click(screen.getByText('Login'))

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Invalid credentials')
      })
    })

    it('should handle login error with generic error', async () => {
      const user = userEvent.setup()
      mockAuthService.getCurrentUser.mockResolvedValueOnce(null as unknown as User)
      mockAuthService.login.mockRejectedValue(new Error('Network error'))

      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not loading')
      })

      await user.click(screen.getByText('Login'))

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('An unexpected error occurred')
      })
    })
  })

  describe('logout', () => {
    it('should logout successfully', async () => {
      const user = userEvent.setup()
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser)
      mockAuthService.logout.mockResolvedValue(undefined)

      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      })

      await user.click(screen.getByText('Logout'))

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('no user')
      })
    })

    it('should clear user even if logout fails with ApiError', async () => {
      const user = userEvent.setup()
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser)
      mockAuthService.logout.mockRejectedValue(new ApiError(500, 'Server error'))

      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      })

      await user.click(screen.getByText('Logout'))

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('no user')
        expect(screen.getByTestId('error')).toHaveTextContent('Server error')
      })
    })

    it('should clear user even if logout fails with generic error', async () => {
      const user = userEvent.setup()
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser)
      mockAuthService.logout.mockRejectedValue(new Error('Network error'))

      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      })

      await user.click(screen.getByText('Logout'))

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('no user')
        expect(screen.getByTestId('error')).toHaveTextContent('An unexpected error occurred')
      })
    })
  })

  describe('register', () => {
    it('should register and auto-login successfully', async () => {
      const user = userEvent.setup()
      mockAuthService.getCurrentUser.mockResolvedValueOnce(null as unknown as User)
      mockAuthService.register.mockResolvedValue(undefined)
      mockAuthService.login.mockResolvedValue(undefined)
      mockAuthService.getCurrentUser.mockResolvedValueOnce(mockUser)

      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not loading')
      })

      await user.click(screen.getByText('Register'))

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      })

      expect(mockAuthService.register).toHaveBeenCalledWith({
        email: 'new@example.com',
        password: 'password',
        name: 'New User',
      })
    })

    it('should handle register error with ApiError', async () => {
      const user = userEvent.setup()
      mockAuthService.getCurrentUser.mockResolvedValueOnce(null as unknown as User)
      mockAuthService.register.mockRejectedValue(new ApiError(400, 'Email already exists'))

      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not loading')
      })

      await user.click(screen.getByText('Register'))

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Email already exists')
      })
    })

    it('should handle register error with generic error', async () => {
      const user = userEvent.setup()
      mockAuthService.getCurrentUser.mockResolvedValueOnce(null as unknown as User)
      mockAuthService.register.mockRejectedValue(new Error('Network error'))

      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not loading')
      })

      await user.click(screen.getByText('Register'))

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('An unexpected error occurred')
      })
    })
  })

  describe('clearError', () => {
    it('should clear error state', async () => {
      const user = userEvent.setup()
      mockAuthService.getCurrentUser.mockResolvedValueOnce(null as unknown as User)
      mockAuthService.login.mockRejectedValue(new ApiError(401, 'Invalid credentials'))

      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not loading')
      })

      await user.click(screen.getByText('Login'))

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Invalid credentials')
      })

      await user.click(screen.getByText('Clear Error'))

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('no error')
      })
    })
  })

  describe('useAuth', () => {
    it('should throw error when used outside provider', () => {
      const originalError = console.error
      console.error = vi.fn()

      expect(() => {
        render(<AuthConsumer />)
      }).toThrow('useAuth must be used within an AuthProvider')

      console.error = originalError
    })
  })
})
