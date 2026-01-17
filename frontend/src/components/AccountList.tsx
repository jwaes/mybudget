/**
 * AccountList component.
 *
 * Displays a list of accounts with their balances.
 */

import { useEffect, useState } from 'react'
import { accountService } from '@/services/accountService'
import { ReconcileModal } from './ReconcileModal'
import type { Account } from '@/types/account'

interface AccountListProps {
  onAccountSelect?: (account: Account) => void
  onReconcileComplete?: () => void
}

export function AccountList({ onAccountSelect, onReconcileComplete }: AccountListProps) {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reconcileAccount, setReconcileAccount] = useState<Account | null>(null)

  useEffect(() => {
    loadAccounts()
  }, [])

  async function loadAccounts() {
    try {
      setIsLoading(true)
      setError(null)
      const response = await accountService.list()
      setAccounts(response.accounts)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load accounts')
    } finally {
      setIsLoading(false)
    }
  }

  function formatCurrency(amount: string): string {
    const num = parseFloat(amount)
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(num)
  }

  function getAccountTypeLabel(type: string): string {
    return type === 'CHECKING' ? 'Checking' : 'Savings'
  }

  if (isLoading) {
    return <div className="account-list loading">Loading accounts...</div>
  }

  if (error) {
    return (
      <div className="account-list error">
        <p>Error: {error}</p>
        <button onClick={loadAccounts}>Retry</button>
      </div>
    )
  }

  if (accounts.length === 0) {
    return (
      <div className="account-list empty">
        <p>No accounts yet.</p>
        <p>Create your first account to get started!</p>
      </div>
    )
  }

  return (
    <div className="account-list">
      <h2>Accounts</h2>
      <ul className="accounts">
        {accounts.map((account) => (
          <li
            key={account.id}
            className="account-item"
            onClick={() => onAccountSelect?.(account)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                onAccountSelect?.(account)
              }
            }}
          >
            <div className="account-info">
              <span className="account-name">{account.name}</span>
              <span className="account-type">
                {getAccountTypeLabel(account.account_type)}
              </span>
            </div>
            <div className="account-balance">
              {formatCurrency(account.balance)}
            </div>
            <button
              className="reconcile-button"
              onClick={(e) => {
                e.stopPropagation()
                setReconcileAccount(account)
              }}
              aria-label={`Reconcile ${account.name}`}
            >
              Reconcile
            </button>
          </li>
        ))}
      </ul>
      <div className="account-summary">
        <strong>Total:</strong>{' '}
        {formatCurrency(
          accounts.reduce((sum, acc) => sum + parseFloat(acc.balance), 0).toString()
        )}
      </div>

      <ReconcileModal
        accountId={reconcileAccount?.id || ''}
        accountName={reconcileAccount?.name || ''}
        accountBalance={reconcileAccount?.balance || '0'}
        isOpen={reconcileAccount !== null}
        onClose={() => setReconcileAccount(null)}
        onComplete={() => {
          setReconcileAccount(null)
          loadAccounts()
          onReconcileComplete?.()
        }}
      />
    </div>
  )
}

export default AccountList
