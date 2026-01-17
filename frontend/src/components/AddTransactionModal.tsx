/**
 * Add Transaction Modal component.
 *
 * Simple form to manually create transactions for testing purposes.
 */

import { useState, useEffect } from 'react'
import { transactionService } from '@/services/transactionService'
import { accountService } from '@/services/accountService'
import type { Account } from '@/types/account'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'

interface AddTransactionModalProps {
  isOpen: boolean
  onClose: () => void
  onTransactionAdded: () => void
  preselectedAccountId?: string
}

export function AddTransactionModal({
  isOpen,
  onClose,
  onTransactionAdded,
  preselectedAccountId,
}: AddTransactionModalProps) {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [accountId, setAccountId] = useState(preselectedAccountId || '')
  const [date, setDate] = useState(() => {
    const isoStr = new Date().toISOString()
    return isoStr.split('T')[0] ?? isoStr.substring(0, 10)
  })
  const [payee, setPayee] = useState('')
  const [amount, setAmount] = useState('')
  const [memo, setMemo] = useState('')
  const [isInflow, setIsInflow] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      loadAccounts()
      // Reset form
      const isoStr = new Date().toISOString()
      setDate(isoStr.split('T')[0] ?? isoStr.substring(0, 10))
      setPayee('')
      setAmount('')
      setMemo('')
      setIsInflow(false)
      setError(null)
      if (preselectedAccountId) {
        setAccountId(preselectedAccountId)
      }
    }
  }, [isOpen, preselectedAccountId])

  async function loadAccounts() {
    try {
      const response = await accountService.list()
      setAccounts(response.accounts)
      const firstAccount = response.accounts[0]
      if (!accountId && firstAccount) {
        setAccountId(firstAccount.id)
      }
    } catch (err) {
      console.error('Failed to load accounts:', err)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (!accountId) {
      setError('Please select an account')
      return
    }

    if (!payee.trim()) {
      setError('Please enter a payee')
      return
    }

    const parsedAmount = parseFloat(amount)
    if (isNaN(parsedAmount) || parsedAmount === 0) {
      setError('Please enter a valid amount')
      return
    }

    setIsSubmitting(true)

    try {
      // Outflows are negative, inflows are positive
      const finalAmount = isInflow ? Math.abs(parsedAmount) : -Math.abs(parsedAmount)

      await transactionService.create({
        account_id: accountId,
        date,
        payee: payee.trim(),
        amount: finalAmount.toFixed(2),
        memo: memo.trim() || null,
      })

      onTransactionAdded()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create transaction')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Add Transaction</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-4 rounded-md bg-destructive/15 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="account">Account</Label>
              <Select value={accountId} onValueChange={setAccountId}>
                <SelectTrigger id="account">
                  <SelectValue placeholder="Select account..." />
                </SelectTrigger>
                <SelectContent>
                  {accounts.map((account) => (
                    <SelectItem key={account.id} value={account.id}>
                      {account.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="date">Date</Label>
              <Input
                type="date"
                id="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="payee">Payee</Label>
              <Input
                type="text"
                id="payee"
                value={payee}
                onChange={(e) => setPayee(e.target.value)}
                placeholder="e.g., Grocery Store"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="amount">Amount</Label>
              <div className="flex gap-3 items-center">
                <div className="flex border rounded-md overflow-hidden">
                  <button
                    type="button"
                    className={cn(
                      'px-3 py-2 text-sm font-medium transition-colors',
                      !isInflow
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground hover:bg-muted/80'
                    )}
                    onClick={() => setIsInflow(false)}
                  >
                    Outflow
                  </button>
                  <button
                    type="button"
                    className={cn(
                      'px-3 py-2 text-sm font-medium transition-colors border-l',
                      isInflow
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground hover:bg-muted/80'
                    )}
                    onClick={() => setIsInflow(true)}
                  >
                    Inflow
                  </button>
                </div>
                <div className="flex-1 flex items-center border rounded-md overflow-hidden focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2">
                  <span className="px-3 py-2 bg-muted text-muted-foreground font-medium">$</span>
                  <Input
                    type="number"
                    id="amount"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="0.00"
                    step="0.01"
                    min="0"
                    required
                    className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="memo">Memo (optional)</Label>
              <Input
                type="text"
                id="memo"
                value={memo}
                onChange={(e) => setMemo(e.target.value)}
                placeholder="Optional note"
              />
            </div>
          </div>

          <DialogFooter className="mt-6">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Adding...' : 'Add Transaction'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default AddTransactionModal
