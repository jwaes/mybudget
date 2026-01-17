/**
 * Unit tests for TransactionInbox component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TransactionInbox } from '@/components/TransactionInbox'

// Mock the services
vi.mock('@/services/transactionService', () => ({
  transactionService: {
    listInbox: vi.fn(),
    approve: vi.fn(),
  },
}))

vi.mock('@/services/categoryService', () => ({
  categoryService: {
    list: vi.fn(),
  },
}))

import { transactionService } from '@/services/transactionService'
import { categoryService } from '@/services/categoryService'

const mockTransactions = [
  {
    id: 'tx-1',
    user_id: 'user-1',
    account_id: 'account-1',
    category_id: null,
    date: '2026-01-15',
    payee: 'Grocery Store',
    amount: '-50.00',
    memo: 'Weekly groceries',
    state: 'INBOX' as const,
    created_at: '2026-01-15T10:00:00Z',
    updated_at: '2026-01-15T10:00:00Z',
    approved_at: null,
    cleared_at: null,
  },
  {
    id: 'tx-2',
    user_id: 'user-1',
    account_id: 'account-1',
    category_id: null,
    date: '2026-01-16',
    payee: 'Coffee Shop',
    amount: '-5.50',
    memo: null,
    state: 'INBOX' as const,
    created_at: '2026-01-16T08:00:00Z',
    updated_at: '2026-01-16T08:00:00Z',
    approved_at: null,
    cleared_at: null,
  },
]

const mockCategories = {
  groups: [
    {
      id: 'group-1',
      user_id: 'user-1',
      name: 'Daily Living',
      display_order: 0,
      categories: [
        {
          id: 'cat-1',
          user_id: 'user-1',
          group_id: 'group-1',
          name: 'Groceries',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
        {
          id: 'cat-2',
          user_id: 'user-1',
          group_id: 'group-1',
          name: 'Dining Out',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
  ],
  total_groups: 1,
  total_categories: 2,
}

describe('TransactionInbox', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should show loading state initially', () => {
    vi.mocked(transactionService.listInbox).mockImplementation(
      () => new Promise(() => {})
    )
    vi.mocked(categoryService.list).mockImplementation(
      () => new Promise(() => {})
    )

    render(<TransactionInbox />)

    // Skeleton loading shows animate-pulse class
    expect(document.querySelector('[class*="animate-pulse"]')).toBeInTheDocument()
  })

  it('should display transactions when loaded', async () => {
    vi.mocked(transactionService.listInbox).mockResolvedValueOnce({
      transactions: mockTransactions,
      total: 2,
    })
    vi.mocked(categoryService.list).mockResolvedValueOnce(mockCategories)

    render(<TransactionInbox />)

    await waitFor(() => {
      expect(screen.getByText('Grocery Store')).toBeInTheDocument()
    })

    expect(screen.getByText('Coffee Shop')).toBeInTheDocument()
    expect(screen.getByText('-$50.00')).toBeInTheDocument()
    expect(screen.getByText('-$5.50')).toBeInTheDocument()
  })

  it('should show empty state when no transactions', async () => {
    vi.mocked(transactionService.listInbox).mockResolvedValueOnce({
      transactions: [],
      total: 0,
    })
    vi.mocked(categoryService.list).mockResolvedValueOnce(mockCategories)

    render(<TransactionInbox />)

    await waitFor(() => {
      expect(screen.getByText(/no transactions in inbox/i)).toBeInTheDocument()
    })
  })

  it('should show error state on error', async () => {
    vi.mocked(transactionService.listInbox).mockRejectedValueOnce(
      new Error('Network error')
    )
    vi.mocked(categoryService.list).mockResolvedValueOnce(mockCategories)

    render(<TransactionInbox />)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  it('should display category dropdown as combobox', async () => {
    vi.mocked(transactionService.listInbox).mockResolvedValueOnce({
      transactions: mockTransactions,
      total: 2,
    })
    vi.mocked(categoryService.list).mockResolvedValueOnce(mockCategories)

    render(<TransactionInbox />)

    await waitFor(() => {
      expect(screen.getByText('Grocery Store')).toBeInTheDocument()
    })

    const categorySelects = screen.getAllByRole('combobox')
    expect(categorySelects).toHaveLength(2) // One per transaction
  })

  it('should disable approve button when no category selected', async () => {
    vi.mocked(transactionService.listInbox).mockResolvedValueOnce({
      transactions: mockTransactions,
      total: 2,
    })
    vi.mocked(categoryService.list).mockResolvedValueOnce(mockCategories)

    render(<TransactionInbox />)

    await waitFor(() => {
      expect(screen.getByText('Grocery Store')).toBeInTheDocument()
    })

    const approveButtons = screen.getAllByRole('button', { name: /approve/i })
    expect(approveButtons[0]).toBeDisabled()
  })

  it('should enable approve button when category is selected', async () => {
    const user = userEvent.setup()

    vi.mocked(transactionService.listInbox).mockResolvedValueOnce({
      transactions: mockTransactions,
      total: 2,
    })
    vi.mocked(categoryService.list).mockResolvedValueOnce(mockCategories)

    render(<TransactionInbox />)

    await waitFor(() => {
      expect(screen.getByText('Grocery Store')).toBeInTheDocument()
    })

    // Click the first category select trigger to open dropdown
    const categorySelects = screen.getAllByRole('combobox')
    await user.click(categorySelects[0])

    // Wait for dropdown to open and select an option
    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'Groceries' })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('option', { name: 'Groceries' }))

    const approveButtons = screen.getAllByRole('button', { name: /approve/i })
    expect(approveButtons[0]).not.toBeDisabled()
  })

  it('should approve transaction and remove from list', async () => {
    const user = userEvent.setup()
    const onTransactionApproved = vi.fn()

    const approvedTransaction = {
      ...mockTransactions[0],
      state: 'APPROVED' as const,
      category_id: 'cat-1',
      approved_at: '2026-01-17T12:00:00Z',
    }

    vi.mocked(transactionService.listInbox).mockResolvedValueOnce({
      transactions: mockTransactions,
      total: 2,
    })
    vi.mocked(categoryService.list).mockResolvedValueOnce(mockCategories)
    vi.mocked(transactionService.approve).mockResolvedValueOnce(approvedTransaction)

    render(<TransactionInbox onTransactionApproved={onTransactionApproved} />)

    await waitFor(() => {
      expect(screen.getByText('Grocery Store')).toBeInTheDocument()
    })

    // Click the first category select trigger to open dropdown
    const categorySelects = screen.getAllByRole('combobox')
    await user.click(categorySelects[0])

    // Wait for dropdown to open and select an option
    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'Groceries' })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('option', { name: 'Groceries' }))

    // Click approve
    const approveButtons = screen.getAllByRole('button', { name: /approve/i })
    await user.click(approveButtons[0])

    // Transaction should be removed from the list
    await waitFor(() => {
      expect(screen.queryByText('Grocery Store')).not.toBeInTheDocument()
    })

    // Coffee Shop should still be there
    expect(screen.getByText('Coffee Shop')).toBeInTheDocument()

    // Callback should be called
    expect(onTransactionApproved).toHaveBeenCalledWith(approvedTransaction)
  })

  it('should filter by account_id when provided', async () => {
    vi.mocked(transactionService.listInbox).mockResolvedValueOnce({
      transactions: mockTransactions,
      total: 2,
    })
    vi.mocked(categoryService.list).mockResolvedValueOnce(mockCategories)

    render(<TransactionInbox accountId="account-123" />)

    await waitFor(() => {
      expect(screen.getByText('Grocery Store')).toBeInTheDocument()
    })

    expect(transactionService.listInbox).toHaveBeenCalledWith({
      account_id: 'account-123',
    })
  })

  it('should display transaction memo when present', async () => {
    vi.mocked(transactionService.listInbox).mockResolvedValueOnce({
      transactions: mockTransactions,
      total: 2,
    })
    vi.mocked(categoryService.list).mockResolvedValueOnce(mockCategories)

    render(<TransactionInbox />)

    await waitFor(() => {
      expect(screen.getByText('Weekly groceries')).toBeInTheDocument()
    })
  })

  it('should display inbox count in header', async () => {
    vi.mocked(transactionService.listInbox).mockResolvedValueOnce({
      transactions: mockTransactions,
      total: 2,
    })
    vi.mocked(categoryService.list).mockResolvedValueOnce(mockCategories)

    render(<TransactionInbox />)

    await waitFor(() => {
      expect(screen.getByText('Inbox (2)')).toBeInTheDocument()
    })
  })
})
