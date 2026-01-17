import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { SidebarLayout } from '@/components/layout/SidebarLayout'

// Mock the auth context
vi.mock('@/lib/auth-context', () => ({
  useAuth: () => ({
    user: { id: '1', email: 'test@example.com' },
    isAuthenticated: true,
    logout: vi.fn(),
  }),
}))

const renderWithRouter = (children: React.ReactNode) => {
  return render(<BrowserRouter>{children}</BrowserRouter>)
}

describe('SidebarLayout', () => {
  it('renders children content', () => {
    renderWithRouter(
      <SidebarLayout>
        <div data-testid="test-content">Test Content</div>
      </SidebarLayout>
    )

    expect(screen.getByTestId('test-content')).toBeInTheDocument()
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('provides SidebarProvider context', () => {
    renderWithRouter(
      <SidebarLayout>
        <div>Content</div>
      </SidebarLayout>
    )

    // SidebarProvider should be wrapping the content
    // The sidebar trigger should be accessible
    expect(screen.getByRole('main')).toBeInTheDocument()
  })

  it('renders sidebar with navigation', () => {
    renderWithRouter(
      <SidebarLayout>
        <div>Content</div>
      </SidebarLayout>
    )

    // Should have sidebar navigation items
    expect(screen.getByText('Budget')).toBeInTheDocument()
    expect(screen.getByText('Accounts')).toBeInTheDocument()
    expect(screen.getByText('Transactions')).toBeInTheDocument()
  })

  it('renders header with sidebar trigger', () => {
    renderWithRouter(
      <SidebarLayout>
        <div>Content</div>
      </SidebarLayout>
    )

    // Header should have a sidebar trigger button (data-sidebar="trigger")
    // There's also a SidebarRail button, so we need to be specific
    const triggers = screen.getAllByRole('button', { name: /toggle sidebar/i })
    const headerTrigger = triggers.find(
      (btn) => btn.getAttribute('data-sidebar') === 'trigger'
    )
    expect(headerTrigger).toBeInTheDocument()
  })
})
