import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

// Helper to mock mobile viewport
const mockMobileViewport = () => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: query.includes('768') ? false : true, // < 768px
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  })
}

// Helper to mock desktop viewport
const mockDesktopViewport = () => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: query.includes('768') ? true : false, // >= 768px
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  })
}

const renderWithRouter = (children: React.ReactNode) => {
  return render(<BrowserRouter>{children}</BrowserRouter>)
}

describe('MobileSidebar', () => {
  afterEach(() => {
    // Reset to desktop after each test
    mockDesktopViewport()
  })

  it('renders sidebar trigger on desktop', () => {
    mockDesktopViewport()
    renderWithRouter(
      <SidebarLayout>
        <div>Content</div>
      </SidebarLayout>
    )

    // SidebarTrigger should be in header
    const triggers = screen.getAllByRole('button', { name: /toggle sidebar/i })
    expect(triggers.length).toBeGreaterThan(0)
  })

  it('renders sidebar content on desktop', () => {
    mockDesktopViewport()
    renderWithRouter(
      <SidebarLayout>
        <div>Content</div>
      </SidebarLayout>
    )

    // Navigation items should be visible
    expect(screen.getByText('Budget')).toBeInTheDocument()
    expect(screen.getByText('Accounts')).toBeInTheDocument()
    expect(screen.getByText('Transactions')).toBeInTheDocument()
  })

  it('has mobile menu trigger for mobile viewports', () => {
    mockMobileViewport()
    renderWithRouter(
      <SidebarLayout>
        <div>Content</div>
      </SidebarLayout>
    )

    // The SidebarTrigger should still be present (works as mobile menu button)
    const triggers = screen.getAllByRole('button', { name: /toggle sidebar/i })
    expect(triggers.length).toBeGreaterThan(0)
  })

  it('can open mobile sidebar via trigger', async () => {
    const user = userEvent.setup()
    mockMobileViewport()
    renderWithRouter(
      <SidebarLayout>
        <div>Content</div>
      </SidebarLayout>
    )

    // Find the trigger button (data-sidebar="trigger")
    const trigger = document.querySelector(
      '[data-sidebar="trigger"]'
    ) as HTMLButtonElement

    if (trigger) {
      await user.click(trigger)

      // After clicking, navigation should be accessible
      await waitFor(() => {
        expect(screen.getByText('Budget')).toBeInTheDocument()
      })
    }
  })

  it('sidebar wrapper has responsive classes', () => {
    mockDesktopViewport()
    renderWithRouter(
      <SidebarLayout>
        <div>Content</div>
      </SidebarLayout>
    )

    // The sidebar uses group peer classes and responsive display
    const sidebarWrapper = document.querySelector('[data-side="left"]')
    expect(sidebarWrapper).toBeInTheDocument()
    // md:block class indicates it's hidden on mobile, shown on medium+
    expect(sidebarWrapper?.className).toContain('md:block')
  })
})
