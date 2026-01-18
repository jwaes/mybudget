/**
 * TransactionInbox component.
 *
 * Displays inbox (unapproved) transactions with ability to approve them.
 */

import { useEffect, useState, useCallback } from 'react'
import { transactionService } from '@/services/transactionService'
import { categoryService } from '@/services/categoryService'
import type { Transaction } from '@/types/transaction'
import type { CategoryGroupWithCategories } from '@/types/category'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
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

  return (
    <Card>
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold">Inbox ({transactions.length})</h2>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead>Payee</TableHead>
            <TableHead className="text-right">Amount</TableHead>
            <TableHead>Category</TableHead>
            <TableHead className="w-[100px]">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {transactions.map((tx) => (
            <TableRow key={tx.id}>
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
