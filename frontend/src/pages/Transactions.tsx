/**
 * Transactions page.
 *
 * Displays all transactions with filtering and search.
 * Supports batch approval for inbox transactions.
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
import type { CategoryGroupWithCategories } from '@/types/category'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
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
  const [categoryGroups, setCategoryGroups] = useState<CategoryGroupWithCategories[]>([])

  // Batch selection state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [batchCategory, setBatchCategory] = useState<string>('')
  const [isBatchApproving, setIsBatchApproving] = useState(false)

  // Individual category selection for approval
  const [selectedCategory, setSelectedCategory] = useState<Record<string, string>>({})

  // Load accounts and categories on mount
  useEffect(() => {
    async function loadInitialData() {
      try {
        const [accountsResponse, categoriesResponse] = await Promise.all([
          accountService.list(),
          categoryService.list(),
        ])
        setAccounts(accountsResponse.accounts)
        setCategoryGroups(categoriesResponse.groups)
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

  // Get inbox transactions for batch approval
  const inboxTransactions = transactions.filter((tx) => tx.state === 'INBOX')
  const selectedInboxIds = new Set(
    Array.from(selectedIds).filter((id) =>
      inboxTransactions.some((tx) => tx.id === id)
    )
  )

  function handleSelectAll() {
    if (selectedIds.size === inboxTransactions.length && inboxTransactions.length > 0) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(inboxTransactions.map((tx) => tx.id)))
    }
  }

  function handleSelectTransaction(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  async function handleBatchApprove() {
    if (!batchCategory || selectedInboxIds.size === 0) return

    setIsBatchApproving(true)
    setError(null)
    try {
      const result = await transactionService.batchApprove({
        transaction_ids: Array.from(selectedInboxIds),
        category_id: batchCategory,
      })

      // Reload data to reflect changes
      await loadData()
      setSelectedIds(new Set())
      setBatchCategory('')

      if (result.failed_count > 0) {
        setError(`${result.success_count} approved, ${result.failed_count} failed`)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to batch approve')
    } finally {
      setIsBatchApproving(false)
    }
  }

  const isAllSelected = selectedIds.size === inboxTransactions.length && inboxTransactions.length > 0
  const isIndeterminate = selectedIds.size > 0 && selectedIds.size < inboxTransactions.length

  function handleCategoryChange(transactionId: string, categoryId: string) {
    setSelectedCategory((prev) => ({
      ...prev,
      [transactionId]: categoryId,
    }))
  }

  async function handleApprove(transactionId: string) {
    const selection = selectedCategory[transactionId]
    if (!selection) return

    try {
      const categoryId = selection === 'READY_TO_ASSIGN' ? undefined : selection
      await transactionService.approve(transactionId, {
        category_id: categoryId,
      })
      // Reload to reflect change
      await loadData()
      // Remove from selection
      setSelectedIds((prev) => {
        const next = new Set(prev)
        next.delete(transactionId)
        return next
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve transaction')
    }
  }

  async function handleUpdateCategory(transactionId: string, categoryId: string) {
    try {
      const newCategoryId = categoryId === 'READY_TO_ASSIGN' ? null : categoryId
      await transactionService.update(transactionId, {
        category_id: newCategoryId,
      })
      // Reload to reflect change
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update category')
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
          {/* Batch controls - visible when at least one inbox transaction is selected */}
          {selectedInboxIds.size > 0 && (
            <div className="p-4 border-b bg-muted/50 flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                {selectedInboxIds.size} selected
              </span>
              <Select value={batchCategory} onValueChange={setBatchCategory}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Select category..." />
                </SelectTrigger>
                <SelectContent>
                  {categoryGroups.map((group) => (
                    <SelectGroup key={group.id}>
                      <SelectLabel>{group.name}</SelectLabel>
                      {group.categories.map((cat) => (
                        <SelectItem key={cat.id} value={cat.id}>
                          {cat.name}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  ))}
                </SelectContent>
              </Select>
              <Button
                onClick={handleBatchApprove}
                disabled={!batchCategory || isBatchApproving}
              >
                {isBatchApproving ? 'Approving...' : 'Approve Selected'}
              </Button>
              <Button variant="ghost" onClick={() => setSelectedIds(new Set())}>
                Clear Selection
              </Button>
            </div>
          )}

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px]">
                  <Checkbox
                    checked={isAllSelected}
                    ref={(el) => {
                      if (el) {
                        (el as unknown as HTMLInputElement).indeterminate = isIndeterminate
                      }
                    }}
                    onCheckedChange={handleSelectAll}
                    aria-label="Select all inbox transactions"
                    disabled={inboxTransactions.length === 0}
                  />
                </TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Payee</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[100px]">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transactions.map((tx) => {
                const isInbox = tx.state === 'INBOX'
                return (
                  <TableRow key={tx.id} data-state={selectedIds.has(tx.id) ? 'selected' : undefined}>
                    <TableCell>
                      <Checkbox
                        checked={selectedIds.has(tx.id)}
                        onCheckedChange={() => handleSelectTransaction(tx.id)}
                        aria-label={`Select transaction ${tx.payee}`}
                        disabled={!isInbox}
                      />
                    </TableCell>
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
                      {isInbox ? (
                        <Select
                          value={selectedCategory[tx.id] || ''}
                          onValueChange={(value) => handleCategoryChange(tx.id, value)}
                        >
                          <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="Select category..." />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="READY_TO_ASSIGN">Ready to Assign</SelectItem>
                            {categoryGroups.map((group) => (
                              <SelectGroup key={group.id}>
                                <SelectLabel>{group.name}</SelectLabel>
                                {group.categories.map((cat) => (
                                  <SelectItem key={cat.id} value={cat.id}>
                                    {cat.name}
                                  </SelectItem>
                                ))}
                              </SelectGroup>
                            ))}
                          </SelectContent>
                        </Select>
                      ) : (
                        <Select
                          value={tx.category_id || 'READY_TO_ASSIGN'}
                          onValueChange={(value) => handleUpdateCategory(tx.id, value)}
                        >
                          <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="Select category..." />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="READY_TO_ASSIGN">Ready to Assign</SelectItem>
                            {categoryGroups.map((group) => (
                              <SelectGroup key={group.id}>
                                <SelectLabel>{group.name}</SelectLabel>
                                {group.categories.map((cat) => (
                                  <SelectItem key={cat.id} value={cat.id}>
                                    {cat.name}
                                  </SelectItem>
                                ))}
                              </SelectGroup>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStateBadgeVariant(tx.state)}>
                        {getStateLabel(tx.state)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {isInbox && (
                        <Button
                          size="sm"
                          onClick={() => handleApprove(tx.id)}
                          disabled={!selectedCategory[tx.id]}
                        >
                          Approve
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                )
              })}
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
