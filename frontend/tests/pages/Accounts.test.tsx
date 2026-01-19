/**
 * Unit tests for AccountsPage component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AccountsPage } from '@/pages/Accounts'
import type { Account } from '@/types/account'

// Mock the accountService
vi.mock('@/services/accountService', () => ({
  accountService: {
    list: vi.fn(),
    create: vi.fn(),
    retrySync: vi.fn(),
  },
}))

import { accountService } from '@/services/accountService'

const mockAccountService = vi.mocked(accountService)

// Helper to create account with overrides
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

const mockAccounts: Account[] = [
  createAccount({
    id: '123',
    name: 'Main Checking',
    account_type: 'CHECKING',
    balance: '1500.00',
  }),
  createAccount({
    id: '456',
    name: 'Emergency Fund',
    account_type: 'SAVINGS',
    balance: '5000.00',
  }),
]

describe('AccountsPage', () => {
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

    render(<AccountsPage />)

    expect(screen.getByRole('heading', { name: /accounts/i })).toBeInTheDocument()
  })

  it('should show loading state initially', () => {
    mockAccountService.list.mockImplementation(() => new Promise(() => {}))

    render(<AccountsPage />)

    // Skeleton loading shows animate-pulse class
    expect(document.querySelector('[class*="animate-pulse"]')).toBeInTheDocument()
  })

  it('should display accounts when loaded', async () => {
    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })

    render(<AccountsPage />)

    await waitFor(() => {
      expect(screen.getByText('Main Checking')).toBeInTheDocument()
    })

    expect(screen.getByText('Emergency Fund')).toBeInTheDocument()
    expect(screen.getByText('$1,500.00')).toBeInTheDocument()
    expect(screen.getByText('$5,000.00')).toBeInTheDocument()
  })

  it('should show empty state when no accounts', async () => {
    mockAccountService.list.mockResolvedValueOnce({
      accounts: [],
      total: 0,
    })

    render(<AccountsPage />)

    await waitFor(() => {
      expect(screen.getByText(/no accounts yet/i)).toBeInTheDocument()
    })
  })

  it('should show error state and retry button on error', async () => {
    mockAccountService.list.mockRejectedValueOnce(new Error('Network error'))

    render(<AccountsPage />)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  it('should show "New Account" button', async () => {
    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })

    render(<AccountsPage />)

    expect(screen.getByRole('button', { name: /new account/i })).toBeInTheDocument()
  })

  it('should show create account form when "New Account" is clicked', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })

    render(<AccountsPage />)

    const newAccountButton = screen.getByRole('button', { name: /new account/i })
    await user.click(newAccountButton)

    // Wait for the form to appear by checking for a form-specific element
    await waitFor(() => {
      expect(screen.getByLabelText(/account name/i)).toBeInTheDocument()
    })

    // Form elements should be visible
    expect(screen.getByLabelText(/account type/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/initial balance/i)).toBeInTheDocument()
  })

  it('should hide "New Account" button when form is open', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })

    render(<AccountsPage />)

    const newAccountButton = screen.getByRole('button', { name: /new account/i })
    await user.click(newAccountButton)

    await waitFor(() => {
      expect(screen.getByLabelText(/account name/i)).toBeInTheDocument()
    })

    // The "New Account" button should not be visible when form is open
    expect(screen.queryByRole('button', { name: /new account/i })).not.toBeInTheDocument()
  })

  it('should close form when Cancel is clicked', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })

    render(<AccountsPage />)

    // Open form
    const newAccountButton = screen.getByRole('button', { name: /new account/i })
    await user.click(newAccountButton)

    await waitFor(() => {
      expect(screen.getByLabelText(/account name/i)).toBeInTheDocument()
    })

    // Click cancel
    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelButton)

    // Form should be hidden - look for form-specific element
    await waitFor(() => {
      expect(screen.queryByLabelText(/account name/i)).not.toBeInTheDocument()
    })

    // New Account button should be visible again
    expect(screen.getByRole('button', { name: /new account/i })).toBeInTheDocument()
  })

  it('should show error when submitting empty form', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })

    render(<AccountsPage />)

    // Open form
    const newAccountButton = screen.getByRole('button', { name: /new account/i })
    await user.click(newAccountButton)

    await waitFor(() => {
      expect(screen.getByLabelText(/account name/i)).toBeInTheDocument()
    })

    // Submit without filling form - get all buttons and find the submit button
    const buttons = screen.getAllByRole('button')
    const submitButton = buttons.find(btn => btn.textContent === 'Create Account')
    expect(submitButton).toBeTruthy()
    await user.click(submitButton!)

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/account name is required/i)).toBeInTheDocument()
    })
  })

  it('should show error when submitting without initial balance', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })

    render(<AccountsPage />)

    // Open form
    const newAccountButton = screen.getByRole('button', { name: /new account/i })
    await user.click(newAccountButton)

    await waitFor(() => {
      expect(screen.getByLabelText(/account name/i)).toBeInTheDocument()
    })

    // Fill name but not balance
    const nameInput = screen.getByLabelText(/account name/i)
    await user.type(nameInput, 'Test Account')

    // Submit - get all buttons and find the submit button
    const buttons = screen.getAllByRole('button')
    const submitButton = buttons.find(btn => btn.textContent === 'Create Account')
    expect(submitButton).toBeTruthy()
    await user.click(submitButton!)

    // Should show validation error for balance
    await waitFor(() => {
      expect(screen.getByText(/initial balance is required/i)).toBeInTheDocument()
    })
  })

  it('should create account and reset form on success', async () => {
    const user = userEvent.setup()

    const newAccount = createAccount({
      id: '789',
      name: 'Test Account',
      account_type: 'CHECKING',
      balance: '100.00',
      initial_balance: '100.00',
    })

    mockAccountService.list.mockResolvedValue({
      accounts: mockAccounts,
      total: 2,
    })

    mockAccountService.create.mockResolvedValueOnce(newAccount)

    render(<AccountsPage />)

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Main Checking')).toBeInTheDocument()
    })

    // Open form
    const newAccountButton = screen.getByRole('button', { name: /new account/i })
    await user.click(newAccountButton)

    await waitFor(() => {
      expect(screen.getByLabelText(/account name/i)).toBeInTheDocument()
    })

    // Fill form
    const nameInput = screen.getByLabelText(/account name/i)
    const balanceInput = screen.getByLabelText(/initial balance/i)

    await user.type(nameInput, 'Test Account')
    await user.type(balanceInput, '100.00')

    // Submit - get all buttons and find the submit button
    const buttons = screen.getAllByRole('button')
    const submitButton = buttons.find(btn => btn.textContent === 'Create Account')
    expect(submitButton).toBeTruthy()
    await user.click(submitButton!)

    // Form should be closed - check for form-specific element
    await waitFor(() => {
      expect(screen.queryByLabelText(/account name/i)).not.toBeInTheDocument()
    })

    // accountService.create should have been called
    // Note: number input may trim trailing zeros, so we check for either format
    expect(mockAccountService.create).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Test Account',
        account_type: 'CHECKING',
      })
    )
    // Verify the initial_balance was passed (number input may format differently)
    const callArgs = mockAccountService.create.mock.calls[0]?.[0]
    expect(parseFloat(callArgs?.initial_balance ?? '0')).toBe(100)
  })

  it('should show error when create fails', async () => {
    const user = userEvent.setup()

    mockAccountService.list.mockResolvedValue({
      accounts: mockAccounts,
      total: 2,
    })

    mockAccountService.create.mockRejectedValueOnce(new Error('Creation failed'))

    render(<AccountsPage />)

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Main Checking')).toBeInTheDocument()
    })

    // Open form
    const newAccountButton = screen.getByRole('button', { name: /new account/i })
    await user.click(newAccountButton)

    await waitFor(() => {
      expect(screen.getByLabelText(/account name/i)).toBeInTheDocument()
    })

    // Fill form
    const nameInput = screen.getByLabelText(/account name/i)
    const balanceInput = screen.getByLabelText(/initial balance/i)

    await user.type(nameInput, 'Test Account')
    await user.type(balanceInput, '100.00')

    // Submit - get all buttons and find the submit button
    const buttons2 = screen.getAllByRole('button')
    const submitButton2 = buttons2.find(btn => btn.textContent === 'Create Account')
    expect(submitButton2).toBeTruthy()
    await user.click(submitButton2!)

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/creation failed/i)).toBeInTheDocument()
    })

    // Form should still be open - check for form-specific element
    expect(screen.getByLabelText(/account name/i)).toBeInTheDocument()
  })

  it('should display total balance', async () => {
    mockAccountService.list.mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })

    render(<AccountsPage />)

    await waitFor(() => {
      expect(screen.getByText('Main Checking')).toBeInTheDocument()
    })

    // Total should be $6,500 (1500 + 5000)
    expect(screen.getByText('$6,500.00')).toBeInTheDocument()
  })
})
