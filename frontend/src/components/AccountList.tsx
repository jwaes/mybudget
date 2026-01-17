/**
 * AccountList component.
 *
 * Displays a list of accounts with their balances.
 */

import { useEffect, useState } from 'react'
import { accountService } from '@/services/accountService'
import { ReconcileModal } from './ReconcileModal'
import type { Account } from '@/types/account'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

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
    return (
      <Card className="p-6">
        <Skeleton className="h-6 w-32 mb-4" />
        <div className="space-y-3">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="p-6 text-center">
        <p className="text-destructive mb-4">Error: {error}</p>
        <Button onClick={loadAccounts}>Retry</Button>
      </Card>
    )
  }

  if (accounts.length === 0) {
    return (
      <Card className="p-8 text-center text-muted-foreground">
        <p className="mb-2">No accounts yet.</p>
        <p>Create your first account to get started!</p>
      </Card>
    )
  }

  const totalBalance = accounts.reduce((sum, acc) => sum + parseFloat(acc.balance), 0)

  return (
    <Card>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Account Name</TableHead>
            <TableHead>Type</TableHead>
            <TableHead className="text-right">Balance</TableHead>
            <TableHead className="w-[100px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {accounts.map((account) => (
            <TableRow
              key={account.id}
              className={onAccountSelect ? 'cursor-pointer hover:bg-muted/50' : ''}
              onClick={() => onAccountSelect?.(account)}
            >
              <TableCell className="font-medium">{account.name}</TableCell>
              <TableCell className="text-muted-foreground">
                {getAccountTypeLabel(account.account_type)}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {formatCurrency(account.balance)}
              </TableCell>
              <TableCell>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    setReconcileAccount(account)
                  }}
                  aria-label={`Reconcile ${account.name}`}
                >
                  Reconcile
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell colSpan={2} className="font-semibold">Total</TableCell>
            <TableCell className="text-right font-semibold tabular-nums">
              {formatCurrency(totalBalance.toString())}
            </TableCell>
            <TableCell></TableCell>
          </TableRow>
        </TableFooter>
      </Table>

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
    </Card>
  )
}

export default AccountList
