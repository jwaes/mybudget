/**
 * TransactionInbox component.
 *
 * Displays inbox (unapproved) transactions with ability to approve them.
 */

import { useEffect, useState } from 'react'
import { transactionService } from '@/services/transactionService'
import { categoryService } from '@/services/categoryService'
import type { Transaction } from '@/types/transaction'
import type { CategoryGroupWithCategories } from '@/types/category'

interface TransactionInboxProps {
  accountId?: string
  onTransactionApproved?: (transaction: Transaction) => void
}

export function TransactionInbox({
  accountId,
  onTransactionApproved,
}: TransactionInboxProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [categories, setCategories] = useState<CategoryGroupWithCategories[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<Record<string, string>>({})

  useEffect(() => {
    loadData()
  }, [accountId])

  async function loadData() {
    try {
      setIsLoading(true)
      setError(null)
      const [txResponse, catResponse] = await Promise.all([
        transactionService.listInbox({ account_id: accountId }),
        categoryService.list(),
      ])
      setTransactions(txResponse.transactions)
      setCategories(catResponse.groups)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleApprove(transactionId: string) {
    const selection = selectedCategory[transactionId]
    if (!selection) {
      return
    }

    try {
      // "READY_TO_ASSIGN" means no category - money goes to Ready to Assign
      const categoryId = selection === 'READY_TO_ASSIGN' ? undefined : selection
      const updatedTx = await transactionService.approve(transactionId, {
        category_id: categoryId,
      })
      setTransactions((prev) => prev.filter((tx) => tx.id !== transactionId))
      onTransactionApproved?.(updatedTx)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve transaction')
    }
  }

  function handleCategoryChange(transactionId: string, categoryId: string) {
    setSelectedCategory((prev) => ({
      ...prev,
      [transactionId]: categoryId,
    }))
  }

  function formatCurrency(amount: string): string {
    const num = parseFloat(amount)
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(num)
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  if (isLoading) {
    return <div className="transaction-inbox loading">Loading transactions...</div>
  }

  if (error) {
    return (
      <div className="transaction-inbox error">
        <p>Error: {error}</p>
        <button onClick={loadData}>Retry</button>
      </div>
    )
  }

  if (transactions.length === 0) {
    return (
      <div className="transaction-inbox empty">
        <p>No transactions in inbox.</p>
        <p>All transactions have been categorized!</p>
      </div>
    )
  }

  return (
    <div className="transaction-inbox">
      <h2>Inbox ({transactions.length})</h2>
      <table className="transactions-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Payee</th>
            <th>Amount</th>
            <th>Category</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((tx) => (
            <tr key={tx.id} className="transaction-row">
              <td className="tx-date">{formatDate(tx.date)}</td>
              <td className="tx-payee">
                {tx.payee}
                {tx.memo && <span className="tx-memo">{tx.memo}</span>}
              </td>
              <td className={`tx-amount ${parseFloat(tx.amount) < 0 ? 'negative' : 'positive'}`}>
                {formatCurrency(tx.amount)}
              </td>
              <td className="tx-category">
                <select
                  value={selectedCategory[tx.id] || ''}
                  onChange={(e) => handleCategoryChange(tx.id, e.target.value)}
                  aria-label="Select category"
                >
                  <option value="">Select category...</option>
                  <option value="READY_TO_ASSIGN">➡️ Ready to Assign</option>
                  {categories.map((group) => (
                    <optgroup key={group.id} label={group.name}>
                      {group.categories.map((cat) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.name}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </td>
              <td className="tx-action">
                <button
                  onClick={() => handleApprove(tx.id)}
                  disabled={!selectedCategory[tx.id]}
                  aria-label="Approve transaction"
                >
                  Approve
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default TransactionInbox
