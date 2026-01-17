/**
 * Unit tests for Login page component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '@/lib/auth-context'
import { LoginPage } from '@/pages/Login'

// Mock the auth service
vi.mock('@/services/authService', () => ({
  authService: {
    login: vi.fn(),
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
  },
}))

// Mock react-router-dom's useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

import { authService } from '@/services/authService'
import { ApiError } from '@/services/api'

const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
  timezone: 'Europe/Brussels',
  created_at: '2026-01-17T00:00:00Z',
  updated_at: '2026-01-17T00:00:00Z',
}

function renderLoginPage() {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default: not authenticated
    vi.mocked(authService.getCurrentUser).mockRejectedValue({ status: 401 })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should render login form with email and password fields', async () => {
    renderLoginPage()

    await waitFor(
      () => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument()
  })

  it('should render a link to the registration page', async () => {
    renderLoginPage()

    await waitFor(
      () => {
        expect(screen.getByRole('link', { name: /register|sign up|create account/i })).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('should show validation error for empty email', async () => {
    const user = userEvent.setup()
    renderLoginPage()

    await waitFor(
      () => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const submitButton = screen.getByRole('button', { name: /log in/i })
    await user.click(submitButton)

    await waitFor(
      () => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('should show validation error for invalid email format', async () => {
    const user = userEvent.setup()
    renderLoginPage()

    // Wait for form to be fully rendered and enabled (after initial auth check)
    await waitFor(
      () => {
        const emailInput = screen.getByLabelText(/email/i)
        expect(emailInput).toBeInTheDocument()
        expect(emailInput).not.toBeDisabled()
      },
      { timeout: 3000 }
    )

    const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement
    await user.type(emailInput, 'invalid-email')

    // Verify the value was typed
    await waitFor(
      () => {
        expect(emailInput.value).toBe('invalid-email')
      },
      { timeout: 3000 }
    )

    const submitButton = screen.getByRole('button', { name: /log in/i })
    await user.click(submitButton)

    await waitFor(
      () => {
        expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('should show validation error for empty password', async () => {
    const user = userEvent.setup()
    renderLoginPage()

    await waitFor(
      () => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement
    await user.type(emailInput, 'test@example.com')

    // Verify the value was typed
    await waitFor(
      () => {
        expect(emailInput.value).toBe('test@example.com')
      },
      { timeout: 3000 }
    )

    const submitButton = screen.getByRole('button', { name: /log in/i })
    await user.click(submitButton)

    await waitFor(
      () => {
        expect(screen.getByText(/password is required/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('should submit credentials and redirect on success', async () => {
    const user = userEvent.setup()

    vi.mocked(authService.login).mockResolvedValueOnce({
      message: 'Login successful',
      user_id: 'user-123',
    })
    vi.mocked(authService.getCurrentUser).mockResolvedValueOnce(mockUser)

    renderLoginPage()

    await waitFor(
      () => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement
    const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')

    // Verify values were typed
    await waitFor(
      () => {
        expect(emailInput.value).toBe('test@example.com')
        expect(passwordInput.value).toBe('password123')
      },
      { timeout: 3000 }
    )

    const submitButton = screen.getByRole('button', { name: /log in/i })
    await user.click(submitButton)

    await waitFor(
      () => {
        expect(authService.login).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
        })
      },
      { timeout: 3000 }
    )
  })

  it('should show error message for invalid credentials', async () => {
    const user = userEvent.setup()

    vi.mocked(authService.login).mockRejectedValueOnce(
      new ApiError(401, 'Invalid email or password')
    )

    renderLoginPage()

    await waitFor(
      () => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement
    const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'wrongpassword')

    // Verify values were typed
    await waitFor(
      () => {
        expect(emailInput.value).toBe('test@example.com')
        expect(passwordInput.value).toBe('wrongpassword')
      },
      { timeout: 3000 }
    )

    const submitButton = screen.getByRole('button', { name: /log in/i })
    await user.click(submitButton)

    await waitFor(
      () => {
        expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('should show loading state while submitting', async () => {
    const user = userEvent.setup()

    // Create a promise that won't resolve immediately
    let resolveLogin: (value: { message: string; user_id: string }) => void
    const loginPromise = new Promise<{ message: string; user_id: string }>((resolve) => {
      resolveLogin = resolve
    })
    vi.mocked(authService.login).mockReturnValueOnce(loginPromise)

    renderLoginPage()

    await waitFor(
      () => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement
    const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')

    // Verify values were typed
    await waitFor(
      () => {
        expect(emailInput.value).toBe('test@example.com')
        expect(passwordInput.value).toBe('password123')
      },
      { timeout: 3000 }
    )

    const submitButton = screen.getByRole('button', { name: /log in/i })
    await user.click(submitButton)

    // Wait for loading state
    await waitFor(
      () => {
        const button = screen.getByRole('button', { name: /logging in/i })
        expect(button).toBeDisabled()
      },
      { timeout: 3000 }
    )

    // Cleanup: resolve the promise
    resolveLogin!({ message: 'Login successful', user_id: 'user-123' })
  })

  it('should disable form inputs while submitting', async () => {
    const user = userEvent.setup()

    let resolveLogin: (value: { message: string; user_id: string }) => void
    const loginPromise = new Promise<{ message: string; user_id: string }>((resolve) => {
      resolveLogin = resolve
    })
    vi.mocked(authService.login).mockReturnValueOnce(loginPromise)

    renderLoginPage()

    await waitFor(
      () => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement
    const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')

    // Verify values were typed
    await waitFor(
      () => {
        expect(emailInput.value).toBe('test@example.com')
        expect(passwordInput.value).toBe('password123')
      },
      { timeout: 3000 }
    )

    const submitButton = screen.getByRole('button', { name: /log in/i })
    await user.click(submitButton)

    // Wait for loading state to show button text change
    await waitFor(
      () => {
        expect(screen.getByRole('button', { name: /logging in/i })).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    // Now inputs should be disabled
    expect(emailInput).toBeDisabled()
    expect(passwordInput).toBeDisabled()

    // Cleanup
    resolveLogin!({ message: 'Login successful', user_id: 'user-123' })
  })
})
