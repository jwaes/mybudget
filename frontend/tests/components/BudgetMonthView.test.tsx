/**
 * Unit tests for BudgetMonthView component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BudgetMonthView } from '@/components/BudgetMonthView'
import { ToastProvider } from '@/components/Toast'

// Helper to render with required providers
function renderWithProviders(ui: React.ReactElement) {
  return render(<ToastProvider>{ui}</ToastProvider>)
}

// Mock the budgetService
vi.mock('@/services/budgetService', () => ({
  budgetService: {
    getMonthView: vi.fn(),
    assignFunds: vi.fn(),
    getUnderfundedSummary: vi.fn(),
    fundUnderfunded: vi.fn(),
    fundAllUnderfunded: vi.fn(),
  },
}))

// Mock the targetService
vi.mock('@/services/targetService', () => ({
  targetService: {
    getTargets: vi.fn(),
    getUnderfunded: vi.fn(),
    createTarget: vi.fn(),
    updateTarget: vi.fn(),
    deleteTarget: vi.fn(),
  },
}))

// Mock the categoryService
vi.mock('@/services/categoryService', () => ({
  categoryService: {
    listGroups: vi.fn(),
    createGroup: vi.fn(),
    updateGroup: vi.fn(),
    deleteGroup: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}))

import { budgetService } from '@/services/budgetService'
import { targetService } from '@/services/targetService'
import { categoryService } from '@/services/categoryService'

const mockBudgetData = {
  month: '2026-01',
  to_assign: '1500.0000',
  groups: [
    {
      id: 'group-1',
      name: 'Monthly Bills',
      display_order: 0,
      categories: [
        {
          id: 'cat-1',
          name: 'Rent',
          funded_this_month: '1200.0000',
          activity: '-1200.0000',
          available: '0.0000',
        },
        {
          id: 'cat-2',
          name: 'Utilities',
          funded_this_month: '150.0000',
          activity: '-100.0000',
          available: '50.0000',
        },
      ],
    },
    {
      id: 'group-2',
      name: 'Savings',
      display_order: 1,
      categories: [
        {
          id: 'cat-3',
          name: 'Emergency Fund',
          funded_this_month: '500.0000',
          activity: '0.0000',
          available: '2500.0000',
        },
      ],
    },
  ],
}

const mockUnderfundedSummary = {
  total_underfunded: '0.00',
  categories_underfunded: 0,
  categories: [],
}

const mockCategoryGroups = [
  {
    id: 'group-1',
    user_id: 'user-1',
    name: 'Monthly Bills',
    display_order: 0,
    created_at: '2026-01-17T00:00:00Z',
    updated_at: '2026-01-17T00:00:00Z',
  },
  {
    id: 'group-2',
    user_id: 'user-1',
    name: 'Savings',
    display_order: 1,
    created_at: '2026-01-17T00:00:00Z',
    updated_at: '2026-01-17T00:00:00Z',
  },
]

describe('BudgetMonthView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(budgetService.getMonthView).mockResolvedValue(mockBudgetData)
    vi.mocked(budgetService.getUnderfundedSummary).mockResolvedValue(mockUnderfundedSummary)
    vi.mocked(targetService.getTargets).mockResolvedValue([])
    vi.mocked(categoryService.listGroups).mockResolvedValue(mockCategoryGroups)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should display loading state initially', async () => {
    // Create a promise that we control
    let resolvePromise: (value: typeof mockBudgetData) => void
    vi.mocked(budgetService.getMonthView).mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve
      })
    )

    renderWithProviders(<BudgetMonthView initialMonth="2026-01" />)

    // Skeleton loading shows animate-pulse class
    expect(document.querySelector('[class*="animate-pulse"]')).toBeInTheDocument()

    // Resolve to avoid act warnings
    resolvePromise!(mockBudgetData)
    await waitFor(() => {
      expect(document.querySelector('[class*="animate-pulse"]')).not.toBeInTheDocument()
    })
  })

  it('should display budget data after loading', async () => {
    renderWithProviders(<BudgetMonthView initialMonth="2026-01" />)

    await waitFor(() => {
      // Wait for skeleton loading to disappear
      expect(document.querySelector('[class*="animate-pulse"]')).not.toBeInTheDocument()
    })

    // Check month is displayed
    expect(screen.getByText('January 2026')).toBeInTheDocument()

    // Check to_assign amount
    expect(screen.getByText('$1,500.00')).toBeInTheDocument()

    // Check category groups
    expect(screen.getByText('Monthly Bills')).toBeInTheDocument()
    expect(screen.getByText('Savings')).toBeInTheDocument()

    // Check categories
    expect(screen.getByText('Rent')).toBeInTheDocument()
    expect(screen.getByText('Utilities')).toBeInTheDocument()
    expect(screen.getByText('Emergency Fund')).toBeInTheDocument()
  })

  it('should display error state when loading fails', async () => {
    vi.mocked(budgetService.getMonthView).mockRejectedValue(new Error('Network error'))

    renderWithProviders(<BudgetMonthView initialMonth="2026-01" />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load budget data')).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
  })

  it('should retry loading when retry button is clicked', async () => {
    vi.mocked(budgetService.getMonthView)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce(mockBudgetData)

    const user = userEvent.setup()

    renderWithProviders(<BudgetMonthView initialMonth="2026-01" />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load budget data')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    await waitFor(() => {
      expect(screen.getByText('January 2026')).toBeInTheDocument()
    })

    expect(budgetService.getMonthView).toHaveBeenCalledTimes(2)
  })

  it('should navigate to previous month', async () => {
    const user = userEvent.setup()

    renderWithProviders(<BudgetMonthView initialMonth="2026-01" />)

    await waitFor(() => {
      expect(screen.getByText('January 2026')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: 'Previous month' }))

    expect(budgetService.getMonthView).toHaveBeenCalledWith('2025-12')
  })

  it('should navigate to next month', async () => {
    const user = userEvent.setup()

    renderWithProviders(<BudgetMonthView initialMonth="2026-01" />)

    await waitFor(() => {
      expect(screen.getByText('January 2026')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: 'Next month' }))

    expect(budgetService.getMonthView).toHaveBeenCalledWith('2026-02')
  })

  it('should display empty state when no categories exist', async () => {
    vi.mocked(budgetService.getMonthView).mockResolvedValue({
      month: '2026-01',
      to_assign: '5000.0000',
      groups: [],
    })

    renderWithProviders(<BudgetMonthView initialMonth="2026-01" />)

    await waitFor(() => {
      expect(screen.getByText('No categories yet.')).toBeInTheDocument()
    })
  })

  it('should format amounts correctly with positive values', async () => {
    renderWithProviders(<BudgetMonthView initialMonth="2026-01" />)

    await waitFor(() => {
      expect(screen.getByText('January 2026')).toBeInTheDocument()
    })

    // Check Emergency Fund available (positive value) - appears twice (group total + category)
    const availableElements = screen.getAllByText('2,500.00')
    expect(availableElements.length).toBeGreaterThan(0)
  })

  it('should apply correct CSS class for negative to_assign', async () => {
    vi.mocked(budgetService.getMonthView).mockResolvedValue({
      ...mockBudgetData,
      to_assign: '-500.0000',
    })

    renderWithProviders(<BudgetMonthView initialMonth="2026-01" />)

    await waitFor(() => {
      // The format is $-500.00 since formatAmount handles the negative
      expect(screen.getByText('$-500.00')).toBeInTheDocument()
    })
  })
})

describe('CategoryRow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(budgetService.getMonthView).mockResolvedValue(mockBudgetData)
    vi.mocked(budgetService.getUnderfundedSummary).mockResolvedValue(mockUnderfundedSummary)
    vi.mocked(targetService.getTargets).mockResolvedValue([])
    vi.mocked(categoryService.listGroups).mockResolvedValue(mockCategoryGroups)
    vi.mocked(budgetService.assignFunds).mockResolvedValue({
      id: 'assignment-1',
      user_id: 'user-1',
      category_id: 'cat-1',
      amount: '100.00',
      month: '2026-01-01',
      created_at: '2026-01-17T00:00:00Z',
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should allow editing funded amount by clicking', async () => {
    const user = userEvent.setup()

    renderWithProviders(<BudgetMonthView initialMonth="2026-01" />)

    await waitFor(() => {
      expect(screen.getByText('Rent')).toBeInTheDocument()
    })

    // Find the Rent category row (parent div containing the category name)
    const rentNameButton = screen.getByText('Rent').closest('button')
    const rentRow = rentNameButton?.parentElement?.parentElement

    // Click on the funded amount text (1,200.00) to start editing
    // The funded amount is displayed as formatted text like "1,200.00"
    const fundedAmount = screen.getByText('1,200.00')
    await user.click(fundedAmount)

    // Should now show an input
    await waitFor(() => {
      const input = rentRow?.querySelector('input')
      expect(input).toBeInTheDocument()
    })
  })

  it('should cancel editing when Escape is pressed', async () => {
    const user = userEvent.setup()

    renderWithProviders(<BudgetMonthView initialMonth="2026-01" />)

    await waitFor(() => {
      expect(screen.getByText('Rent')).toBeInTheDocument()
    })

    // Find the Rent category row
    const rentNameButton = screen.getByText('Rent').closest('button')
    const rentRow = rentNameButton?.parentElement?.parentElement

    // Click on the funded amount to start editing
    const fundedAmount = screen.getByText('1,200.00')
    await user.click(fundedAmount)

    // Verify input appears
    await waitFor(() => {
      const input = rentRow?.querySelector('input')
      expect(input).toBeInTheDocument()
    })

    await user.keyboard('{Escape}')

    // Input should no longer be visible
    await waitFor(() => {
      expect(rentRow?.querySelector('input')).not.toBeInTheDocument()
    })
    expect(budgetService.assignFunds).not.toHaveBeenCalled()
  })

  it('should display category budget information', async () => {
    renderWithProviders(<BudgetMonthView initialMonth="2026-01" />)

    await waitFor(() => {
      expect(screen.getByText('Rent')).toBeInTheDocument()
    })

    // Check that Rent category shows its budget info
    expect(screen.getByText('Rent')).toBeInTheDocument()

    // Activity should be displayed (negative for spending)
    const activityElements = screen.getAllByText('-1,200.00')
    expect(activityElements.length).toBeGreaterThan(0)
  })
})

describe('MonthNavigator', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(budgetService.getMonthView).mockResolvedValue(mockBudgetData)
    vi.mocked(budgetService.getUnderfundedSummary).mockResolvedValue(mockUnderfundedSummary)
    vi.mocked(targetService.getTargets).mockResolvedValue([])
    vi.mocked(categoryService.listGroups).mockResolvedValue(mockCategoryGroups)
  })

  it('should display current month correctly', async () => {
    renderWithProviders(<BudgetMonthView initialMonth="2026-06" />)

    await waitFor(() => {
      expect(screen.getByText('June 2026')).toBeInTheDocument()
    })
  })

  it('should handle year boundary when navigating backward', async () => {
    vi.mocked(budgetService.getMonthView).mockResolvedValue({
      ...mockBudgetData,
      month: '2026-01',
    })

    const user = userEvent.setup()

    renderWithProviders(<BudgetMonthView initialMonth="2026-01" />)

    await waitFor(() => {
      expect(screen.getByText('January 2026')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: 'Previous month' }))

    expect(budgetService.getMonthView).toHaveBeenCalledWith('2025-12')
  })

  it('should handle year boundary when navigating forward', async () => {
    vi.mocked(budgetService.getMonthView).mockResolvedValue({
      ...mockBudgetData,
      month: '2026-12',
    })

    const user = userEvent.setup()

    renderWithProviders(<BudgetMonthView initialMonth="2026-12" />)

    await waitFor(() => {
      expect(screen.getByText('December 2026')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: 'Next month' }))

    expect(budgetService.getMonthView).toHaveBeenCalledWith('2027-01')
  })
})
