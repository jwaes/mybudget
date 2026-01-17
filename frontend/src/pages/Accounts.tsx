/**
 * Accounts page.
 *
 * Displays the list of accounts and allows creating new accounts.
 */

import { useState } from 'react'
import { AccountList } from '@/components/AccountList'
import { accountService } from '@/services/accountService'
import type { AccountType } from '@/types/account'

export function AccountsPage() {
  const [isCreating, setIsCreating] = useState(false)
  const [name, setName] = useState('')
  const [accountType, setAccountType] = useState<AccountType>('CHECKING')
  const [initialBalance, setInitialBalance] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  async function handleCreateAccount(e: React.FormEvent) {
    e.preventDefault()

    if (!name.trim()) {
      setError('Account name is required')
      return
    }

    if (!initialBalance.trim()) {
      setError('Initial balance is required')
      return
    }

    try {
      setError(null)
      await accountService.create({
        name: name.trim(),
        account_type: accountType,
        initial_balance: initialBalance,
      })

      // Reset form and refresh list
      setName('')
      setAccountType('CHECKING')
      setInitialBalance('')
      setIsCreating(false)
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create account')
    }
  }

  return (
    <div className="accounts-page">
      <header className="page-header">
        <h1>Accounts</h1>
        {!isCreating && (
          <button onClick={() => setIsCreating(true)} className="create-button">
            + New Account
          </button>
        )}
      </header>

      {isCreating && (
        <form onSubmit={handleCreateAccount} className="create-account-form">
          <h2>Create Account</h2>
          {error && <p className="error-message">{error}</p>}

          <div className="form-group">
            <label htmlFor="name">Account Name</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Main Checking"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="accountType">Account Type</label>
            <select
              id="accountType"
              value={accountType}
              onChange={(e) => setAccountType(e.target.value as AccountType)}
            >
              <option value="CHECKING">Checking</option>
              <option value="SAVINGS">Savings</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="initialBalance">Initial Balance</label>
            <input
              id="initialBalance"
              type="number"
              step="0.01"
              value={initialBalance}
              onChange={(e) => setInitialBalance(e.target.value)}
              placeholder="0.00"
            />
          </div>

          <div className="form-actions">
            <button type="submit" className="submit-button">
              Create Account
            </button>
            <button
              type="button"
              onClick={() => {
                setIsCreating(false)
                setError(null)
              }}
              className="cancel-button"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <AccountList key={refreshKey} />
    </div>
  )
}

export default AccountsPage
