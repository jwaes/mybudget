/**
 * Reconcile Modal component.
 *
 * Multi-step modal for account reconciliation workflow.
 * Step 1: Enter statement balance and date
 * Step 2: Select transactions to mark as cleared
 * Step 3: Review, create adjustment if needed, complete
 */

import { useState, useEffect, type FormEvent } from 'react'
import { reconciliationService } from '@/services/reconciliationService'
import { transactionService } from '@/services/transactionService'
import { categoryService } from '@/services/categoryService'
import type { Reconciliation } from '@/types/reconciliation'
import type { Transaction } from '@/types/transaction'
import type { CategoryGroupWithCategories } from '@/types/category'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

interface ReconcileModalProps {
  accountId: string
  accountName: string
  accountBalance: string
  isOpen: boolean
  onClose: () => void
  onComplete: () => void
}

type Step = 'start' | 'transactions' | 'review'

function formatAmount(amount: string): string {
  const num = parseFloat(amount)
  if (isNaN(num)) return '0.00'
  return num.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function ReconcileModal({
  accountId,
  accountName,
  accountBalance,
  isOpen,
  onClose,
  onComplete,
}: ReconcileModalProps) {
  const [step, setStep] = useState<Step>('start')
  const [statementBalance, setStatementBalance] = useState('')
  const [statementDate, setStatementDate] = useState('')
  const [reconciliation, setReconciliation] = useState<Reconciliation | null>(null)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [selectedTxIds, setSelectedTxIds] = useState<Set<string>>(new Set())
  const [categoryGroups, setCategoryGroups] = useState<CategoryGroupWithCategories[]>([])
  const [adjustmentCategoryId, setAdjustmentCategoryId] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset when modal opens
  useEffect(() => {
    if (isOpen) {
      setStep('start')
      setStatementBalance('')
      const today = new Date().toISOString()
      setStatementDate(today.split('T')[0] ?? today.substring(0, 10))
      setReconciliation(null)
      setTransactions([])
      setSelectedTxIds(new Set())
      setAdjustmentCategoryId('')
      setError(null)
    }
  }, [isOpen])

  // Fetch transactions when reconciliation is created
  useEffect(() => {
    if (reconciliation && step === 'transactions') {
      fetchTransactions()
    }
  }, [reconciliation, step])

  // Fetch category groups for adjustment dropdown
  useEffect(() => {
    if (step === 'review') {
      fetchCategoryGroups()
    }
  }, [step])

  const fetchTransactions = async () => {
    try {
      // Fetch approved and cleared transactions for this account
      const response = await transactionService.list({
        account_id: accountId,
        limit: 500,
      })
      // Filter to only approved and cleared
      const relevantTx = response.transactions.filter(
        (tx) => tx.state === 'APPROVED' || tx.state === 'CLEARED'
      )
      setTransactions(relevantTx)
      // Pre-select already cleared transactions
      const clearedIds = new Set(
        relevantTx.filter((tx) => tx.state === 'CLEARED').map((tx) => tx.id)
      )
      setSelectedTxIds(clearedIds)
    } catch (err) {
      setError('Failed to fetch transactions')
    }
  }

  const fetchCategoryGroups = async () => {
    try {
      const response = await categoryService.list()
      setCategoryGroups(response.groups)
      // Set default category if available
      const firstGroup = response.groups[0]
      const firstCategory = firstGroup?.categories[0]
      if (firstCategory) {
        setAdjustmentCategoryId(firstCategory.id)
      }
    } catch (err) {
      // Non-critical, just for adjustment dropdown
    }
  }

  const handleStartReconciliation = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    const balance = parseFloat(statementBalance)
    if (isNaN(balance)) {
      setError('Please enter a valid statement balance')
      return
    }

    setIsSubmitting(true)
    try {
      const recon = await reconciliationService.start({
        account_id: accountId,
        statement_balance: balance.toFixed(2),
        statement_date: statementDate,
      })
      setReconciliation(recon)
      setStep('transactions')
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to start reconciliation')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleToggleTransaction = async (txId: string) => {
    if (!reconciliation) return

    const isCurrentlySelected = selectedTxIds.has(txId)
    setIsSubmitting(true)
    setError(null)

    try {
      if (isCurrentlySelected) {
        const response = await reconciliationService.unmarkCleared(reconciliation.id, {
          transaction_ids: [txId],
        })
        setSelectedTxIds((prev) => {
          const next = new Set(prev)
          next.delete(txId)
          return next
        })
        setReconciliation((prev) =>
          prev
            ? {
                ...prev,
                cleared_balance: response.cleared_balance,
                discrepancy: response.discrepancy,
              }
            : null
        )
      } else {
        const response = await reconciliationService.markCleared(reconciliation.id, {
          transaction_ids: [txId],
        })
        setSelectedTxIds((prev) => new Set(prev).add(txId))
        setReconciliation((prev) =>
          prev
            ? {
                ...prev,
                cleared_balance: response.cleared_balance,
                discrepancy: response.discrepancy,
              }
            : null
        )
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to update transaction')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSelectAll = async () => {
    if (!reconciliation) return

    const unselectedTxIds = transactions
      .filter((tx) => !selectedTxIds.has(tx.id))
      .map((tx) => tx.id)

    if (unselectedTxIds.length === 0) return

    setIsSubmitting(true)
    setError(null)

    try {
      const response = await reconciliationService.markCleared(reconciliation.id, {
        transaction_ids: unselectedTxIds,
      })
      setSelectedTxIds(new Set(transactions.map((tx) => tx.id)))
      setReconciliation((prev) =>
        prev
          ? {
              ...prev,
              cleared_balance: response.cleared_balance,
              discrepancy: response.discrepancy,
            }
          : null
      )
    } catch (err) {
      setError('Failed to mark all transactions')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClearAll = async () => {
    if (!reconciliation) return

    const selectedIds = Array.from(selectedTxIds)
    if (selectedIds.length === 0) return

    setIsSubmitting(true)
    setError(null)

    try {
      const response = await reconciliationService.unmarkCleared(reconciliation.id, {
        transaction_ids: selectedIds,
      })
      setSelectedTxIds(new Set())
      setReconciliation((prev) =>
        prev
          ? {
              ...prev,
              cleared_balance: response.cleared_balance,
              discrepancy: response.discrepancy,
            }
          : null
      )
    } catch (err) {
      setError('Failed to clear selection')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCreateAdjustment = async () => {
    if (!reconciliation || !adjustmentCategoryId) return

    setIsSubmitting(true)
    setError(null)

    try {
      await reconciliationService.createAdjustment(reconciliation.id, {
        category_id: adjustmentCategoryId,
      })
      const updated = await reconciliationService.get(reconciliation.id)
      setReconciliation(updated)
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to create adjustment')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleComplete = async () => {
    if (!reconciliation) return

    setIsSubmitting(true)
    setError(null)

    try {
      await reconciliationService.complete(reconciliation.id)
      onComplete()
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to complete reconciliation')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancel = async () => {
    if (reconciliation) {
      try {
        await reconciliationService.cancel(reconciliation.id)
      } catch (err) {
        // Ignore cancellation errors
      }
    }
    onClose()
  }

  // Step 1: Enter statement balance
  const renderStartStep = () => (
    <form onSubmit={handleStartReconciliation} className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Enter your bank statement balance and date to begin reconciliation.
      </p>

      {error && (
        <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="space-y-2">
        <label htmlFor="statementBalance" className="text-sm font-medium">
          Statement Balance
        </label>
        <div className="flex items-center rounded-md border">
          <span className="px-3 text-muted-foreground">$</span>
          <Input
            id="statementBalance"
            type="number"
            step="0.01"
            value={statementBalance}
            onChange={(e) => setStatementBalance(e.target.value)}
            placeholder="0.00"
            className="border-0 focus-visible:ring-0"
            disabled={isSubmitting}
            required
          />
        </div>
      </div>

      <div className="space-y-2">
        <label htmlFor="statementDate" className="text-sm font-medium">
          Statement Date
        </label>
        <Input
          id="statementDate"
          type="date"
          value={statementDate}
          onChange={(e) => setStatementDate(e.target.value)}
          disabled={isSubmitting}
          required
        />
      </div>

      <div className="rounded-md bg-muted p-3">
        <div className="text-sm text-muted-foreground">Current Account Balance</div>
        <div className="text-lg font-semibold">${formatAmount(accountBalance)}</div>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={handleCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Starting...' : 'Start Reconciliation'}
        </Button>
      </div>
    </form>
  )

  // Step 2: Select transactions
  const renderTransactionsStep = () => (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Select the transactions that appear on your statement.
      </p>

      {error && (
        <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {reconciliation && (
        <div className="grid grid-cols-3 gap-4 rounded-md bg-muted p-3 text-sm">
          <div>
            <div className="text-muted-foreground">Statement</div>
            <div className="font-semibold">${formatAmount(reconciliation.statement_balance)}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Cleared</div>
            <div className="font-semibold">${formatAmount(reconciliation.cleared_balance)}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Difference</div>
            <div
              className={cn(
                'font-semibold',
                parseFloat(reconciliation.discrepancy) === 0
                  ? 'text-green-600'
                  : 'text-destructive'
              )}
            >
              ${formatAmount(reconciliation.discrepancy)}
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleSelectAll}
          disabled={isSubmitting}
        >
          Select All
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleClearAll}
          disabled={isSubmitting}
        >
          Clear All
        </Button>
      </div>

      <div className="max-h-64 overflow-y-auto rounded-md border">
        {transactions.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No transactions to reconcile
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50">
              <tr>
                <th className="p-2 text-left font-medium"></th>
                <th className="p-2 text-left font-medium">Date</th>
                <th className="p-2 text-left font-medium">Payee</th>
                <th className="p-2 text-right font-medium">Amount</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <tr
                  key={tx.id}
                  className={cn(
                    'cursor-pointer border-b hover:bg-muted/50',
                    selectedTxIds.has(tx.id) && 'bg-primary/10'
                  )}
                  onClick={() => handleToggleTransaction(tx.id)}
                >
                  <td className="p-2">
                    <input
                      type="checkbox"
                      checked={selectedTxIds.has(tx.id)}
                      onChange={() => {}}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                  </td>
                  <td className="p-2">{formatDate(tx.date)}</td>
                  <td className="p-2 max-w-[150px] truncate">{tx.payee}</td>
                  <td
                    className={cn(
                      'p-2 text-right tabular-nums',
                      parseFloat(tx.amount) < 0 ? 'text-destructive' : 'text-green-600'
                    )}
                  >
                    ${formatAmount(tx.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={() => setStep('start')}
          disabled={isSubmitting}
        >
          Back
        </Button>
        <Button type="button" variant="outline" onClick={handleCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="button" onClick={() => setStep('review')} disabled={isSubmitting}>
          Continue
        </Button>
      </div>
    </div>
  )

  // Step 3: Review and complete
  const renderReviewStep = () => {
    if (!reconciliation) return null

    const discrepancy = parseFloat(reconciliation.discrepancy)
    const isBalanced = discrepancy === 0

    return (
      <div className="space-y-4">
        {error && (
          <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="grid grid-cols-3 gap-4 rounded-md bg-muted p-3 text-sm">
          <div>
            <div className="text-muted-foreground">Statement</div>
            <div className="font-semibold">${formatAmount(reconciliation.statement_balance)}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Cleared</div>
            <div className="font-semibold">${formatAmount(reconciliation.cleared_balance)}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Difference</div>
            <div
              className={cn(
                'font-semibold',
                isBalanced ? 'text-green-600' : 'text-destructive'
              )}
            >
              ${formatAmount(reconciliation.discrepancy)}
            </div>
          </div>
        </div>

        {isBalanced ? (
          <div className="rounded-md bg-green-50 p-4 text-center text-green-700">
            <p className="font-medium">Your account is balanced!</p>
            <p className="text-sm">Click Complete to finish reconciliation.</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="rounded-md bg-amber-50 p-4 text-amber-800">
              <p className="font-medium">
                There is a ${formatAmount(Math.abs(discrepancy).toString())} difference.
              </p>
              <p className="text-sm">You can go back and mark more transactions, or create an adjustment.</p>
            </div>

            <div className="space-y-2">
              <label htmlFor="adjustmentCategory" className="text-sm font-medium">
                Adjustment Category
              </label>
              <select
                id="adjustmentCategory"
                value={adjustmentCategoryId}
                onChange={(e) => setAdjustmentCategoryId(e.target.value)}
                disabled={isSubmitting}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {categoryGroups.map((group) => (
                  <optgroup key={group.id} label={group.name}>
                    {group.categories?.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.name}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
              <Button
                type="button"
                variant="secondary"
                onClick={handleCreateAdjustment}
                disabled={isSubmitting || !adjustmentCategoryId}
                className="w-full"
              >
                {isSubmitting ? 'Creating...' : 'Create Adjustment'}
              </Button>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => setStep('transactions')}
            disabled={isSubmitting}
          >
            Back
          </Button>
          <Button type="button" variant="outline" onClick={handleCancel} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="button" onClick={handleComplete} disabled={isSubmitting || !isBalanced}>
            {isSubmitting ? 'Completing...' : 'Complete'}
          </Button>
        </div>
      </div>
    )
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleCancel()}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            Reconcile Account
            <span className="rounded bg-muted px-2 py-1 text-sm font-normal text-muted-foreground">
              {accountName}
            </span>
          </DialogTitle>
          <DialogDescription className="sr-only">
            Reconcile your account with your bank statement
          </DialogDescription>
        </DialogHeader>

        {/* Step indicator */}
        <div className="flex gap-4 border-b pb-3">
          <span
            className={cn(
              'rounded px-2 py-1 text-sm',
              step === 'start'
                ? 'bg-primary/10 font-medium text-primary'
                : 'text-green-600'
            )}
          >
            1. Enter Balance
          </span>
          <span
            className={cn(
              'rounded px-2 py-1 text-sm',
              step === 'transactions'
                ? 'bg-primary/10 font-medium text-primary'
                : step === 'review'
                  ? 'text-green-600'
                  : 'text-muted-foreground'
            )}
          >
            2. Mark Cleared
          </span>
          <span
            className={cn(
              'rounded px-2 py-1 text-sm',
              step === 'review'
                ? 'bg-primary/10 font-medium text-primary'
                : 'text-muted-foreground'
            )}
          >
            3. Complete
          </span>
        </div>

        {/* Step content */}
        <div className="flex-1 overflow-y-auto py-4">
          {step === 'start' && renderStartStep()}
          {step === 'transactions' && renderTransactionsStep()}
          {step === 'review' && renderReviewStep()}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default ReconcileModal
