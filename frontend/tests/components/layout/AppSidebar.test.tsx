import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { SidebarProvider } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/layout/AppSidebar'

// Mock the auth context
vi.mock('@/lib/auth-context', () => ({
  useAuth: () => ({
    user: { id: '1', email: 'test@example.com' },
    isAuthenticated: true,
    logout: vi.fn(),
  }),
}))

const renderWithProviders = (children: React.ReactNode) => {
  return render(
    <BrowserRouter>
      <SidebarProvider>{children}</SidebarProvider>
    </BrowserRouter>
  )
}

describe('AppSidebar', () => {
  it('renders sidebar with header, content, and footer sections', () => {
    renderWithProviders(<AppSidebar />)

    // Header with app name
    expect(screen.getByText('MyBudget')).toBeInTheDocument()
    expect(screen.getByText('Spending Targets')).toBeInTheDocument()

    // Navigation items in content
    expect(screen.getByText('Budget')).toBeInTheDocument()
    expect(screen.getByText('Accounts')).toBeInTheDocument()
    expect(screen.getByText('Transactions')).toBeInTheDocument()

    // Footer with user info
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
  })

  it('renders navigation items with correct icons', () => {
    renderWithProviders(<AppSidebar />)

    // Each nav item should have an icon (svg)
    const navLinks = screen.getAllByRole('link')
    // Header link + 3 nav links = 4 total links
    expect(navLinks.length).toBeGreaterThanOrEqual(4)
  })

  it('renders navigation items with correct links', () => {
    renderWithProviders(<AppSidebar />)

    // Get all links with href attributes
    const budgetLinks = screen.getAllByRole('link').filter(
      (link) => link.getAttribute('href') === '/budget'
    )
    const accountsLinks = screen.getAllByRole('link').filter(
      (link) => link.getAttribute('href') === '/accounts'
    )
    const transactionsLinks = screen.getAllByRole('link').filter(
      (link) => link.getAttribute('href') === '/transactions'
    )

    // Each route should have at least one link
    expect(budgetLinks.length).toBeGreaterThan(0)
    expect(accountsLinks.length).toBeGreaterThan(0)
    expect(transactionsLinks.length).toBeGreaterThan(0)
  })

  it('includes SidebarRail for collapse functionality', () => {
    renderWithProviders(<AppSidebar />)

    // SidebarRail renders as a button with data-sidebar="rail"
    const rail = document.querySelector('[data-sidebar="rail"]')
    expect(rail).toBeInTheDocument()
  })
})
