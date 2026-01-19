/**
 * TransactionInbox component.
 *
 * Displays inbox (unapproved) transactions with ability to approve them
 * individually or in batches (FR-045).
 */

import { useEffect, useState, useCallback } from 'react'
import { transactionService } from '@/services/transactionService'
import { categoryService } from '@/services/categoryService'
import type { Transaction } from '@/types/transaction'
import type { CategoryGroupWithCategories } from '@/types/category'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'

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

  // Batch approval state (FR-045)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [batchCategory, setBatchCategory] = useState<string>('')
  const [isBatchApproving, setIsBatchApproving] = useState(false)

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      const [txResponse, catResponse] = await Promise.all([
        transactionService.listInbox({ account_id: accountId }),
        categoryService.list(),
      ])
      setTransactions(txResponse.transactions)
      setCategories(catResponse.groups)
      // Clear selection when data is reloaded
      setSelectedIds(new Set())
      setBatchCategory('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setIsLoading(false)
    }
  }, [accountId])

  useEffect(() => {
    loadData()
  }, [loadData])

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
      // Also remove from selection if it was selected
      setSelectedIds((prev) => {
        const next = new Set(prev)
        next.delete(transactionId)
        return next
      })
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

  // Batch selection handlers (FR-045)
  function handleSelectAll() {
    if (selectedIds.size === transactions.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(transactions.map((tx) => tx.id)))
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
    if (!batchCategory || selectedIds.size === 0) return

    setIsBatchApproving(true)
    setError(null)
    try {
      const result = await transactionService.batchApprove({
        transaction_ids: Array.from(selectedIds),
        category_id: batchCategory,
      })

      // Remove successful transactions from the list
      const failedIdSet = new Set(result.failed_ids)
      setTransactions((prev) =>
        prev.filter((tx) => !selectedIds.has(tx.id) || failedIdSet.has(tx.id))
      )
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
        <Button onClick={loadData}>Retry</Button>
      </Card>
    )
  }

  if (transactions.length === 0) {
    return (
      <Card className="p-8 text-center text-muted-foreground">
        <p className="mb-2">No transactions in inbox.</p>
        <p>All transactions have been categorized!</p>
      </Card>
    )
  }

  const isAllSelected = selectedIds.size === transactions.length
  const isIndeterminate = selectedIds.size > 0 && selectedIds.size < transactions.length

  return (
    <Card>
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold">Inbox ({transactions.length})</h2>
      </div>

      {/* Batch controls - visible when at least one transaction is selected (FR-045) */}
      {selectedIds.size > 0 && (
        <div className="p-4 border-b bg-muted/50 flex items-center gap-4">
          <span className="text-sm text-muted-foreground">
            {selectedIds.size} selected
          </span>
          <Select value={batchCategory} onValueChange={setBatchCategory}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Select category..." />
            </SelectTrigger>
            <SelectContent>
              {/* Note: Batch approval requires a category, so "Ready to Assign" is not included */}
              {categories.map((group) => (
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
                    // Set indeterminate state via DOM API
                    (el as unknown as HTMLInputElement).indeterminate = isIndeterminate
                  }
                }}
                onCheckedChange={handleSelectAll}
                aria-label="Select all transactions"
              />
            </TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Payee</TableHead>
            <TableHead className="text-right">Amount</TableHead>
            <TableHead>Category</TableHead>
            <TableHead className="w-[100px]">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {transactions.map((tx) => (
            <TableRow key={tx.id} data-state={selectedIds.has(tx.id) ? 'selected' : undefined}>
              <TableCell>
                <Checkbox
                  checked={selectedIds.has(tx.id)}
                  onCheckedChange={() => handleSelectTransaction(tx.id)}
                  aria-label={`Select transaction ${tx.payee}`}
                />
              </TableCell>
              <TableCell className="text-muted-foreground">{formatDate(tx.date)}</TableCell>
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
                <Select
                  value={selectedCategory[tx.id] || ''}
                  onValueChange={(value) => handleCategoryChange(tx.id, value)}
                >
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Select category..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="READY_TO_ASSIGN">Ready to Assign</SelectItem>
                    {categories.map((group) => (
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
              </TableCell>
              <TableCell>
                <Button
                  size="sm"
                  onClick={() => handleApprove(tx.id)}
                  disabled={!selectedCategory[tx.id]}
                >
                  Approve
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  )
}

export default TransactionInbox
