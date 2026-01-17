/**
 * Unit tests for Register page component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '@/lib/auth-context'
import { RegisterPage } from '@/pages/Register'

// Mock the auth service
vi.mock('@/services/authService', () => ({
  authService: {
    register: vi.fn(),
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
  email: 'newuser@example.com',
  timezone: 'Europe/Brussels',
  created_at: '2026-01-17T00:00:00Z',
  updated_at: '2026-01-17T00:00:00Z',
}

function renderRegisterPage() {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <RegisterPage />
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default: not authenticated
    vi.mocked(authService.getCurrentUser).mockRejectedValue({ status: 401 })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should render registration form with email, password, confirm password, and timezone fields', async () => {
    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    })

    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/timezone/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /register|sign up|create account/i })).toBeInTheDocument()
  })

  it('should render a link to the login page', async () => {
    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /log in|sign in|already have an account/i })).toBeInTheDocument()
    })
  })

  it('should show validation error for empty email', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    })

    const submitButton = screen.getByRole('button', { name: /register|sign up|create account/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/email.*required|please enter.*email/i)).toBeInTheDocument()
    })
  })

  it('should show validation error for invalid email format', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    })

    const emailInput = screen.getByLabelText(/email/i)
    await user.type(emailInput, 'invalid-email')

    const submitButton = screen.getByRole('button', { name: /register|sign up|create account/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/valid email|invalid email/i)).toBeInTheDocument()
    })
  })

  it('should show validation error for password shorter than 8 characters', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    })

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'short')

    const submitButton = screen.getByRole('button', { name: /register|sign up|create account/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/8 characters|too short|at least 8/i)).toBeInTheDocument()
    })
  })

  it('should show validation error when passwords do not match', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    })

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'differentpassword')

    const submitButton = screen.getByRole('button', { name: /register|sign up|create account/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/passwords.*match|do not match|must match/i)).toBeInTheDocument()
    })
  })

  it('should show validation error when timezone is not selected', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    })

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')

    const submitButton = screen.getByRole('button', { name: /register|sign up|create account/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/please select a timezone|timezone.*required/i)).toBeInTheDocument()
    })
  })

  it('should have timezone dropdown with IANA timezone options', async () => {
    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/timezone/i)).toBeInTheDocument()
    })

    const timezoneSelect = screen.getByLabelText(/timezone/i)

    // Should have common IANA timezones
    expect(timezoneSelect).toBeInTheDocument()

    // Check for presence of option elements (either as options or when dropdown is clicked)
    const options = timezoneSelect.querySelectorAll('option')
    // At minimum should have placeholder + some timezone options
    expect(options.length).toBeGreaterThan(1)
  })

  it('should submit registration and auto-login on success', async () => {
    const user = userEvent.setup()

    vi.mocked(authService.register).mockResolvedValueOnce(mockUser)
    vi.mocked(authService.login).mockResolvedValueOnce({
      message: 'Login successful',
      user_id: 'user-123',
    })
    vi.mocked(authService.getCurrentUser).mockResolvedValueOnce(mockUser)

    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    })

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const timezoneSelect = screen.getByLabelText(/timezone/i)

    await user.type(emailInput, 'newuser@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')
    await user.selectOptions(timezoneSelect, 'Europe/Brussels')

    const submitButton = screen.getByRole('button', { name: /register|sign up|create account/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(authService.register).toHaveBeenCalledWith({
        email: 'newuser@example.com',
        password: 'password123',
        timezone: 'Europe/Brussels',
      })
    })
  })

  it('should show error message for duplicate email', async () => {
    const user = userEvent.setup()

    vi.mocked(authService.register).mockRejectedValueOnce(
      new ApiError(400, 'Email already registered')
    )

    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    })

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const timezoneSelect = screen.getByLabelText(/timezone/i)

    await user.type(emailInput, 'existing@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')
    await user.selectOptions(timezoneSelect, 'Europe/Brussels')

    const submitButton = screen.getByRole('button', { name: /register|sign up|create account/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/already registered|email.*exists|already in use/i)).toBeInTheDocument()
    })
  })

  it('should show loading state while submitting', async () => {
    const user = userEvent.setup()

    let resolveRegister: (value: typeof mockUser) => void
    const registerPromise = new Promise<typeof mockUser>((resolve) => {
      resolveRegister = resolve
    })
    vi.mocked(authService.register).mockReturnValueOnce(registerPromise)

    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    })

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const timezoneSelect = screen.getByLabelText(/timezone/i)

    await user.type(emailInput, 'newuser@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')
    await user.selectOptions(timezoneSelect, 'Europe/Brussels')

    const submitButton = screen.getByRole('button', { name: /register|sign up|create account/i })
    await user.click(submitButton)

    // Button should be disabled or show loading state
    await waitFor(() => {
      const button = screen.getByRole('button', { name: /register|sign|creating|loading/i })
      expect(button).toBeDisabled()
    })

    // Cleanup
    resolveRegister!(mockUser)
  })

  it('should disable form inputs while submitting', async () => {
    const user = userEvent.setup()

    let resolveRegister: (value: typeof mockUser) => void
    const registerPromise = new Promise<typeof mockUser>((resolve) => {
      resolveRegister = resolve
    })
    vi.mocked(authService.register).mockReturnValueOnce(registerPromise)

    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    })

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const timezoneSelect = screen.getByLabelText(/timezone/i)

    await user.type(emailInput, 'newuser@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')
    await user.selectOptions(timezoneSelect, 'Europe/Brussels')

    const submitButton = screen.getByRole('button', { name: /register|sign up|create account/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(emailInput).toBeDisabled()
      expect(passwordInput).toBeDisabled()
      expect(confirmPasswordInput).toBeDisabled()
      expect(timezoneSelect).toBeDisabled()
    })

    // Cleanup
    resolveRegister!(mockUser)
  })
})
