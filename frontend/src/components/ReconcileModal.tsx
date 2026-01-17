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
import type { CategoryGroup } from '@/types/category'

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
  const [categoryGroups, setCategoryGroups] = useState<CategoryGroup[]>([])
  const [adjustmentCategoryId, setAdjustmentCategoryId] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset when modal opens
  useEffect(() => {
    if (isOpen) {
      setStep('start')
      setStatementBalance('')
      setStatementDate(new Date().toISOString().split('T')[0])
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
      const groups = await categoryService.listGroups()
      setCategoryGroups(groups)
      // Set default category if available
      if (groups.length > 0 && groups[0].categories && groups[0].categories.length > 0) {
        setAdjustmentCategoryId(groups[0].categories[0].id)
      }
    } catch (err) {
      // Non-critical, just for adjustment dropdown
    }
  }

  if (!isOpen) return null

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
        // Unmark as cleared
        const response = await reconciliationService.unmarkCleared(reconciliation.id, {
          transaction_ids: [txId],
        })
        setSelectedTxIds((prev) => {
          const next = new Set(prev)
          next.delete(txId)
          return next
        })
        // Update reconciliation balances
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
        // Mark as cleared
        const response = await reconciliationService.markCleared(reconciliation.id, {
          transaction_ids: [txId],
        })
        setSelectedTxIds((prev) => new Set(prev).add(txId))
        // Update reconciliation balances
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
      // Refresh reconciliation to get updated balances
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
      onClose()
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
      } catch {
        // Ignore cancellation errors
      }
    }
    onClose()
  }

  const discrepancy = reconciliation ? parseFloat(reconciliation.discrepancy) : 0
  const isBalanced = Math.abs(discrepancy) < 0.01

  const renderStartStep = () => (
    <form onSubmit={handleStartReconciliation}>
      {error && <div className="error-message">{error}</div>}

      <p className="info-text">
        Enter the ending balance and date from your bank statement to begin reconciling.
      </p>

      <div className="form-group">
        <label htmlFor="statementBalance">Statement Balance</label>
        <div className="amount-input-wrapper">
          <span className="currency-symbol">$</span>
          <input
            id="statementBalance"
            type="number"
            step="0.01"
            value={statementBalance}
            onChange={(e) => setStatementBalance(e.target.value)}
            placeholder="0.00"
            disabled={isSubmitting}
            required
            autoFocus
          />
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="statementDate">Statement Date</label>
        <input
          id="statementDate"
          type="date"
          value={statementDate}
          onChange={(e) => setStatementDate(e.target.value)}
          max={new Date().toISOString().split('T')[0]}
          disabled={isSubmitting}
          required
        />
      </div>

      <div className="account-info">
        <span>Current Balance:</span>
        <span className="balance">${formatAmount(accountBalance)}</span>
      </div>

      <div className="modal-actions">
        <button type="button" className="cancel-btn" onClick={handleCancel} disabled={isSubmitting}>
          Cancel
        </button>
        <button type="submit" className="primary-btn" disabled={isSubmitting}>
          {isSubmitting ? 'Starting...' : 'Start Reconciliation'}
        </button>
      </div>
    </form>
  )

  const renderTransactionsStep = () => (
    <div className="transactions-step">
      {error && <div className="error-message">{error}</div>}

      <div className="balance-summary">
        <div className="balance-row">
          <span>Statement Balance:</span>
          <span>${formatAmount(reconciliation?.statement_balance || '0')}</span>
        </div>
        <div className="balance-row">
          <span>Cleared Balance:</span>
          <span>${formatAmount(reconciliation?.cleared_balance || '0')}</span>
        </div>
        <div className={`balance-row discrepancy ${isBalanced ? 'balanced' : 'unbalanced'}`}>
          <span>Difference:</span>
          <span>${formatAmount(reconciliation?.discrepancy || '0')}</span>
        </div>
      </div>

      <div className="transactions-header">
        <span>{transactions.length} transactions</span>
        <div className="bulk-actions">
          <button
            type="button"
            className="link-btn"
            onClick={handleSelectAll}
            disabled={isSubmitting}
          >
            Select All
          </button>
          <button
            type="button"
            className="link-btn"
            onClick={handleClearAll}
            disabled={isSubmitting}
          >
            Clear All
          </button>
        </div>
      </div>

      <div className="transactions-list">
        {transactions.length === 0 ? (
          <p className="no-transactions">No approved transactions to reconcile.</p>
        ) : (
          transactions.map((tx) => (
            <label
              key={tx.id}
              className={`transaction-row ${selectedTxIds.has(tx.id) ? 'selected' : ''}`}
            >
              <input
                type="checkbox"
                checked={selectedTxIds.has(tx.id)}
                onChange={() => handleToggleTransaction(tx.id)}
                disabled={isSubmitting}
              />
              <span className="tx-date">{formatDate(tx.date)}</span>
              <span className="tx-payee">{tx.payee}</span>
              <span className={`tx-amount ${parseFloat(tx.amount) < 0 ? 'negative' : 'positive'}`}>
                ${formatAmount(tx.amount)}
              </span>
            </label>
          ))
        )}
      </div>

      <div className="modal-actions">
        <button type="button" className="cancel-btn" onClick={handleCancel} disabled={isSubmitting}>
          Cancel
        </button>
        <button
          type="button"
          className="primary-btn"
          onClick={() => setStep('review')}
          disabled={isSubmitting}
        >
          Continue
        </button>
      </div>
    </div>
  )

  const renderReviewStep = () => (
    <div className="review-step">
      {error && <div className="error-message">{error}</div>}

      <div className="balance-summary large">
        <div className="balance-row">
          <span>Statement Balance:</span>
          <span>${formatAmount(reconciliation?.statement_balance || '0')}</span>
        </div>
        <div className="balance-row">
          <span>Cleared Balance:</span>
          <span>${formatAmount(reconciliation?.cleared_balance || '0')}</span>
        </div>
        <div className={`balance-row discrepancy ${isBalanced ? 'balanced' : 'unbalanced'}`}>
          <span>Difference:</span>
          <span className="discrepancy-amount">
            ${formatAmount(reconciliation?.discrepancy || '0')}
          </span>
        </div>
      </div>

      {isBalanced ? (
        <div className="status-message success">
          Your account is balanced! Click "Complete" to finish reconciliation.
        </div>
      ) : (
        <div className="adjustment-section">
          <p className="status-message warning">
            There is a ${formatAmount(Math.abs(discrepancy).toString())} difference. You can:
          </p>
          <ul className="options-list">
            <li>Go back and mark more transactions as cleared</li>
            <li>Create an adjustment transaction to balance</li>
          </ul>

          <div className="adjustment-form">
            <label htmlFor="adjustmentCategory">Adjustment Category</label>
            <select
              id="adjustmentCategory"
              value={adjustmentCategoryId}
              onChange={(e) => setAdjustmentCategoryId(e.target.value)}
              disabled={isSubmitting}
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
            <button
              type="button"
              className="secondary-btn"
              onClick={handleCreateAdjustment}
              disabled={isSubmitting || !adjustmentCategoryId}
            >
              {isSubmitting ? 'Creating...' : 'Create Adjustment'}
            </button>
          </div>
        </div>
      )}

      <div className="modal-actions">
        <button
          type="button"
          className="back-btn"
          onClick={() => setStep('transactions')}
          disabled={isSubmitting}
        >
          Back
        </button>
        <div className="right-actions">
          <button type="button" className="cancel-btn" onClick={handleCancel} disabled={isSubmitting}>
            Cancel
          </button>
          <button
            type="button"
            className="primary-btn"
            onClick={handleComplete}
            disabled={isSubmitting || !isBalanced}
          >
            {isSubmitting ? 'Completing...' : 'Complete'}
          </button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="modal-overlay" onClick={handleCancel}>
      <div className="modal-content reconcile-modal" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>Reconcile Account</h2>
          <span className="account-name-display">{accountName}</span>
          <button className="close-btn" onClick={handleCancel} aria-label="Close">
            &times;
          </button>
        </header>

        <div className="step-indicator">
          <span className={`step ${step === 'start' ? 'active' : step !== 'start' ? 'complete' : ''}`}>
            1. Enter Balance
          </span>
          <span className={`step ${step === 'transactions' ? 'active' : step === 'review' ? 'complete' : ''}`}>
            2. Mark Cleared
          </span>
          <span className={`step ${step === 'review' ? 'active' : ''}`}>
            3. Complete
          </span>
        </div>

        <div className="modal-body">
          {step === 'start' && renderStartStep()}
          {step === 'transactions' && renderTransactionsStep()}
          {step === 'review' && renderReviewStep()}
        </div>

        <style>{`
          .reconcile-modal {
            max-width: 600px;
            max-height: 85vh;
            display: flex;
            flex-direction: column;
          }

          .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
          }

          .modal-content {
            background: white;
            border-radius: 8px;
            width: 100%;
            overflow: hidden;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
          }

          .modal-header {
            display: flex;
            align-items: center;
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #eee;
            background: #f9f9f9;
          }

          .modal-header h2 {
            margin: 0;
            font-size: 1.25rem;
            font-weight: 600;
          }

          .account-name-display {
            margin-left: 1rem;
            padding: 0.25rem 0.75rem;
            background: #e8e8e8;
            border-radius: 4px;
            font-size: 0.875rem;
            color: #555;
          }

          .close-btn {
            margin-left: auto;
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #666;
            padding: 0.25rem 0.5rem;
          }

          .close-btn:hover {
            color: #333;
          }

          .step-indicator {
            display: flex;
            border-bottom: 1px solid #eee;
            padding: 0.75rem 1.5rem;
            gap: 1rem;
          }

          .step {
            font-size: 0.875rem;
            color: #999;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
          }

          .step.active {
            color: #0066cc;
            font-weight: 500;
            background: #e6f0ff;
          }

          .step.complete {
            color: #28a745;
          }

          .modal-body {
            padding: 1.5rem;
            overflow-y: auto;
            flex: 1;
          }

          .info-text {
            margin: 0 0 1.5rem;
            color: #666;
          }

          .form-group {
            margin-bottom: 1.25rem;
          }

          .form-group label {
            display: block;
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: #333;
          }

          .amount-input-wrapper {
            display: flex;
            align-items: center;
            border: 1px solid #ccc;
            border-radius: 4px;
            overflow: hidden;
          }

          .currency-symbol {
            padding: 0.75rem;
            background: #f5f5f5;
            color: #666;
            font-weight: 500;
          }

          .amount-input-wrapper input {
            flex: 1;
            padding: 0.75rem;
            border: none;
            font-size: 1rem;
            outline: none;
          }

          .amount-input-wrapper:focus-within {
            border-color: #0066cc;
            box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
          }

          input[type="date"],
          select {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 1rem;
          }

          input[type="date"]:focus,
          select:focus {
            border-color: #0066cc;
            outline: none;
            box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
          }

          .account-info {
            display: flex;
            justify-content: space-between;
            padding: 1rem;
            background: #f9f9f9;
            border-radius: 4px;
            margin-bottom: 1.5rem;
          }

          .account-info .balance {
            font-weight: 600;
          }

          .error-message {
            background: #fee;
            color: #c00;
            padding: 0.75rem 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
            font-size: 0.875rem;
          }

          .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 0.75rem;
            margin-top: 1.5rem;
            padding-top: 1rem;
            border-top: 1px solid #eee;
          }

          .right-actions {
            display: flex;
            gap: 0.75rem;
          }

          .back-btn {
            margin-right: auto;
          }

          .cancel-btn,
          .primary-btn,
          .secondary-btn,
          .back-btn {
            padding: 0.75rem 1.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s ease;
          }

          .cancel-btn,
          .back-btn {
            background: white;
            border: 1px solid #ccc;
            color: #666;
          }

          .cancel-btn:hover:not(:disabled),
          .back-btn:hover:not(:disabled) {
            background: #f5f5f5;
          }

          .primary-btn {
            background: #0066cc;
            border: none;
            color: white;
          }

          .primary-btn:hover:not(:disabled) {
            background: #0052a3;
          }

          .primary-btn:disabled {
            background: #99c2e8;
          }

          .secondary-btn {
            background: #f0f0f0;
            border: 1px solid #ccc;
            color: #333;
          }

          .secondary-btn:hover:not(:disabled) {
            background: #e0e0e0;
          }

          button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
          }

          /* Transactions Step */
          .balance-summary {
            display: grid;
            gap: 0.5rem;
            padding: 1rem;
            background: #f9f9f9;
            border-radius: 4px;
            margin-bottom: 1rem;
          }

          .balance-summary.large {
            padding: 1.5rem;
            font-size: 1.1rem;
          }

          .balance-row {
            display: flex;
            justify-content: space-between;
          }

          .balance-row.discrepancy {
            padding-top: 0.5rem;
            border-top: 1px solid #ddd;
            font-weight: 600;
          }

          .balance-row.discrepancy.balanced {
            color: #28a745;
          }

          .balance-row.discrepancy.unbalanced {
            color: #dc3545;
          }

          .transactions-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            font-size: 0.875rem;
            color: #666;
          }

          .bulk-actions {
            display: flex;
            gap: 1rem;
          }

          .link-btn {
            background: none;
            border: none;
            color: #0066cc;
            cursor: pointer;
            padding: 0;
            font-size: 0.875rem;
          }

          .link-btn:hover {
            text-decoration: underline;
          }

          .transactions-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
          }

          .no-transactions {
            padding: 2rem;
            text-align: center;
            color: #666;
          }

          .transaction-row {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background 0.15s;
          }

          .transaction-row:last-child {
            border-bottom: none;
          }

          .transaction-row:hover {
            background: #f5f5f5;
          }

          .transaction-row.selected {
            background: #e6f0ff;
          }

          .transaction-row input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
          }

          .tx-date {
            width: 80px;
            font-size: 0.875rem;
            color: #666;
          }

          .tx-payee {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .tx-amount {
            font-family: monospace;
            font-weight: 500;
          }

          .tx-amount.negative {
            color: #dc3545;
          }

          .tx-amount.positive {
            color: #28a745;
          }

          /* Review Step */
          .status-message {
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
          }

          .status-message.success {
            background: #d4edda;
            color: #155724;
          }

          .status-message.warning {
            background: #fff3cd;
            color: #856404;
          }

          .options-list {
            margin: 0.5rem 0 1rem 1.5rem;
            color: #666;
          }

          .options-list li {
            margin-bottom: 0.25rem;
          }

          .adjustment-section {
            margin-top: 1rem;
          }

          .adjustment-form {
            display: flex;
            gap: 1rem;
            align-items: flex-end;
            margin-top: 1rem;
          }

          .adjustment-form label {
            flex: 1;
          }

          .adjustment-form select {
            margin-top: 0.5rem;
          }

          .adjustment-form .secondary-btn {
            white-space: nowrap;
          }
        `}</style>
      </div>
    </div>
  )
}

export default ReconcileModal
