/**
 * Transactions page.
 *
 * Displays all transactions and provides access to the inbox.
 */

import { useState, useEffect, useCallback } from 'react'
import { TransactionInbox } from '@/components/TransactionInbox'
import { CSVImport } from '@/components/CSVImport'
import { AddTransactionModal } from '@/components/AddTransactionModal'
import { transactionService } from '@/services/transactionService'
import { accountService } from '@/services/accountService'
import type { Transaction } from '@/types/transaction'
import type { Account } from '@/types/account'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

type TabType = 'inbox' | 'all'

export function TransactionsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('inbox')
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [selectedAccountId, setSelectedAccountId] = useState<string | undefined>()
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)

  // Load accounts on mount
  useEffect(() => {
    async function loadAccounts() {
      try {
        const accountsResponse = await accountService.list()
        setAccounts(accountsResponse.accounts)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load accounts')
      }
    }
    loadAccounts()
  }, [])

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

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
  }, [activeTab, selectedAccountId])

  useEffect(() => {
    loadData()
  }, [loadData])

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

  function getStateBadgeVariant(state: string): 'default' | 'secondary' | 'outline' {
    switch (state) {
      case 'CLEARED':
        return 'default'
      case 'APPROVED':
        return 'secondary'
      default:
        return 'outline'
    }
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
    <div className="p-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-foreground">Transactions</h1>
        <div className="flex items-center gap-3">
          <Button onClick={() => setIsAddModalOpen(true)}>+ Add Transaction</Button>
          {selectedAccountId && (
            <CSVImport accountId={selectedAccountId} onImportComplete={loadData} />
          )}
        </div>
      </div>

      <div className="flex items-center gap-4 mb-6">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-muted-foreground">Account:</label>
          <Select
            value={selectedAccountId || 'all'}
            onValueChange={(value) => setSelectedAccountId(value === 'all' ? undefined : value)}
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="All Accounts" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Accounts</SelectItem>
              {accounts.map((account) => (
                <SelectItem key={account.id} value={account.id}>
                  {account.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex gap-1 mb-6">
        <Button
          variant={activeTab === 'inbox' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('inbox')}
        >
          Inbox
        </Button>
        <Button
          variant={activeTab === 'all' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('all')}
        >
          All Transactions
        </Button>
      </div>

      {activeTab === 'inbox' && (
        <TransactionInbox
          accountId={selectedAccountId}
          onTransactionApproved={handleTransactionApproved}
        />
      )}

      {activeTab === 'all' && (
        <>
          {isLoading && (
            <Card className="p-6">
              <div className="space-y-3">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </div>
            </Card>
          )}
          {error && (
            <Card className="p-6 text-center">
              <p className="text-destructive mb-4">Error: {error}</p>
              <Button onClick={loadData}>Retry</Button>
            </Card>
          )}
          {!isLoading && !error && transactions.length === 0 && (
            <Card className="p-8 text-center text-muted-foreground">
              <p>No transactions found.</p>
            </Card>
          )}
          {!isLoading && !error && transactions.length > 0 && (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Payee</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>State</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {transactions.map((tx) => (
                    <TableRow key={tx.id}>
                      <TableCell className="text-muted-foreground">
                        {formatDate(tx.date)}
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{tx.payee}</div>
                        {tx.memo && (
                          <div className="text-sm text-muted-foreground">{tx.memo}</div>
                        )}
                      </TableCell>
                      <TableCell
                        className={cn(
                          'text-right tabular-nums',
                          parseFloat(tx.amount) < 0 ? 'text-destructive' : 'text-green-600'
                        )}
                      >
                        {formatCurrency(tx.amount)}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStateBadgeVariant(tx.state)}>
                          {getStateLabel(tx.state)}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </>
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
