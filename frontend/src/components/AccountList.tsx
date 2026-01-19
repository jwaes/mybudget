/**
 * AccountList component.
 *
 * Displays a list of accounts with their balances and sync status.
 */

import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Clock, Minus, RefreshCw } from 'lucide-react'
import { accountService } from '@/services/accountService'
import { ReconcileModal } from './ReconcileModal'
import type { Account } from '@/types/account'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

interface AccountListProps {
  onAccountSelect?: (account: Account) => void
  onReconcileComplete?: () => void
}

export function AccountList({ onAccountSelect, onReconcileComplete }: AccountListProps) {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reconcileAccount, setReconcileAccount] = useState<Account | null>(null)
  const [retryingAccountId, setRetryingAccountId] = useState<string | null>(null)

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

  async function handleRetrySync(accountId: string) {
    try {
      setRetryingAccountId(accountId)
      await accountService.retrySync(accountId)
      await loadAccounts()
    } catch (err) {
      // Error will be reflected in the account's sync_error after reload
      await loadAccounts()
    } finally {
      setRetryingAccountId(null)
    }
  }

  function renderSyncStatus(account: Account) {
    const status = account.sync_status
    const isRetrying = retryingAccountId === account.id

    switch (status) {
      case 'SUCCESS':
        return (
          <div className="flex items-center gap-1.5 text-green-600" data-testid="sync-status-success">
            <CheckCircle className="h-4 w-4" />
            <span>Synced</span>
            {account.last_sync_at && (
              <span className="text-muted-foreground text-xs">
                {formatRelativeTime(account.last_sync_at)}
              </span>
            )}
          </div>
        )
      case 'FAILED':
        return (
          <div className="flex items-center gap-2" data-testid="sync-status-failed">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center gap-1.5 text-red-600 cursor-help">
                    <XCircle className="h-4 w-4" />
                    <span>Failed</span>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{account.sync_error || 'Unknown error'}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2"
              onClick={(e) => {
                e.stopPropagation()
                handleRetrySync(account.id)
              }}
              disabled={isRetrying}
              aria-label={`Retry sync for ${account.name}`}
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isRetrying ? 'animate-spin' : ''}`} />
              <span className="ml-1">Retry</span>
            </Button>
          </div>
        )
      case 'PENDING':
        return (
          <div className="flex items-center gap-1.5 text-yellow-600" data-testid="sync-status-pending">
            <Clock className="h-4 w-4" />
            <span>Pending</span>
          </div>
        )
      case 'NEVER_SYNCED':
      default:
        return (
          <div className="flex items-center gap-1.5 text-muted-foreground" data-testid="sync-status-never-synced">
            <Minus className="h-4 w-4" />
            <span>Not synced</span>
          </div>
        )
    }
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
            <TableHead>Sync Status</TableHead>
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
              <TableCell>{renderSyncStatus(account)}</TableCell>
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
            <TableCell colSpan={3} className="font-semibold">Total</TableCell>
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
