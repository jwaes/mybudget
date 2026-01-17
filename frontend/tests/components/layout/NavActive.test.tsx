import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
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

const renderWithRoute = (initialRoute: string) => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <SidebarProvider>
        <AppSidebar />
      </SidebarProvider>
    </MemoryRouter>
  )
}

// Helper to find nav links (not header links) - nav links have data-size="default"
const getNavLink = (text: string) => {
  const links = screen.getAllByRole('link')
  return links.find(
    (link) =>
      link.textContent?.includes(text) &&
      link.getAttribute('data-size') === 'default'
  )
}

describe('NavActive - Active navigation highlighting', () => {
  it('highlights Budget as active on root path', () => {
    renderWithRoute('/')

    // Budget should be active on root path
    const budgetLink = getNavLink('Budget')
    expect(budgetLink).toHaveAttribute('data-active', 'true')
  })

  it('highlights Budget as active on /budget path', () => {
    renderWithRoute('/budget')

    const budgetLink = getNavLink('Budget')
    expect(budgetLink).toHaveAttribute('data-active', 'true')
  })

  it('highlights Accounts as active on /accounts path', () => {
    renderWithRoute('/accounts')

    const accountsLink = getNavLink('Accounts')
    expect(accountsLink).toHaveAttribute('data-active', 'true')

    // Budget should not be active
    const budgetLink = getNavLink('Budget')
    expect(budgetLink).toHaveAttribute('data-active', 'false')
  })

  it('highlights Transactions as active on /transactions path', () => {
    renderWithRoute('/transactions')

    const transactionsLink = getNavLink('Transactions')
    expect(transactionsLink).toHaveAttribute('data-active', 'true')
  })

  it('only highlights one nav item at a time', () => {
    renderWithRoute('/accounts')

    const links = screen.getAllByRole('link')
    // Filter to only nav links (data-size="default"), not header link (data-size="lg")
    const navLinks = links.filter(
      (link) => link.getAttribute('data-size') === 'default'
    )
    const activeLinks = navLinks.filter(
      (link) => link.getAttribute('data-active') === 'true'
    )

    // Only one nav item should be active
    expect(activeLinks.length).toBe(1)
  })
})
