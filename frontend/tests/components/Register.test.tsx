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
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
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

    // Wait for form to be fully rendered and enabled (after initial auth check)
    await waitFor(
      () => {
        const emailInput = screen.getByLabelText(/email/i)
        expect(emailInput).toBeInTheDocument()
        expect(emailInput).not.toBeDisabled()
      },
      { timeout: 3000 }
    )

    const submitButton = screen.getByRole('button', { name: /create account/i })
    await user.click(submitButton)

    // Wait for validation error
    await waitFor(
      () => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('should show validation error for invalid email format', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    // Wait for form to be fully rendered
    await waitFor(
      () => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
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

    const submitButton = screen.getByRole('button', { name: /create account/i })
    await user.click(submitButton)

    // Wait for validation error
    await waitFor(
      () => {
        expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('should show validation error for password shorter than 8 characters', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    // Wait for form to be fully rendered
    await waitFor(
      () => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'short')

    const submitButton = screen.getByRole('button', { name: /create account/i })
    await user.click(submitButton)

    // Wait for validation error
    await waitFor(
      () => {
        expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('should show validation error when passwords do not match', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    // Wait for form to be fully rendered
    await waitFor(
      () => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'differentpassword')

    const submitButton = screen.getByRole('button', { name: /create account/i })
    await user.click(submitButton)

    // Wait for validation error
    await waitFor(
      () => {
        expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('should show validation error when timezone is not selected', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    // Wait for form to be fully rendered
    await waitFor(
      () => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')

    const submitButton = screen.getByRole('button', { name: /create account/i })
    await user.click(submitButton)

    // Wait for validation error
    await waitFor(
      () => {
        expect(screen.getByText(/please select a timezone/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('should have timezone dropdown with IANA timezone options', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    await waitFor(() => {
      expect(screen.getByRole('combobox', { name: /timezone/i })).toBeInTheDocument()
    })

    const timezoneSelect = screen.getByRole('combobox', { name: /timezone/i })

    // Should have common IANA timezones - open dropdown to check
    await user.click(timezoneSelect)

    await waitFor(() => {
      // Check for some common timezone options (underscores replaced with spaces in display)
      expect(screen.getByRole('option', { name: /America\/New York/ })).toBeInTheDocument()
    })
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
    const timezoneSelect = screen.getByRole('combobox', { name: /timezone/i })

    await user.type(emailInput, 'newuser@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')

    // Select timezone using shadcn Select (click to open, click option)
    await user.click(timezoneSelect)
    await waitFor(() => {
      expect(screen.getByRole('option', { name: /Europe\/Brussels/ })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('option', { name: /Europe\/Brussels/ }))

    const submitButton = screen.getByRole('button', { name: /create account/i })
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
    const timezoneSelect = screen.getByRole('combobox', { name: /timezone/i })

    await user.type(emailInput, 'existing@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')

    // Select timezone using shadcn Select
    await user.click(timezoneSelect)
    await waitFor(() => {
      expect(screen.getByRole('option', { name: /Europe\/Brussels/ })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('option', { name: /Europe\/Brussels/ }))

    const submitButton = screen.getByRole('button', { name: /create account/i })
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
    const timezoneSelect = screen.getByRole('combobox', { name: /timezone/i })

    await user.type(emailInput, 'newuser@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')

    // Select timezone using shadcn Select
    await user.click(timezoneSelect)
    await waitFor(() => {
      expect(screen.getByRole('option', { name: /Europe\/Brussels/ })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('option', { name: /Europe\/Brussels/ }))

    const submitButton = screen.getByRole('button', { name: /create account/i })
    await user.click(submitButton)

    // Button should show loading text and be disabled
    await waitFor(
      () => {
        const button = screen.getByRole('button', { name: /creating account/i })
        expect(button).toBeDisabled()
      },
      { timeout: 3000 }
    )

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
    const timezoneSelect = screen.getByRole('combobox', { name: /timezone/i })

    await user.type(emailInput, 'newuser@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')

    // Select timezone using shadcn Select
    await user.click(timezoneSelect)
    await waitFor(() => {
      expect(screen.getByRole('option', { name: /Europe\/Brussels/ })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('option', { name: /Europe\/Brussels/ }))

    const submitButton = screen.getByRole('button', { name: /create account/i })
    await user.click(submitButton)

    // First wait for the loading state to be visible (button text changes)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /creating account/i })).toBeInTheDocument()
    })

    // Now check that inputs are disabled
    expect(emailInput).toBeDisabled()
    expect(passwordInput).toBeDisabled()
    expect(confirmPasswordInput).toBeDisabled()
    // shadcn Select uses disabled attribute
    expect(timezoneSelect).toBeDisabled()

    // Cleanup
    resolveRegister!(mockUser)
  })
})
