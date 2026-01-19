/**
 * Unit tests for BudgetPage component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BudgetPage } from '@/pages/Budget'
import { ToastProvider } from '@/components/Toast'
import type { BudgetMonthView, UnderfundedSummary } from '@/types/budget'
import type { CategoryTarget } from '@/types/target'
import type { CategoryGroup } from '@/types/category'

// Mock the services
vi.mock('@/services/budgetService', () => ({
  budgetService: {
    getMonthView: vi.fn(),
    getUnderfundedSummary: vi.fn(),
    assignFunds: vi.fn(),
    fundUnderfunded: vi.fn(),
    fundAllUnderfunded: vi.fn(),
  },
}))

vi.mock('@/services/targetService', () => ({
  targetService: {
    getTargets: vi.fn(),
    getUnderfunded: vi.fn(),
  },
}))

vi.mock('@/services/categoryService', () => ({
  categoryService: {
    listGroups: vi.fn(),
  },
}))

import { budgetService } from '@/services/budgetService'
import { targetService } from '@/services/targetService'
import { categoryService } from '@/services/categoryService'

const mockBudgetService = vi.mocked(budgetService)
const mockTargetService = vi.mocked(targetService)
const mockCategoryService = vi.mocked(categoryService)

// Helper to render with providers
function renderWithProviders(ui: React.ReactElement) {
  return render(<ToastProvider>{ui}</ToastProvider>)
}

// Mock data
const mockBudgetData: BudgetMonthView = {
  month: '2026-01',
  to_assign: '1000.00',
  groups: [
    {
      id: 'grp-1',
      name: 'Bills',
      display_order: 1,
      categories: [
        {
          id: 'cat-1',
          name: 'Rent',
          funded_this_month: '500.00',
          activity: '-500.00',
          available: '0.00',
        },
        {
          id: 'cat-2',
          name: 'Utilities',
          funded_this_month: '100.00',
          activity: '-75.00',
          available: '25.00',
        },
      ],
    },
    {
      id: 'grp-2',
      name: 'Expenses',
      display_order: 2,
      categories: [
        {
          id: 'cat-3',
          name: 'Groceries',
          funded_this_month: '300.00',
          activity: '-250.00',
          available: '50.00',
        },
      ],
    },
  ],
}

const mockUnderfundedSummary: UnderfundedSummary = {
  total_underfunded: '0.00',
  categories_underfunded: 0,
  categories: [],
}

const mockTargets: CategoryTarget[] = []

const mockCategoryGroups: CategoryGroup[] = [
  {
    id: 'grp-1',
    user_id: 'user-1',
    name: 'Bills',
    display_order: 1,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'grp-2',
    user_id: 'user-1',
    name: 'Expenses',
    display_order: 2,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
]

describe('BudgetPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should render page title', async () => {
    mockBudgetService.getMonthView.mockResolvedValue(mockBudgetData)
    mockBudgetService.getUnderfundedSummary.mockResolvedValue(mockUnderfundedSummary)
    mockTargetService.getTargets.mockResolvedValue(mockTargets)
    mockCategoryService.listGroups.mockResolvedValue(mockCategoryGroups)

    renderWithProviders(<BudgetPage />)

    expect(screen.getByRole('heading', { name: /budget/i })).toBeInTheDocument()
  })

  it('should show loading state initially', () => {
    // Create promises that never resolve
    mockBudgetService.getMonthView.mockImplementation(() => new Promise(() => {}))
    mockBudgetService.getUnderfundedSummary.mockImplementation(() => new Promise(() => {}))
    mockTargetService.getTargets.mockImplementation(() => new Promise(() => {}))
    mockCategoryService.listGroups.mockImplementation(() => new Promise(() => {}))

    renderWithProviders(<BudgetPage />)

    // Skeleton loading elements should be present (Skeleton uses animate-pulse)
    expect(document.querySelector('[class*="animate-pulse"]')).toBeInTheDocument()
  })

  it('should display budget data when loaded', async () => {
    mockBudgetService.getMonthView.mockResolvedValue(mockBudgetData)
    mockBudgetService.getUnderfundedSummary.mockResolvedValue(mockUnderfundedSummary)
    mockTargetService.getTargets.mockResolvedValue(mockTargets)
    mockCategoryService.listGroups.mockResolvedValue(mockCategoryGroups)

    renderWithProviders(<BudgetPage />)

    // Wait for data to load and display "To Assign" amount
    await waitFor(() => {
      expect(screen.getByText('$1,000.00')).toBeInTheDocument()
    })

    // Category groups should be displayed
    expect(screen.getByText('Bills')).toBeInTheDocument()
    expect(screen.getByText('Expenses')).toBeInTheDocument()

    // Categories should be displayed
    expect(screen.getByText('Rent')).toBeInTheDocument()
    expect(screen.getByText('Utilities')).toBeInTheDocument()
    expect(screen.getByText('Groceries')).toBeInTheDocument()
  })

  it('should display to_assign amount with correct formatting', async () => {
    mockBudgetService.getMonthView.mockResolvedValue(mockBudgetData)
    mockBudgetService.getUnderfundedSummary.mockResolvedValue(mockUnderfundedSummary)
    mockTargetService.getTargets.mockResolvedValue(mockTargets)
    mockCategoryService.listGroups.mockResolvedValue(mockCategoryGroups)

    renderWithProviders(<BudgetPage />)

    await waitFor(() => {
      // Check for "To Assign:" label
      expect(screen.getByText('To Assign:')).toBeInTheDocument()
    })

    // The to_assign value should be formatted as currency
    expect(screen.getByText('$1,000.00')).toBeInTheDocument()
  })

  it('should show error state and retry button on error', async () => {
    mockBudgetService.getMonthView.mockRejectedValue(new Error('Failed to load'))
    mockBudgetService.getUnderfundedSummary.mockRejectedValue(new Error('Failed to load'))
    mockTargetService.getTargets.mockRejectedValue(new Error('Failed to load'))
    mockCategoryService.listGroups.mockRejectedValue(new Error('Failed to load'))

    renderWithProviders(<BudgetPage />)

    await waitFor(() => {
      expect(screen.getByText(/failed to load budget data/i)).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  it('should retry loading when retry button is clicked', async () => {
    const user = userEvent.setup()

    // First call fails
    mockBudgetService.getMonthView.mockRejectedValueOnce(new Error('Network error'))
    mockBudgetService.getUnderfundedSummary.mockRejectedValueOnce(new Error('Network error'))
    mockTargetService.getTargets.mockRejectedValueOnce(new Error('Network error'))
    mockCategoryService.listGroups.mockRejectedValueOnce(new Error('Network error'))

    // Second call succeeds
    mockBudgetService.getMonthView.mockResolvedValueOnce(mockBudgetData)
    mockBudgetService.getUnderfundedSummary.mockResolvedValueOnce(mockUnderfundedSummary)
    mockTargetService.getTargets.mockResolvedValueOnce(mockTargets)
    mockCategoryService.listGroups.mockResolvedValueOnce(mockCategoryGroups)

    renderWithProviders(<BudgetPage />)

    // Wait for error state
    await waitFor(() => {
      expect(screen.getByText(/failed to load budget data/i)).toBeInTheDocument()
    })

    // Click retry
    const retryButton = screen.getByRole('button', { name: /retry/i })
    await user.click(retryButton)

    // Should show data after retry
    await waitFor(() => {
      expect(screen.getByText('$1,000.00')).toBeInTheDocument()
    })
  })

  it('should show empty state when no categories exist', async () => {
    const emptyBudgetData: BudgetMonthView = {
      month: '2026-01',
      to_assign: '5000.00',
      groups: [],
    }

    mockBudgetService.getMonthView.mockResolvedValue(emptyBudgetData)
    mockBudgetService.getUnderfundedSummary.mockResolvedValue(mockUnderfundedSummary)
    mockTargetService.getTargets.mockResolvedValue([])
    mockCategoryService.listGroups.mockResolvedValue([])

    renderWithProviders(<BudgetPage />)

    await waitFor(() => {
      expect(screen.getByText(/no categories yet/i)).toBeInTheDocument()
    })

    // Should have button to add category group
    expect(screen.getByRole('button', { name: /add category group/i })).toBeInTheDocument()
  })

  it('should show underfunded summary when categories are underfunded', async () => {
    const underfundedSummary: UnderfundedSummary = {
      total_underfunded: '250.00',
      categories_underfunded: 2,
      categories: [
        { category_id: 'cat-1', category_name: 'Rent', underfunded: '150.00' },
        { category_id: 'cat-2', category_name: 'Utilities', underfunded: '100.00' },
      ],
    }

    mockBudgetService.getMonthView.mockResolvedValue(mockBudgetData)
    mockBudgetService.getUnderfundedSummary.mockResolvedValue(underfundedSummary)
    mockTargetService.getTargets.mockResolvedValue(mockTargets)
    mockCategoryService.listGroups.mockResolvedValue(mockCategoryGroups)

    renderWithProviders(<BudgetPage />)

    await waitFor(() => {
      expect(screen.getByText('$250.00')).toBeInTheDocument()
    })

    // Fund Underfunded button should be visible
    expect(screen.getByRole('button', { name: /fund underfunded/i })).toBeInTheDocument()
  })

  it('should display column headers', async () => {
    mockBudgetService.getMonthView.mockResolvedValue(mockBudgetData)
    mockBudgetService.getUnderfundedSummary.mockResolvedValue(mockUnderfundedSummary)
    mockTargetService.getTargets.mockResolvedValue(mockTargets)
    mockCategoryService.listGroups.mockResolvedValue(mockCategoryGroups)

    renderWithProviders(<BudgetPage />)

    await waitFor(() => {
      expect(screen.getByText('Category')).toBeInTheDocument()
    })

    expect(screen.getByText('Funded')).toBeInTheDocument()
    expect(screen.getByText('Activity')).toBeInTheDocument()
    expect(screen.getByText('Available')).toBeInTheDocument()
  })

  it('should show negative to_assign in red', async () => {
    const negativeBudgetData: BudgetMonthView = {
      ...mockBudgetData,
      to_assign: '-500.00',
    }

    mockBudgetService.getMonthView.mockResolvedValue(negativeBudgetData)
    mockBudgetService.getUnderfundedSummary.mockResolvedValue(mockUnderfundedSummary)
    mockTargetService.getTargets.mockResolvedValue(mockTargets)
    mockCategoryService.listGroups.mockResolvedValue(mockCategoryGroups)

    renderWithProviders(<BudgetPage />)

    await waitFor(() => {
      const toAssignElement = document.querySelector('.to-assign-amount')
      expect(toAssignElement).toBeInTheDocument()
      expect(toAssignElement).toHaveClass('text-destructive')
    })
  })

  it('should show positive to_assign in green', async () => {
    mockBudgetService.getMonthView.mockResolvedValue(mockBudgetData)
    mockBudgetService.getUnderfundedSummary.mockResolvedValue(mockUnderfundedSummary)
    mockTargetService.getTargets.mockResolvedValue(mockTargets)
    mockCategoryService.listGroups.mockResolvedValue(mockCategoryGroups)

    renderWithProviders(<BudgetPage />)

    await waitFor(() => {
      const toAssignElement = document.querySelector('.to-assign-amount')
      expect(toAssignElement).toBeInTheDocument()
      expect(toAssignElement).toHaveClass('text-green-600')
    })
  })

  it('should call services on initial render', async () => {
    mockBudgetService.getMonthView.mockResolvedValue(mockBudgetData)
    mockBudgetService.getUnderfundedSummary.mockResolvedValue(mockUnderfundedSummary)
    mockTargetService.getTargets.mockResolvedValue(mockTargets)
    mockCategoryService.listGroups.mockResolvedValue(mockCategoryGroups)

    renderWithProviders(<BudgetPage />)

    await waitFor(() => {
      expect(mockBudgetService.getMonthView).toHaveBeenCalled()
      expect(mockBudgetService.getUnderfundedSummary).toHaveBeenCalled()
      expect(mockTargetService.getTargets).toHaveBeenCalled()
      expect(mockCategoryService.listGroups).toHaveBeenCalled()
    })
  })
})
