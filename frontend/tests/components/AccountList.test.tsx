/**
 * Unit tests for AccountList component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AccountList } from '@/components/AccountList'

// Mock the accountService
vi.mock('@/services/accountService', () => ({
  accountService: {
    list: vi.fn(),
  },
}))

import { accountService } from '@/services/accountService'

const mockAccounts = [
  {
    id: '123',
    user_id: 'user-1',
    name: 'Main Checking',
    account_type: 'CHECKING' as const,
    balance: '1500.00',
    initial_balance: '1000.00',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: '456',
    user_id: 'user-1',
    name: 'Emergency Fund',
    account_type: 'SAVINGS' as const,
    balance: '5000.00',
    initial_balance: '5000.00',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
]

describe('AccountList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should show loading state initially', () => {
    vi.mocked(accountService.list).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    render(<AccountList />)

    expect(screen.getByText(/loading accounts/i)).toBeInTheDocument()
  })

  it('should display accounts when loaded', async () => {
    vi.mocked(accountService.list).mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })

    render(<AccountList />)

    await waitFor(() => {
      expect(screen.getByText('Main Checking')).toBeInTheDocument()
    })

    expect(screen.getByText('Emergency Fund')).toBeInTheDocument()
    expect(screen.getByText('$1,500.00')).toBeInTheDocument()
    expect(screen.getByText('$5,000.00')).toBeInTheDocument()
  })

  it('should show empty state when no accounts', async () => {
    vi.mocked(accountService.list).mockResolvedValueOnce({
      accounts: [],
      total: 0,
    })

    render(<AccountList />)

    await waitFor(() => {
      expect(screen.getByText(/no accounts yet/i)).toBeInTheDocument()
    })
  })

  it('should show error state and retry button on error', async () => {
    vi.mocked(accountService.list).mockRejectedValueOnce(
      new Error('Network error')
    )

    render(<AccountList />)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  it('should retry loading when retry button is clicked', async () => {
    const user = userEvent.setup()

    vi.mocked(accountService.list)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        accounts: mockAccounts,
        total: 2,
      })

    render(<AccountList />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /retry/i }))

    await waitFor(() => {
      expect(screen.getByText('Main Checking')).toBeInTheDocument()
    })
  })

  it('should call onAccountSelect when account is clicked', async () => {
    const user = userEvent.setup()
    const onAccountSelect = vi.fn()

    vi.mocked(accountService.list).mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })

    render(<AccountList onAccountSelect={onAccountSelect} />)

    await waitFor(() => {
      expect(screen.getByText('Main Checking')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Main Checking'))

    expect(onAccountSelect).toHaveBeenCalledWith(mockAccounts[0])
  })

  it('should display correct account type labels', async () => {
    vi.mocked(accountService.list).mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })

    render(<AccountList />)

    await waitFor(() => {
      expect(screen.getByText('Main Checking')).toBeInTheDocument()
    })

    // Check account names and types are displayed
    expect(screen.getByText('Main Checking')).toBeInTheDocument()
    expect(screen.getByText('Emergency Fund')).toBeInTheDocument()
    // Type labels
    expect(screen.getByText('Checking')).toBeInTheDocument()
    expect(screen.getByText('Savings')).toBeInTheDocument()
  })

  it('should display total balance', async () => {
    vi.mocked(accountService.list).mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })

    render(<AccountList />)

    await waitFor(() => {
      expect(screen.getByText('Main Checking')).toBeInTheDocument()
    })

    // Total should be $6,500 (1500 + 5000)
    expect(screen.getByText('$6,500.00')).toBeInTheDocument()
  })

  it('should handle keyboard navigation', async () => {
    const user = userEvent.setup()
    const onAccountSelect = vi.fn()

    vi.mocked(accountService.list).mockResolvedValueOnce({
      accounts: mockAccounts,
      total: 2,
    })

    render(<AccountList onAccountSelect={onAccountSelect} />)

    await waitFor(() => {
      expect(screen.getByText('Main Checking')).toBeInTheDocument()
    })

    const checkingItem = screen.getByText('Main Checking').closest('li')
    checkingItem?.focus()
    await user.keyboard('{Enter}')

    expect(onAccountSelect).toHaveBeenCalledWith(mockAccounts[0])
  })
})
