/**
 * Transactions page.
 *
 * Displays all transactions and provides access to the inbox.
 */

import { useState, useEffect } from 'react'
import { TransactionInbox } from '@/components/TransactionInbox'
import { CSVImport } from '@/components/CSVImport'
import { AddTransactionModal } from '@/components/AddTransactionModal'
import { transactionService } from '@/services/transactionService'
import { accountService } from '@/services/accountService'
import type { Transaction } from '@/types/transaction'
import type { Account } from '@/types/account'

type TabType = 'inbox' | 'all'

export function TransactionsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('inbox')
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [selectedAccountId, setSelectedAccountId] = useState<string | undefined>()
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)

  useEffect(() => {
    loadData()
  }, [activeTab, selectedAccountId])

  async function loadData() {
    try {
      setIsLoading(true)
      setError(null)

      // Load accounts if we haven't yet
      if (accounts.length === 0) {
        const accountsResponse = await accountService.list()
        setAccounts(accountsResponse.accounts)
      }

      // Load transactions based on active tab
      if (activeTab === 'all') {
        const response = await transactionService.list({
          account_id: selectedAccountId,
        })
        setTransactions(response.transactions)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setIsLoading(false)
    }
  }

  function handleTransactionApproved() {
    // Refresh transactions list if on 'all' tab
    if (activeTab === 'all') {
      loadData()
    }
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

  function getStateLabel(state: string): string {
    switch (state) {
      case 'INBOX':
        return 'Inbox'
      case 'APPROVED':
        return 'Approved'
      case 'CLEARED':
        return 'Cleared'
      default:
        return state
    }
  }

  return (
    <div className="transactions-page">
      <header className="page-header">
        <h1>Transactions</h1>
        <div className="header-actions">
          <button
            className="add-transaction-btn"
            onClick={() => setIsAddModalOpen(true)}
          >
            + Add Transaction
          </button>
          {selectedAccountId && (
            <CSVImport
              accountId={selectedAccountId}
              onImportComplete={loadData}
            />
          )}
        </div>
      </header>

      <div className="filters">
        <div className="account-filter">
          <label htmlFor="accountFilter">Account:</label>
          <select
            id="accountFilter"
            value={selectedAccountId || ''}
            onChange={(e) => setSelectedAccountId(e.target.value || undefined)}
          >
            <option value="">All Accounts</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <nav className="tabs">
        <button
          className={`tab ${activeTab === 'inbox' ? 'active' : ''}`}
          onClick={() => setActiveTab('inbox')}
        >
          Inbox
        </button>
        <button
          className={`tab ${activeTab === 'all' ? 'active' : ''}`}
          onClick={() => setActiveTab('all')}
        >
          All Transactions
        </button>
      </nav>

      {activeTab === 'inbox' && (
        <TransactionInbox
          accountId={selectedAccountId}
          onTransactionApproved={handleTransactionApproved}
        />
      )}

      {activeTab === 'all' && (
        <div className="all-transactions">
          {isLoading && <p>Loading transactions...</p>}
          {error && <p className="error-message">{error}</p>}
          {!isLoading && !error && transactions.length === 0 && (
            <p>No transactions found.</p>
          )}
          {!isLoading && !error && transactions.length > 0 && (
            <table className="transactions-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Payee</th>
                  <th>Amount</th>
                  <th>State</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => (
                  <tr key={tx.id}>
                    <td>{formatDate(tx.date)}</td>
                    <td>
                      {tx.payee}
                      {tx.memo && <span className="tx-memo">{tx.memo}</span>}
                    </td>
                    <td
                      className={
                        parseFloat(tx.amount) < 0 ? 'negative' : 'positive'
                      }
                    >
                      {formatCurrency(tx.amount)}
                    </td>
                    <td>
                      <span className={`state-badge state-${tx.state.toLowerCase()}`}>
                        {getStateLabel(tx.state)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <AddTransactionModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onTransactionAdded={loadData}
        preselectedAccountId={selectedAccountId}
      />
    </div>
  )
}

export default TransactionsPage
