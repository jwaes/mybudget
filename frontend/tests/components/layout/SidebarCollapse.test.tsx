import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

describe('SidebarCollapse', () => {
  it('renders in expanded state by default', () => {
    renderWithProviders(<AppSidebar />)

    // The sidebar should have data-state="expanded" initially
    const sidebar = document.querySelector('[data-sidebar="sidebar"]')
    const parentWithState = sidebar?.closest('[data-state]')
    expect(parentWithState).toHaveAttribute('data-state', 'expanded')
  })

  it('includes SidebarRail for collapse toggle', () => {
    renderWithProviders(<AppSidebar />)

    // SidebarRail is the edge trigger for collapse
    const rail = document.querySelector('[data-sidebar="rail"]')
    expect(rail).toBeInTheDocument()
    expect(rail?.tagName.toLowerCase()).toBe('button')
  })

  it('toggles sidebar state when rail is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<AppSidebar />)

    const rail = document.querySelector(
      '[data-sidebar="rail"]'
    ) as HTMLButtonElement
    expect(rail).toBeInTheDocument()

    // Get the parent element that tracks state
    const getSidebarState = () => {
      const sidebar = document.querySelector('[data-sidebar="sidebar"]')
      return sidebar?.closest('[data-state]')?.getAttribute('data-state')
    }

    // Initially expanded
    expect(getSidebarState()).toBe('expanded')

    // Click to collapse
    await user.click(rail)
    expect(getSidebarState()).toBe('collapsed')

    // Click again to expand
    await user.click(rail)
    expect(getSidebarState()).toBe('expanded')
  })

  it('supports collapsible="icon" mode', () => {
    renderWithProviders(<AppSidebar />)

    // The sidebar parent should have data-collapsible attribute
    const sidebarWrapper = document.querySelector('[data-collapsible]')
    expect(sidebarWrapper).toBeInTheDocument()
  })

  it('can be toggled via keyboard shortcut (Ctrl+B)', async () => {
    const user = userEvent.setup()
    renderWithProviders(<AppSidebar />)

    const getSidebarState = () => {
      const sidebar = document.querySelector('[data-sidebar="sidebar"]')
      return sidebar?.closest('[data-state]')?.getAttribute('data-state')
    }

    // Initially expanded
    expect(getSidebarState()).toBe('expanded')

    // Press Ctrl+B to toggle
    await user.keyboard('{Control>}b{/Control}')
    expect(getSidebarState()).toBe('collapsed')

    // Press Ctrl+B again to expand
    await user.keyboard('{Control>}b{/Control}')
    expect(getSidebarState()).toBe('expanded')
  })
})
