import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { SidebarProvider } from '@/components/ui/sidebar'
import { NavUser } from '@/components/layout/NavUser'

// Create a mock logout function we can track
const mockLogout = vi.fn()

// Mock the auth context
vi.mock('@/lib/auth-context', () => ({
  useAuth: () => ({
    user: { id: '1', email: 'testuser@example.com' },
    isAuthenticated: true,
    logout: mockLogout,
  }),
}))

const renderWithProviders = (children: React.ReactNode) => {
  return render(
    <BrowserRouter>
      <SidebarProvider>{children}</SidebarProvider>
    </BrowserRouter>
  )
}

describe('NavUser', () => {
  beforeEach(() => {
    mockLogout.mockClear()
  })

  it('displays user email', () => {
    renderWithProviders(<NavUser />)

    expect(screen.getByText('testuser@example.com')).toBeInTheDocument()
  })

  it('displays username extracted from email', () => {
    renderWithProviders(<NavUser />)

    // Shows the part before @ as username
    expect(screen.getByText('testuser')).toBeInTheDocument()
  })

  it('renders user icon', () => {
    renderWithProviders(<NavUser />)

    // User icon should be rendered (lucide-react User icon)
    const iconContainers = document.querySelectorAll('.lucide-user')
    expect(iconContainers.length).toBeGreaterThan(0)
  })

  it('opens dropdown menu when clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<NavUser />)

    // Find and click the trigger button
    const trigger = screen.getByRole('button')
    await user.click(trigger)

    // Dropdown should show "Log out" option
    await waitFor(() => {
      expect(screen.getByText('Log out')).toBeInTheDocument()
    })
  })

  it('calls logout when Log out is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<NavUser />)

    // Open dropdown
    const trigger = screen.getByRole('button')
    await user.click(trigger)

    // Click logout
    await waitFor(() => {
      expect(screen.getByText('Log out')).toBeInTheDocument()
    })

    const logoutButton = screen.getByText('Log out')
    await user.click(logoutButton)

    // Logout should have been called
    expect(mockLogout).toHaveBeenCalledTimes(1)
  })

  it('shows ChevronsUpDown icon indicating dropdown', () => {
    renderWithProviders(<NavUser />)

    // The chevrons icon indicates there's a dropdown
    const chevronsIcon = document.querySelector('.lucide-chevrons-up-down')
    expect(chevronsIcon).toBeInTheDocument()
  })
})
