/**
 * AccountList component.
 *
 * Displays a list of accounts with their balances and sync status.
 * Accounts linked to bank connections are grouped by bank.
 */

import React, { useEffect, useState, useMemo } from 'react'
import { CheckCircle, XCircle, Clock, Minus, RefreshCw, Building2, Trash2, MoreHorizontal } from 'lucide-react'
import { accountService } from '@/services/accountService'
import { ReconcileModal } from './ReconcileModal'
import { DeleteAccountDialog } from './DeleteAccountDialog'
import { ConnectionStatusBadge } from './ConnectionStatusBadge'
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

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
  const [deleteAccount, setDeleteAccount] = useState<Account | null>(null)
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
    } catch {
      // Error will be reflected in the account's sync_error after reload
      await loadAccounts()
    } finally {
      setRetryingAccountId(null)
    }
  }

  // Group accounts by bank connection - must be called before early returns (hooks rules)
  const groupedAccounts = useMemo(() => {
    const groups: Map<string | null, { name: string | null; health: Account['bank_connection_health']; accounts: Account[] }> = new Map()

    for (const account of accounts) {
      const connectionId = account.bank_connection_id || null
      if (!groups.has(connectionId)) {
        groups.set(connectionId, {
          name: account.bank_connection_name || null,
          health: account.bank_connection_health || null,
          accounts: [],
        })
      }
      groups.get(connectionId)!.accounts.push(account)
    }

    // Sort: manual accounts (null connection) first, then by bank name
    return Array.from(groups.entries()).sort(([aId, aGroup], [bId, bGroup]) => {
      if (aId === null) return -1
      if (bId === null) return 1
      return (aGroup.name || '').localeCompare(bGroup.name || '')
    })
  }, [accounts])

  const totalBalance = useMemo(
    () => accounts.reduce((sum, acc) => sum + parseFloat(acc.balance), 0),
    [accounts]
  )

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

  function renderAccountRow(account: Account) {
    return (
      <TableRow
        key={account.id}
        className={onAccountSelect ? 'cursor-pointer hover:bg-muted/50' : ''}
        onClick={() => onAccountSelect?.(account)}
      >
        <TableCell className="font-medium">
          <div className="flex items-center gap-2">
            {account.name}
            {account.bank_connection_health && (
              <ConnectionStatusBadge
                status={account.bank_connection_health}
                lastSyncAt={account.last_sync_at}
                className="ml-2"
              />
            )}
          </div>
        </TableCell>
        <TableCell className="text-muted-foreground">
          {getAccountTypeLabel(account.account_type)}
        </TableCell>
        <TableCell>{renderSyncStatus(account)}</TableCell>
        <TableCell className="text-right tabular-nums">
          {formatCurrency(account.balance)}
        </TableCell>
        <TableCell>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => e.stopPropagation()}
                aria-label={`Actions for ${account.name}`}
              >
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation()
                  setReconcileAccount(account)
                }}
              >
                Reconcile
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation()
                  setDeleteAccount(account)
                }}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </TableCell>
      </TableRow>
    )
  }

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
          {groupedAccounts.map(([connectionId, group]) => (
            connectionId === null ? (
              // Manual accounts - render directly
              group.accounts.map((account) => renderAccountRow(account))
            ) : (
              // Bank connection group - render with header
              <React.Fragment key={connectionId}>
                <TableRow className="bg-muted/30 hover:bg-muted/30">
                  <TableCell colSpan={5} className="py-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                      <Building2 className="h-4 w-4" />
                      <span>{group.name}</span>
                      {group.health && (
                        <ConnectionStatusBadge
                          status={group.health}
                        />
                      )}
                    </div>
                  </TableCell>
                </TableRow>
                {group.accounts.map((account) => renderAccountRow(account))}
              </React.Fragment>
            )
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

      {deleteAccount && (
        <DeleteAccountDialog
          open={deleteAccount !== null}
          onOpenChange={(open) => {
            if (!open) setDeleteAccount(null)
          }}
          account={{
            id: deleteAccount.id,
            name: deleteAccount.name,
            bank_connection_id: deleteAccount.bank_connection_id,
          }}
          onDeleted={() => {
            setDeleteAccount(null)
            loadAccounts()
            // Notify sidebar to refresh uncategorized count
            window.dispatchEvent(new Event('account-deleted'))
          }}
        />
      )}
    </Card>
  )
}

export default AccountList
