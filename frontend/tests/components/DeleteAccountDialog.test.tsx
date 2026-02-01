/**
 * Unit tests for DeleteAccountDialog component.
 *
 * Tests account deletion confirmation dialog functionality.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DeleteAccountDialog } from '@/components/DeleteAccountDialog'

// Mock the accountService
vi.mock('@/services/accountService', () => ({
  accountService: {
    delete: vi.fn(),
  },
}))

import { accountService } from '@/services/accountService'

const mockAccountService = vi.mocked(accountService)

describe('DeleteAccountDialog', () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
    account: {
      id: 'acc-123',
      name: 'Checking Account',
    },
    onDeleted: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockAccountService.delete.mockResolvedValue(undefined)
  })

  it('renders dialog with account name', () => {
    render(<DeleteAccountDialog {...defaultProps} />)

    expect(screen.getByRole('alertdialog')).toBeInTheDocument()
    expect(screen.getByText(/Delete Checking Account/i)).toBeInTheDocument()
  })

  it('shows deletion warning message', () => {
    render(<DeleteAccountDialog {...defaultProps} />)

    expect(screen.getByText(/permanently deleted/i)).toBeInTheDocument()
  })

  it('calls onOpenChange with false when Cancel is clicked', async () => {
    const user = userEvent.setup()
    render(<DeleteAccountDialog {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: /cancel/i }))

    expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false)
  })

  it('calls accountService.delete and onDeleted when Delete is clicked', async () => {
    const user = userEvent.setup()
    render(<DeleteAccountDialog {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: /^delete$/i }))

    await waitFor(() => {
      expect(mockAccountService.delete).toHaveBeenCalledWith('acc-123')
      expect(defaultProps.onDeleted).toHaveBeenCalled()
      expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false)
    })
  })

  it('shows loading state during deletion', async () => {
    // Make delete take some time
    mockAccountService.delete.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    )

    const user = userEvent.setup()
    render(<DeleteAccountDialog {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: /^delete$/i }))

    expect(screen.getByText(/deleting/i)).toBeInTheDocument()
  })

  it('shows error message when deletion fails', async () => {
    mockAccountService.delete.mockRejectedValue(new Error('Network error'))

    const user = userEvent.setup()
    render(<DeleteAccountDialog {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: /^delete$/i }))

    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument()
    })

    // Dialog should remain open
    expect(defaultProps.onOpenChange).not.toHaveBeenCalled()
  })

  it('disables Cancel button while deleting', async () => {
    mockAccountService.delete.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    )

    const user = userEvent.setup()
    render(<DeleteAccountDialog {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: /^delete$/i }))

    expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled()
  })

  it('does not render when open is false', () => {
    render(<DeleteAccountDialog {...defaultProps} open={false} />)

    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
  })
})

describe('DeleteAccountDialog - Bank-connected accounts', () => {
  const bankConnectedProps = {
    open: true,
    onOpenChange: vi.fn(),
    account: {
      id: 'acc-456',
      name: 'ING Savings',
      bank_connection_id: 'conn-789',
    },
    onDeleted: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockAccountService.delete.mockResolvedValue(undefined)
  })

  it('shows bank unlink warning for bank-connected accounts', () => {
    render(<DeleteAccountDialog {...bankConnectedProps} />)

    expect(screen.getByText(/unlink/i)).toBeInTheDocument()
  })

  it('explains bank connection will be preserved', () => {
    render(<DeleteAccountDialog {...bankConnectedProps} />)

    expect(screen.getByText(/preserved for other accounts/i)).toBeInTheDocument()
  })
})
