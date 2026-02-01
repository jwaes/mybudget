/**
 * Transactions page.
 *
 * Displays all transactions with filtering and search.
 */

import { useState, useEffect, useCallback } from 'react'
import { Upload } from 'lucide-react'
import { CSVImportDialog } from '@/components/CSVImportDialog'
import { AddTransactionModal } from '@/components/AddTransactionModal'
import { TransactionSearch } from '@/components/TransactionSearch'
import { TransactionFilters, type TransactionFiltersState } from '@/components/TransactionFilters'
import { transactionService } from '@/services/transactionService'
import { accountService } from '@/services/accountService'
import { categoryService } from '@/services/categoryService'
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

export function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [selectedAccountId, setSelectedAccountId] = useState<string | undefined>()
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState<TransactionFiltersState>({})
  const [categories, setCategories] = useState<Array<{ id: string; name: string }>>([])

  // Load accounts and categories on mount
  useEffect(() => {
    async function loadInitialData() {
      try {
        const [accountsResponse, categoriesResponse] = await Promise.all([
          accountService.list(),
          categoryService.list(),
        ])
        setAccounts(accountsResponse.accounts)
        // Flatten categories from groups for the filter dropdown
        const flatCategories = categoriesResponse.groups.flatMap((group) =>
          group.categories.map((cat) => ({ id: cat.id, name: cat.name }))
        )
        setCategories(flatCategories)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load initial data')
      }
    }
    loadInitialData()
  }, [])

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await transactionService.list({
        account_id: selectedAccountId,
        payee_search: searchQuery || undefined,
        date_from: filters.date_from,
        date_to: filters.date_to,
        amount_min: filters.amount_min,
        amount_max: filters.amount_max,
        category_id: filters.category_id,
        state: filters.state as 'INBOX' | 'APPROVED' | 'CLEARED' | undefined,
        uncategorized_only: filters.uncategorized_only,
      })
      setTransactions(response.transactions)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setIsLoading(false)
    }
  }, [selectedAccountId, searchQuery, filters])

  useEffect(() => {
    loadData()
  }, [loadData])

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
          <Button variant="outline" onClick={() => setIsImportDialogOpen(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Import CSV
          </Button>
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

      <div className="flex flex-col gap-4 mb-6">
        <div className="flex items-center gap-4">
          <TransactionSearch value={searchQuery} onChange={setSearchQuery} />
        </div>
        <TransactionFilters
          filters={filters}
          categories={categories}
          onChange={setFilters}
          onClear={() => setFilters({})}
        />
      </div>

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
                <TableHead>Status</TableHead>
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

      <AddTransactionModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onTransactionAdded={loadData}
        preselectedAccountId={selectedAccountId}
      />

      <CSVImportDialog
        isOpen={isImportDialogOpen}
        onClose={() => setIsImportDialogOpen(false)}
        onImportComplete={() => loadData()}
        accounts={accounts}
        preselectedAccountId={selectedAccountId}
      />
    </div>
  )
}

export default TransactionsPage
