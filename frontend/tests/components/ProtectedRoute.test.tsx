/**
 * Unit tests for ProtectedRoute component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ProtectedRoute } from '@/components/ProtectedRoute'

// Mock the useAuth hook
vi.mock('@/lib/auth-context', () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from '@/lib/auth-context'

const mockUseAuth = vi.mocked(useAuth)

// Helper to render ProtectedRoute with router context
function renderWithRouter(
  ui: React.ReactNode,
  { initialRoute = '/protected' } = {}
) {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route
          path="/protected"
          element={<ProtectedRoute>{ui}</ProtectedRoute>}
        />
      </Routes>
    </MemoryRouter>
  )
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should show loading state while checking authentication', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: true,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
      clearError: vi.fn(),
    })

    renderWithRouter(<div>Protected Content</div>)

    // Should show loading spinner
    expect(screen.getByLabelText('Loading')).toBeInTheDocument()
    expect(screen.getByText('Loading...')).toBeInTheDocument()

    // Should NOT show protected content
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()

    // Should NOT redirect to login yet
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument()
  })

  it('should redirect to /login when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
      clearError: vi.fn(),
    })

    renderWithRouter(<div>Protected Content</div>)

    // Should redirect to login page
    expect(screen.getByText('Login Page')).toBeInTheDocument()

    // Should NOT show protected content
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('should render children when authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
      clearError: vi.fn(),
    })

    renderWithRouter(<div>Protected Content</div>)

    // Should show protected content
    expect(screen.getByText('Protected Content')).toBeInTheDocument()

    // Should NOT show login page
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument()
  })

  it('should pass session expired message to login page when error is set', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      error: 'Your session has expired. Please log in again.',
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
      clearError: vi.fn(),
    })

    // Custom render to capture location state
    let locationState: unknown
    render(
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route
            path="/login"
            element={
              <div>
                <span>Login Page</span>
                <LocationCapture onCapture={(state) => (locationState = state)} />
              </div>
            }
          />
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    )

    // Should redirect to login
    expect(screen.getByText('Login Page')).toBeInTheDocument()
  })

  it('should preserve attempted URL in location state for redirect after login', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
      clearError: vi.fn(),
    })

    renderWithRouter(<div>Protected Content</div>)

    // Should redirect to login
    expect(screen.getByText('Login Page')).toBeInTheDocument()
  })

  it('should not show loading when isLoading is false and user is null', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
      clearError: vi.fn(),
    })

    renderWithRouter(<div>Protected Content</div>)

    // Should NOT show loading spinner
    expect(screen.queryByLabelText('Loading')).not.toBeInTheDocument()
  })

  it('should render nested children correctly when authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
      clearError: vi.fn(),
    })

    renderWithRouter(
      <div>
        <h1>Dashboard</h1>
        <p>Welcome to your dashboard</p>
        <button>Click me</button>
      </div>
    )

    // Should render all nested children
    expect(screen.getByRole('heading', { name: 'Dashboard' })).toBeInTheDocument()
    expect(screen.getByText('Welcome to your dashboard')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument()
  })
})

// Helper component to capture location state
import { useLocation } from 'react-router-dom'

function LocationCapture({ onCapture }: { onCapture: (state: unknown) => void }) {
  const location = useLocation()
  onCapture(location.state)
  return null
}
