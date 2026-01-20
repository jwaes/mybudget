/**
 * ImportPreviewTable component.
 *
 * Displays a preview of transactions to be imported from CSV.
 */

import { AlertTriangle, Check, X } from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { PreviewTransaction } from '@/services/csvImportService'

interface ImportPreviewTableProps {
  /** Preview transactions from CSV */
  transactions: PreviewTransaction[]
  /** Row numbers that are excluded from import */
  excludedRows: Set<number>
  /** Callback when row selection changes */
  onToggleRow: (rowNumber: number) => void
  /** Callback to toggle all rows */
  onToggleAll: () => void
}

/**
 * Table showing preview of transactions to be imported.
 */
export function ImportPreviewTable({
  transactions,
  excludedRows,
  onToggleRow,
  onToggleAll,
}: ImportPreviewTableProps) {
  const allSelected = transactions.length > 0 && excludedRows.size === 0
  const someSelected =
    excludedRows.size > 0 && excludedRows.size < transactions.length

  function formatCurrency(amount: string): string {
    const num = parseFloat(amount)
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(num)
  }

  function formatDate(dateStr: string): string {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  if (transactions.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No transactions to preview
      </div>
    )
  }

  return (
    <div className="border rounded-md">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[50px]">
              <Checkbox
                checked={allSelected}
                ref={(el) => {
                  if (el && 'indeterminate' in el) {
                    (el as HTMLInputElement).indeterminate = someSelected
                  }
                }}
                onCheckedChange={onToggleAll}
                aria-label="Select all rows"
              />
            </TableHead>
            <TableHead className="w-[60px]">Row</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Payee</TableHead>
            <TableHead className="text-right">Amount</TableHead>
            <TableHead>Memo</TableHead>
            <TableHead className="w-[100px]">Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {transactions.map((tx) => {
            const isExcluded = excludedRows.has(tx.row_number)
            const amount = parseFloat(tx.amount)

            return (
              <TableRow
                key={tx.row_number}
                className={cn(
                  tx.is_duplicate && 'bg-yellow-50 dark:bg-yellow-950/20',
                  isExcluded && 'opacity-50'
                )}
              >
                <TableCell>
                  <Checkbox
                    checked={!isExcluded}
                    onCheckedChange={() => onToggleRow(tx.row_number)}
                    aria-label={`Include row ${tx.row_number}`}
                  />
                </TableCell>
                <TableCell className="text-muted-foreground text-sm">
                  {tx.row_number}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {formatDate(tx.date)}
                </TableCell>
                <TableCell>
                  <span className="font-medium">{tx.payee}</span>
                </TableCell>
                <TableCell
                  className={cn(
                    'text-right tabular-nums',
                    amount < 0 ? 'text-destructive' : 'text-green-600'
                  )}
                >
                  {formatCurrency(tx.amount)}
                </TableCell>
                <TableCell className="text-muted-foreground text-sm max-w-[150px] truncate">
                  {tx.memo || '-'}
                </TableCell>
                <TableCell>
                  {tx.is_duplicate ? (
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Badge
                            variant="outline"
                            className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-500 border-yellow-300"
                          >
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            Duplicate
                          </Badge>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{tx.duplicate_reason || 'Possible duplicate transaction'}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  ) : isExcluded ? (
                    <Badge variant="outline" className="text-muted-foreground">
                      <X className="h-3 w-3 mr-1" />
                      Skipped
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-green-600 border-green-300">
                      <Check className="h-3 w-3 mr-1" />
                      Ready
                    </Badge>
                  )}
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}

export default ImportPreviewTable
