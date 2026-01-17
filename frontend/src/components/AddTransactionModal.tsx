/**
 * Add Transaction Modal component.
 *
 * Simple form to manually create transactions for testing purposes.
 */

import { useState, useEffect } from 'react'
import { transactionService } from '@/services/transactionService'
import { accountService } from '@/services/accountService'
import type { Account } from '@/types/account'

interface AddTransactionModalProps {
  isOpen: boolean
  onClose: () => void
  onTransactionAdded: () => void
  preselectedAccountId?: string
}

export function AddTransactionModal({
  isOpen,
  onClose,
  onTransactionAdded,
  preselectedAccountId,
}: AddTransactionModalProps) {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [accountId, setAccountId] = useState(preselectedAccountId || '')
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])
  const [payee, setPayee] = useState('')
  const [amount, setAmount] = useState('')
  const [memo, setMemo] = useState('')
  const [isInflow, setIsInflow] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      loadAccounts()
      // Reset form
      setDate(new Date().toISOString().split('T')[0])
      setPayee('')
      setAmount('')
      setMemo('')
      setIsInflow(false)
      setError(null)
      if (preselectedAccountId) {
        setAccountId(preselectedAccountId)
      }
    }
  }, [isOpen, preselectedAccountId])

  async function loadAccounts() {
    try {
      const response = await accountService.list()
      setAccounts(response.accounts)
      if (!accountId && response.accounts.length > 0) {
        setAccountId(response.accounts[0].id)
      }
    } catch (err) {
      console.error('Failed to load accounts:', err)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (!accountId) {
      setError('Please select an account')
      return
    }

    if (!payee.trim()) {
      setError('Please enter a payee')
      return
    }

    const parsedAmount = parseFloat(amount)
    if (isNaN(parsedAmount) || parsedAmount === 0) {
      setError('Please enter a valid amount')
      return
    }

    setIsSubmitting(true)

    try {
      // Outflows are negative, inflows are positive
      const finalAmount = isInflow ? Math.abs(parsedAmount) : -Math.abs(parsedAmount)

      await transactionService.create({
        account_id: accountId,
        date,
        payee: payee.trim(),
        amount: finalAmount.toFixed(2),
        memo: memo.trim() || null,
      })

      onTransactionAdded()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create transaction')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>Add Transaction</h2>
          <button className="close-btn" onClick={onClose} aria-label="Close">
            &times;
          </button>
        </header>

        <form onSubmit={handleSubmit} className="modal-body">
          {error && <p className="error-message">{error}</p>}

          <div className="form-group">
            <label htmlFor="account">Account</label>
            <select
              id="account"
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              required
            >
              <option value="">Select account...</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="date">Date</label>
            <input
              type="date"
              id="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="payee">Payee</label>
            <input
              type="text"
              id="payee"
              value={payee}
              onChange={(e) => setPayee(e.target.value)}
              placeholder="e.g., Grocery Store"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="amount">Amount</label>
            <div className="amount-input-row">
              <div className="amount-type-toggle">
                <button
                  type="button"
                  className={`toggle-btn ${!isInflow ? 'active' : ''}`}
                  onClick={() => setIsInflow(false)}
                >
                  Outflow
                </button>
                <button
                  type="button"
                  className={`toggle-btn ${isInflow ? 'active' : ''}`}
                  onClick={() => setIsInflow(true)}
                >
                  Inflow
                </button>
              </div>
              <div className="amount-input-wrapper">
                <span className="currency-symbol">$</span>
                <input
                  type="number"
                  id="amount"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                  step="0.01"
                  min="0"
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="memo">Memo (optional)</label>
            <input
              type="text"
              id="memo"
              value={memo}
              onChange={(e) => setMemo(e.target.value)}
              placeholder="Optional note"
            />
          </div>

          <div className="modal-actions">
            <button type="button" className="cancel-btn" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="primary-btn" disabled={isSubmitting}>
              {isSubmitting ? 'Adding...' : 'Add Transaction'}
            </button>
          </div>
        </form>

        <style>{`
          .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
          }

          .modal-content {
            background: white;
            border-radius: 8px;
            width: 100%;
            max-width: 450px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
          }

          .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #e5e5e5;
          }

          .modal-header h2 {
            margin: 0;
            font-size: 1.25rem;
          }

          .close-btn {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #666;
            padding: 0;
            line-height: 1;
          }

          .close-btn:hover {
            color: #333;
          }

          .modal-body {
            padding: 1.5rem;
          }

          .error-message {
            background-color: #fee;
            color: #c00;
            padding: 0.75rem;
            border-radius: 4px;
            margin-bottom: 1rem;
          }

          .form-group {
            margin-bottom: 1rem;
          }

          .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: #333;
          }

          .form-group input,
          .form-group select {
            width: 100%;
            padding: 0.625rem;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 1rem;
          }

          .form-group input:focus,
          .form-group select:focus {
            outline: none;
            border-color: #0066cc;
            box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
          }

          .amount-input-row {
            display: flex;
            gap: 0.75rem;
            align-items: center;
          }

          .amount-type-toggle {
            display: flex;
            border: 1px solid #ccc;
            border-radius: 4px;
            overflow: hidden;
          }

          .toggle-btn {
            padding: 0.5rem 0.75rem;
            border: none;
            background: #f5f5f5;
            cursor: pointer;
            font-size: 0.875rem;
            transition: background-color 0.2s;
          }

          .toggle-btn:first-child {
            border-right: 1px solid #ccc;
          }

          .toggle-btn.active {
            background: #0066cc;
            color: white;
          }

          .toggle-btn:hover:not(.active) {
            background: #e5e5e5;
          }

          .amount-input-wrapper {
            display: flex;
            align-items: center;
            flex: 1;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding-left: 0.625rem;
          }

          .amount-input-wrapper:focus-within {
            border-color: #0066cc;
            box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
          }

          .currency-symbol {
            color: #666;
            font-size: 1rem;
          }

          .amount-input-wrapper input {
            border: none;
            padding-left: 0.25rem;
          }

          .amount-input-wrapper input:focus {
            outline: none;
            box-shadow: none;
          }

          .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 0.75rem;
            margin-top: 1.5rem;
            padding-top: 1rem;
            border-top: 1px solid #e5e5e5;
          }

          .cancel-btn {
            padding: 0.625rem 1.25rem;
            background: #f5f5f5;
            border: 1px solid #ccc;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.875rem;
          }

          .cancel-btn:hover {
            background: #e5e5e5;
          }

          .primary-btn {
            padding: 0.625rem 1.25rem;
            background: #0066cc;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.875rem;
          }

          .primary-btn:hover:not(:disabled) {
            background: #0055aa;
          }

          .primary-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
          }
        `}</style>
      </div>
    </div>
  )
}

export default AddTransactionModal
