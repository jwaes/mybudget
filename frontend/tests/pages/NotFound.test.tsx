/**
 * Unit tests for NotFound page component.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { NotFound } from '@/pages/NotFound'

// Helper to render NotFound with router context
function renderWithRouter() {
  return render(
    <MemoryRouter>
      <NotFound />
    </MemoryRouter>
  )
}

describe('NotFound', () => {
  it('should render 404 heading', () => {
    renderWithRouter()

    expect(screen.getByText('404')).toBeInTheDocument()
  })

  it('should render Page Not Found message', () => {
    renderWithRouter()

    expect(screen.getByText('Page Not Found')).toBeInTheDocument()
  })

  it('should render descriptive message', () => {
    renderWithRouter()

    expect(
      screen.getByText(
        "The page you're looking for doesn't exist or has been moved."
      )
    ).toBeInTheDocument()
  })

  it('should have a link to the home/budget page', () => {
    renderWithRouter()

    const budgetLink = screen.getByRole('link', { name: 'Go to Budget' })
    expect(budgetLink).toBeInTheDocument()
    expect(budgetLink).toHaveAttribute('href', '/')
  })

  it('should have a link to the accounts page', () => {
    renderWithRouter()

    const accountsLink = screen.getByRole('link', { name: 'View Accounts' })
    expect(accountsLink).toBeInTheDocument()
    expect(accountsLink).toHaveAttribute('href', '/accounts')
  })

  it('should render both navigation buttons', () => {
    renderWithRouter()

    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(2)
  })

  it('should display 404 in a prominent way', () => {
    renderWithRouter()

    const heading = screen.getByText('404')
    // Check that it has the large font styling class
    expect(heading).toHaveClass('text-6xl')
  })

  it('should be centered on the page', () => {
    renderWithRouter()

    // The container should have centering classes
    const container = screen.getByText('404').closest('div.min-h-screen')
    expect(container).toHaveClass('flex', 'items-center', 'justify-center')
  })
})
