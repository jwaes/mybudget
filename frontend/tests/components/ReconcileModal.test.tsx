/**
 * Unit tests for ReconcileModal component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ReconcileModal } from '@/components/ReconcileModal'

// Mock the services
vi.mock('@/services/reconciliationService', () => ({
  reconciliationService: {
    start: vi.fn(),
    get: vi.fn(),
    markCleared: vi.fn(),
    unmarkCleared: vi.fn(),
    createAdjustment: vi.fn(),
    complete: vi.fn(),
    cancel: vi.fn(),
  },
}))

vi.mock('@/services/transactionService', () => ({
  transactionService: {
    list: vi.fn(),
  },
}))

vi.mock('@/services/categoryService', () => ({
  categoryService: {
    list: vi.fn(),
  },
}))

import { reconciliationService } from '@/services/reconciliationService'
import { transactionService } from '@/services/transactionService'
import { categoryService } from '@/services/categoryService'

const mockReconciliation = {
  id: 'recon-123',
  user_id: 'user-1',
  account_id: 'account-123',
  statement_balance: '1500.00',
  statement_date: '2026-01-15',
  status: 'IN_PROGRESS' as const,
  cleared_balance: '1400.00',
  discrepancy: '100.00',
  created_at: '2026-01-15T10:00:00Z',
  completed_at: null,
  adjustment_transaction_id: null,
}

const mockTransactions = [
  {
    id: 'tx-1',
    user_id: 'user-1',
    account_id: 'account-123',
    date: '2026-01-10',
    payee: 'Grocery Store',
    memo: null,
    amount: '-50.00',
    state: 'APPROVED',
    category_id: null,
    created_at: '2026-01-10T00:00:00Z',
    updated_at: '2026-01-10T00:00:00Z',
  },
  {
    id: 'tx-2',
    user_id: 'user-1',
    account_id: 'account-123',
    date: '2026-01-12',
    payee: 'Paycheck',
    memo: null,
    amount: '2000.00',
    state: 'APPROVED',
    category_id: null,
    created_at: '2026-01-12T00:00:00Z',
    updated_at: '2026-01-12T00:00:00Z',
  },
  {
    id: 'tx-3',
    user_id: 'user-1',
    account_id: 'account-123',
    date: '2026-01-14',
    payee: 'Electric Bill',
    memo: null,
    amount: '-100.00',
    state: 'CLEARED',
    category_id: null,
    created_at: '2026-01-14T00:00:00Z',
    updated_at: '2026-01-14T00:00:00Z',
  },
]

const mockCategoryGroups = [
  {
    id: 'group-1',
    user_id: 'user-1',
    name: 'Bills',
    sort_order: 1,
    is_income: false,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    categories: [
      {
        id: 'cat-1',
        user_id: 'user-1',
        group_id: 'group-1',
        name: 'Miscellaneous',
        sort_order: 1,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
    ],
  },
]

describe('ReconcileModal', () => {
  const onClose = vi.fn()
  const onComplete = vi.fn()

  const defaultProps = {
    accountId: 'account-123',
    accountName: 'Main Checking',
    accountBalance: '1500.00',
    isOpen: true,
    onClose,
    onComplete,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Step 1 - Statement Entry', () => {
    it('should render initial form with statement balance and date fields', () => {
      render(<ReconcileModal {...defaultProps} />)

      expect(screen.getByText(/reconcile account/i)).toBeInTheDocument()
      expect(screen.getByText(defaultProps.accountName)).toBeInTheDocument()
      expect(screen.getByLabelText(/statement balance/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/statement date/i)).toBeInTheDocument()
    })

    it('should not render when isOpen is false', () => {
      render(<ReconcileModal {...defaultProps} isOpen={false} />)

      expect(screen.queryByText(/reconcile account/i)).not.toBeInTheDocument()
    })

    it('should call onClose when cancel button is clicked', async () => {
      const user = userEvent.setup()

      render(<ReconcileModal {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: /cancel/i }))

      expect(onClose).toHaveBeenCalled()
    })

    it('should not call start when statement balance is empty', async () => {
      const user = userEvent.setup()

      render(<ReconcileModal {...defaultProps} />)

      // Leave the balance input empty
      const balanceInput = screen.getByLabelText(/statement balance/i)
      expect(balanceInput).toHaveValue(null)

      await user.click(screen.getByRole('button', { name: /start reconciliation/i }))

      // Should not call the service (HTML5 validation blocks submit)
      expect(reconciliationService.start).not.toHaveBeenCalled()
    })

    it('should start reconciliation and proceed to step 2', async () => {
      const user = userEvent.setup()

      vi.mocked(reconciliationService.start).mockResolvedValueOnce(mockReconciliation)
      vi.mocked(transactionService.list).mockResolvedValueOnce({
        transactions: mockTransactions,
        total: 3,
      })

      render(<ReconcileModal {...defaultProps} />)

      const balanceInput = screen.getByLabelText(/statement balance/i)
      await user.clear(balanceInput)
      await user.type(balanceInput, '1500.00')

      await user.click(screen.getByRole('button', { name: /start reconciliation/i }))

      await waitFor(() => {
        expect(reconciliationService.start).toHaveBeenCalledWith({
          account_id: defaultProps.accountId,
          statement_balance: '1500.00',
          statement_date: expect.any(String),
        })
      })

      // Should show transactions list (step 2)
      await waitFor(() => {
        expect(screen.getByText(/grocery store/i)).toBeInTheDocument()
      })
    })
  })

  describe('Step 2 - Mark Transactions', () => {
    async function renderAtStep2() {
      const user = userEvent.setup()

      vi.mocked(reconciliationService.start).mockResolvedValueOnce(mockReconciliation)
      vi.mocked(transactionService.list).mockResolvedValueOnce({
        transactions: mockTransactions,
        total: 3,
      })

      render(<ReconcileModal {...defaultProps} />)

      // Fill in step 1 and proceed
      const balanceInput = screen.getByLabelText(/statement balance/i)
      await user.clear(balanceInput)
      await user.type(balanceInput, '1500.00')

      await user.click(screen.getByRole('button', { name: /start reconciliation/i }))

      await waitFor(() => {
        expect(screen.getByText(/grocery store/i)).toBeInTheDocument()
      })

      return user
    }

    it('should display transactions list', async () => {
      await renderAtStep2()

      expect(screen.getByText(/grocery store/i)).toBeInTheDocument()
      expect(screen.getByText(/paycheck/i)).toBeInTheDocument()
      expect(screen.getByText(/electric bill/i)).toBeInTheDocument()
    })

    it('should show current balances and discrepancy', async () => {
      await renderAtStep2()

      // Should show balance summary section with amounts
      // The balance labels are shown along with values
      expect(screen.getByText('$1,500.00')).toBeInTheDocument() // statement
      expect(screen.getByText('$1,400.00')).toBeInTheDocument() // cleared
      expect(screen.getByText('Difference')).toBeInTheDocument()
    })

    it('should mark transaction as cleared when checkbox is clicked', async () => {
      const user = await renderAtStep2()

      vi.mocked(reconciliationService.markCleared).mockResolvedValueOnce({
        cleared_balance: '1350.00',
        discrepancy: '150.00',
      })

      // Find checkboxes - the first unchecked one (APPROVED transactions)
      const checkboxes = screen.getAllByRole('checkbox')
      const uncheckedCheckbox = checkboxes.find(cb => !cb.hasAttribute('checked'))

      if (uncheckedCheckbox) {
        await user.click(uncheckedCheckbox)

        await waitFor(() => {
          expect(reconciliationService.markCleared).toHaveBeenCalled()
        })
      }
    })

    it('should proceed to step 3 when continue button is clicked', async () => {
      const user = await renderAtStep2()

      vi.mocked(categoryService.list).mockResolvedValueOnce({ groups: mockCategoryGroups, total_groups: 1, total_categories: 1 })

      await user.click(screen.getByRole('button', { name: /continue/i }))

      await waitFor(() => {
        // Should show final review/complete step
        expect(screen.getByRole('button', { name: /complete/i })).toBeInTheDocument()
      })
    })
  })

  describe('Step 3 - Complete Reconciliation', () => {
    async function renderAtStep3(balanced = true) {
      const user = userEvent.setup()

      const recon = balanced
        ? { ...mockReconciliation, cleared_balance: '1500.00', discrepancy: '0.00' }
        : mockReconciliation

      vi.mocked(reconciliationService.start).mockResolvedValueOnce(recon)
      vi.mocked(transactionService.list).mockResolvedValueOnce({
        transactions: mockTransactions,
        total: 3,
      })
      vi.mocked(categoryService.list).mockResolvedValueOnce({ groups: mockCategoryGroups, total_groups: 1, total_categories: 1 })

      render(<ReconcileModal {...defaultProps} />)

      // Navigate through step 1
      const balanceInput = screen.getByLabelText(/statement balance/i)
      await user.clear(balanceInput)
      await user.type(balanceInput, '1500.00')

      await user.click(screen.getByRole('button', { name: /start reconciliation/i }))

      await waitFor(() => {
        expect(screen.getByText(/grocery store/i)).toBeInTheDocument()
      })

      // Navigate to step 3
      await user.click(screen.getByRole('button', { name: /continue/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /complete/i })).toBeInTheDocument()
      })

      return user
    }

    it('should show success message when balanced', async () => {
      await renderAtStep3(true)

      expect(screen.getByText(/balanced/i)).toBeInTheDocument()
    })

    it('should complete reconciliation when complete button is clicked', async () => {
      const user = await renderAtStep3(true)

      vi.mocked(reconciliationService.complete).mockResolvedValueOnce({
        ...mockReconciliation,
        status: 'COMPLETED',
        completed_at: '2026-01-15T10:30:00Z',
      })

      await user.click(screen.getByRole('button', { name: /complete/i }))

      await waitFor(() => {
        expect(reconciliationService.complete).toHaveBeenCalledWith(mockReconciliation.id)
      })

      await waitFor(() => {
        expect(onComplete).toHaveBeenCalled()
      })
    })

    it('should show adjustment option when there is a discrepancy', async () => {
      await renderAtStep3(false)

      // Should show the adjustment section with create button
      expect(screen.getByRole('button', { name: /create adjustment/i })).toBeInTheDocument()
      expect(screen.getByText(/create an adjustment/i)).toBeInTheDocument()
    })

    it('should go back to step 2 when back button is clicked', async () => {
      const user = await renderAtStep3(true)

      await user.click(screen.getByRole('button', { name: /back/i }))

      await waitFor(() => {
        expect(screen.getByText(/grocery store/i)).toBeInTheDocument()
      })
    })

    it('should cancel reconciliation when cancel is clicked', async () => {
      const user = await renderAtStep3(true)

      vi.mocked(reconciliationService.cancel).mockResolvedValueOnce(undefined)

      await user.click(screen.getByRole('button', { name: /cancel/i }))

      await waitFor(() => {
        expect(reconciliationService.cancel).toHaveBeenCalledWith(mockReconciliation.id)
      })

      expect(onClose).toHaveBeenCalled()
    })
  })

  describe('Adjustment Creation', () => {
    it('should create adjustment when button is clicked', async () => {
      const user = userEvent.setup()

      vi.mocked(reconciliationService.start).mockResolvedValueOnce(mockReconciliation)
      vi.mocked(transactionService.list).mockResolvedValueOnce({
        transactions: mockTransactions,
        total: 3,
      })
      vi.mocked(categoryService.list).mockResolvedValueOnce({ groups: mockCategoryGroups, total_groups: 1, total_categories: 1 })
      vi.mocked(reconciliationService.createAdjustment).mockResolvedValueOnce({
        transaction: {
          id: 'adj-tx-1',
          user_id: 'user-1',
          account_id: 'account-123',
          date: '2026-01-15',
          payee: 'Reconciliation Adjustment',
          memo: null,
          amount: '100.00',
          state: 'CLEARED',
          category_id: 'cat-1',
          created_at: '2026-01-15T10:00:00Z',
          updated_at: '2026-01-15T10:00:00Z',
        },
        cleared_balance: '1500.00',
        discrepancy: '0.00',
      })
      vi.mocked(reconciliationService.get).mockResolvedValueOnce({
        ...mockReconciliation,
        cleared_balance: '1500.00',
        discrepancy: '0.00',
      })

      render(<ReconcileModal {...defaultProps} />)

      // Navigate through step 1
      const balanceInput = screen.getByLabelText(/statement balance/i)
      await user.clear(balanceInput)
      await user.type(balanceInput, '1500.00')

      await user.click(screen.getByRole('button', { name: /start reconciliation/i }))

      await waitFor(() => {
        expect(screen.getByText(/grocery store/i)).toBeInTheDocument()
      })

      // Navigate to step 3
      await user.click(screen.getByRole('button', { name: /continue/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /create adjustment/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /create adjustment/i }))

      await waitFor(() => {
        expect(reconciliationService.createAdjustment).toHaveBeenCalledWith(
          mockReconciliation.id,
          { category_id: 'cat-1' }
        )
      })
    })
  })

  describe('Error Handling', () => {
    it('should display error when start reconciliation fails', async () => {
      const user = userEvent.setup()

      vi.mocked(reconciliationService.start).mockRejectedValueOnce(
        new Error('Failed to start reconciliation')
      )

      render(<ReconcileModal {...defaultProps} />)

      const balanceInput = screen.getByLabelText(/statement balance/i)
      await user.clear(balanceInput)
      await user.type(balanceInput, '1500.00')

      await user.click(screen.getByRole('button', { name: /start reconciliation/i }))

      await waitFor(() => {
        expect(screen.getByText(/failed to start reconciliation/i)).toBeInTheDocument()
      })
    })

    it('should display error when complete reconciliation fails', async () => {
      const user = userEvent.setup()

      vi.mocked(reconciliationService.start).mockResolvedValueOnce({
        ...mockReconciliation,
        cleared_balance: '1500.00',
        discrepancy: '0.00',
      })
      vi.mocked(transactionService.list).mockResolvedValueOnce({
        transactions: mockTransactions,
        total: 3,
      })
      vi.mocked(categoryService.list).mockResolvedValueOnce({ groups: mockCategoryGroups, total_groups: 1, total_categories: 1 })
      vi.mocked(reconciliationService.complete).mockRejectedValueOnce(
        new Error('Failed to complete')
      )

      render(<ReconcileModal {...defaultProps} />)

      // Navigate through step 1
      const balanceInput = screen.getByLabelText(/statement balance/i)
      await user.clear(balanceInput)
      await user.type(balanceInput, '1500.00')

      await user.click(screen.getByRole('button', { name: /start reconciliation/i }))

      await waitFor(() => {
        expect(screen.getByText(/grocery store/i)).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /continue/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /complete/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /complete/i }))

      await waitFor(() => {
        expect(screen.getByText(/failed to complete/i)).toBeInTheDocument()
      })
    })
  })
})
