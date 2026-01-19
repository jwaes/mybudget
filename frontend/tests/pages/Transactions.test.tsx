/**
 * Unit tests for TransactionsPage component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TransactionsPage } from '@/pages/Transactions'
import type { Account } from '@/types/account'
import type { Transaction } from '@/types/transaction'

// Mock the services
vi.mock('@/services/transactionService', () => ({
  transactionService: {
    list: vi.fn(),
    listInbox: vi.fn(),
    approve: vi.fn(),
    create: vi.fn(),
  },
}))

vi.mock('@/services/accountService', () => ({
  accountService: {
    list: vi.fn(),
  },
}))

vi.mock('@/services/categoryService', () => ({
  categoryService: {
    list: vi.fn(),
  },
}))

// Mock child components that have complex behavior
vi.mock('@/components/TransactionInbox', () => ({
  TransactionInbox: ({ accountId, onTransactionApproved }: { accountId?: string; onTransactionApproved?: () => void }) => (
    <div data-testid="transaction-inbox" data-account-id={accountId}>
      <button onClick={onTransactionApproved}>Mock Approve</button>
      Transaction Inbox Component
    </div>
  ),
}))

vi.mock('@/components/CSVImport', () => ({
  CSVImport: ({ accountId, onImportComplete }: { accountId: string; onImportComplete?: () => void }) => (
    <div data-testid="csv-import" data-account-id={accountId}>
      <button onClick={onImportComplete}>Mock Import</button>
      CSV Import Component
    </div>
  ),
}))

vi.mock('@/components/AddTransactionModal', () => ({
  AddTransactionModal: ({
    isOpen,
    onClose,
    onTransactionAdded,
    preselectedAccountId,
  }: {
    isOpen: boolean
    onClose: () => void
    onTransactionAdded?: () => void
    preselectedAccountId?: string
  }) => (
    isOpen ? (
      <div data-testid="add-transaction-modal" data-account-id={preselectedAccountId}>
        <button onClick={onClose}>Close Modal</button>
        <button onClick={onTransactionAdded}>Mock Add Transaction</button>
        Add Transaction Modal
      </div>
    ) : null
  ),
}))

vi.mock('@/components/TransactionSearch', () => ({
  TransactionSearch: ({ value, onChange }: { value: string; onChange: (val: string) => void }) => (
    <input
      data-testid="transaction-search"
      type="text"
      placeholder="Search transactions..."
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  ),
}))

vi.mock('@/components/TransactionFilters', () => ({
  TransactionFilters: () => (
    <div data-testid="transaction-filters">Mock Filters</div>
  ),
}))

import { transactionService } from '@/services/transactionService'
import { accountService } from '@/services/accountService'
import { categoryService } from '@/services/categoryService'

const mockTransactionService = vi.mocked(transactionService)
const mockAccountService = vi.mocked(accountService)
const mockCategoryService = vi.mocked(categoryService)

// Helper functions
function createAccount(overrides: Partial<Account> = {}): Account {
  return {
    id: '123',
    user_id: 'user-1',
    name: 'Main Checking',
    account_type: 'CHECKING',
    balance: '1500.00',
    initial_balance: '1000.00',
    sync_status: 'SUCCESS',
    last_sync_at: '2026-01-18T10:00:00Z',
    sync_error: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function createTransaction(overrides: Partial<Transaction> = {}): Transaction {
  return {
    id: 'tx-1',
    user_id: 'user-1',
    account_id: 'account-1',
    category_id: null,
    date: '2026-01-15',
    payee: 'Grocery Store',
    amount: '-50.00',
    memo: 'Weekly groceries',
    state: 'APPROVED',
    created_at: '2026-01-15T10:00:00Z',
    updated_at: '2026-01-15T10:00:00Z',
    approved_at: '2026-01-15T10:00:00Z',
    cleared_at: null,
    ...overrides,
  }
}

const mockAccounts: Account[] = [
  createAccount({ id: '123', name: 'Main Checking' }),
  createAccount({ id: '456', name: 'Savings Account', account_type: 'SAVINGS' }),
]

const mockTransactions: Transaction[] = [
  createTransaction({
    id: 'tx-1',
    payee: 'Grocery Store',
    amount: '-50.00',
    state: 'APPROVED',
    date: '2026-01-15',
    memo: 'Weekly groceries',
  }),
  createTransaction({
    id: 'tx-2',
    payee: 'Coffee Shop',
    amount: '-5.50',
    state: 'CLEARED',
    date: '2026-01-16',
    memo: null,
  }),
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
      ],
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
  ],
  total_groups: 1,
  total_categories: 1,
}

describe('TransactionsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should render page title', async () => {
    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)
    mockTransactionService.list.mockResolvedValueOnce({
      transactions: [],
      total: 0,
    })

    render(<TransactionsPage />)

    expect(screen.getByRole('heading', { name: /transactions/i })).toBeInTheDocument()
  })

  it('should show Add Transaction button', async () => {
    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)

    render(<TransactionsPage />)

    expect(screen.getByRole('button', { name: /add transaction/i })).toBeInTheDocument()
  })

  it('should show account selector', async () => {
    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)

    render(<TransactionsPage />)

    await waitFor(() => {
      expect(screen.getByText('Account:')).toBeInTheDocument()
    })

    // The account selector combobox should be present
    const accountSelector = screen.getByRole('combobox')
    expect(accountSelector).toBeInTheDocument()
  })

  it('should show Inbox tab by default', async () => {
    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)

    render(<TransactionsPage />)

    await waitFor(() => {
      expect(screen.getByTestId('transaction-inbox')).toBeInTheDocument()
    })
  })

  it('should show Inbox and All Transactions tab buttons', async () => {
    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)

    render(<TransactionsPage />)

    expect(screen.getByRole('button', { name: 'Inbox' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'All Transactions' })).toBeInTheDocument()
  })

  it('should switch to All Transactions tab when clicked', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)
    mockTransactionService.list.mockResolvedValue({
      transactions: mockTransactions,
      total: 2,
    })

    render(<TransactionsPage />)

    const allTransactionsButton = screen.getByRole('button', { name: 'All Transactions' })
    await user.click(allTransactionsButton)

    // Should show transactions table instead of inbox
    await waitFor(() => {
      expect(screen.queryByTestId('transaction-inbox')).not.toBeInTheDocument()
    })
  })

  it('should show loading state when loading transactions', async () => {
    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)
    mockTransactionService.list.mockImplementation(() => new Promise(() => {}))

    const user = userEvent.setup()

    render(<TransactionsPage />)

    const allTransactionsButton = screen.getByRole('button', { name: 'All Transactions' })
    await user.click(allTransactionsButton)

    // Skeleton loading shows animate-pulse class
    await waitFor(() => {
      expect(document.querySelector('[class*="animate-pulse"]')).toBeInTheDocument()
    })
  })

  it('should display transactions when loaded on All tab', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)
    mockTransactionService.list.mockResolvedValue({
      transactions: mockTransactions,
      total: 2,
    })

    render(<TransactionsPage />)

    const allTransactionsButton = screen.getByRole('button', { name: 'All Transactions' })
    await user.click(allTransactionsButton)

    await waitFor(() => {
      expect(screen.getByText('Grocery Store')).toBeInTheDocument()
    })

    expect(screen.getByText('Coffee Shop')).toBeInTheDocument()
    expect(screen.getByText('-$50.00')).toBeInTheDocument()
    expect(screen.getByText('-$5.50')).toBeInTheDocument()
  })

  it('should show empty state when no transactions', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)
    mockTransactionService.list.mockResolvedValue({
      transactions: [],
      total: 0,
    })

    render(<TransactionsPage />)

    const allTransactionsButton = screen.getByRole('button', { name: 'All Transactions' })
    await user.click(allTransactionsButton)

    await waitFor(() => {
      expect(screen.getByText(/no transactions found/i)).toBeInTheDocument()
    })
  })

  it('should show error state on API error', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)
    mockTransactionService.list.mockRejectedValue(new Error('Network error'))

    render(<TransactionsPage />)

    const allTransactionsButton = screen.getByRole('button', { name: 'All Transactions' })
    await user.click(allTransactionsButton)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  it('should retry loading when retry button is clicked', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)
    mockTransactionService.list
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValue({
        transactions: mockTransactions,
        total: 2,
      })

    render(<TransactionsPage />)

    const allTransactionsButton = screen.getByRole('button', { name: 'All Transactions' })
    await user.click(allTransactionsButton)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    })

    const retryButton = screen.getByRole('button', { name: /retry/i })
    await user.click(retryButton)

    await waitFor(() => {
      expect(screen.getByText('Grocery Store')).toBeInTheDocument()
    })
  })

  it('should open Add Transaction modal when button is clicked', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)

    render(<TransactionsPage />)

    const addButton = screen.getByRole('button', { name: /add transaction/i })
    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByTestId('add-transaction-modal')).toBeInTheDocument()
    })
  })

  it('should close Add Transaction modal when close is clicked', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)

    render(<TransactionsPage />)

    const addButton = screen.getByRole('button', { name: /add transaction/i })
    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByTestId('add-transaction-modal')).toBeInTheDocument()
    })

    const closeButton = screen.getByRole('button', { name: /close modal/i })
    await user.click(closeButton)

    await waitFor(() => {
      expect(screen.queryByTestId('add-transaction-modal')).not.toBeInTheDocument()
    })
  })

  it('should show CSV import when account is selected', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)

    render(<TransactionsPage />)

    // Select an account
    const accountSelector = screen.getByRole('combobox')
    await user.click(accountSelector)

    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'Main Checking' })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('option', { name: 'Main Checking' }))

    await waitFor(() => {
      expect(screen.getByTestId('csv-import')).toBeInTheDocument()
    })
  })

  it('should display transaction memo when present', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)
    mockTransactionService.list.mockResolvedValue({
      transactions: mockTransactions,
      total: 2,
    })

    render(<TransactionsPage />)

    const allTransactionsButton = screen.getByRole('button', { name: 'All Transactions' })
    await user.click(allTransactionsButton)

    await waitFor(() => {
      expect(screen.getByText('Weekly groceries')).toBeInTheDocument()
    })
  })

  it('should display transaction state badges', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)
    mockTransactionService.list.mockResolvedValue({
      transactions: mockTransactions,
      total: 2,
    })

    render(<TransactionsPage />)

    const allTransactionsButton = screen.getByRole('button', { name: 'All Transactions' })
    await user.click(allTransactionsButton)

    await waitFor(() => {
      expect(screen.getByText('Approved')).toBeInTheDocument()
    })

    expect(screen.getByText('Cleared')).toBeInTheDocument()
  })

  it('should format dates correctly', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)
    mockTransactionService.list.mockResolvedValue({
      transactions: mockTransactions,
      total: 2,
    })

    render(<TransactionsPage />)

    const allTransactionsButton = screen.getByRole('button', { name: 'All Transactions' })
    await user.click(allTransactionsButton)

    await waitFor(() => {
      // Jan 15, 2026 format
      expect(screen.getByText('Jan 15, 2026')).toBeInTheDocument()
    })

    expect(screen.getByText('Jan 16, 2026')).toBeInTheDocument()
  })

  it('should handle initial data loading error gracefully', async () => {
    mockAccountService.list.mockRejectedValueOnce(new Error('Failed to load accounts'))
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)

    render(<TransactionsPage />)

    // Page should still render even if initial data loading fails
    expect(screen.getByRole('heading', { name: /transactions/i })).toBeInTheDocument()
  })

  it('should have search component', async () => {
    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)

    render(<TransactionsPage />)

    // Search input should be present
    const searchInput = screen.getByPlaceholderText(/search/i)
    expect(searchInput).toBeInTheDocument()
  })

  it('should switch back to Inbox tab', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })
    mockCategoryService.list.mockResolvedValueOnce(mockCategories)
    mockTransactionService.list.mockResolvedValue({
      transactions: mockTransactions,
      total: 2,
    })

    render(<TransactionsPage />)

    // Switch to All Transactions
    const allTransactionsButton = screen.getByRole('button', { name: 'All Transactions' })
    await user.click(allTransactionsButton)

    await waitFor(() => {
      expect(screen.queryByTestId('transaction-inbox')).not.toBeInTheDocument()
    })

    // Switch back to Inbox
    const inboxButton = screen.getByRole('button', { name: 'Inbox' })
    await user.click(inboxButton)

    await waitFor(() => {
      expect(screen.getByTestId('transaction-inbox')).toBeInTheDocument()
    })
  })
})
