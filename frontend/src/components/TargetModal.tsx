/**
 * Target Modal component.
 *
 * Modal dialog for creating and editing category spending targets.
 * Supports three target types: Monthly Needed, Target Balance, Target by Date.
 */

import { useState, useEffect, type FormEvent } from 'react'
import type { CategoryTarget, TargetType, CategoryTargetCreate, CategoryTargetUpdate } from '@/types/target'
import { targetService } from '@/services/targetService'
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
import { cn } from '@/lib/utils'

interface TargetModalProps {
  categoryId: string
  categoryName: string
  existingTarget?: CategoryTarget | null
  isOpen: boolean
  onClose: () => void
  onSave: (target: CategoryTarget) => void
  onDelete?: () => void
}

const TARGET_TYPE_LABELS: Record<TargetType, string> = {
  MONTHLY_NEEDED: 'Monthly Needed',
  TARGET_BALANCE: 'Target Balance',
  TARGET_BY_DATE: 'Target by Date',
}

const TARGET_TYPE_DESCRIPTIONS: Record<TargetType, string> = {
  MONTHLY_NEEDED: 'Fund this amount every month',
  TARGET_BALANCE: 'Maintain this amount available always',
  TARGET_BY_DATE: 'Reach this amount by a specific date',
}

export function TargetModal({
  categoryId,
  categoryName,
  existingTarget,
  isOpen,
  onClose,
  onSave,
  onDelete,
}: TargetModalProps) {
  const [targetType, setTargetType] = useState<TargetType>('MONTHLY_NEEDED')
  const [amount, setAmount] = useState('')
  const [targetDate, setTargetDate] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset form when modal opens or target changes
  useEffect(() => {
    if (isOpen) {
      if (existingTarget) {
        setTargetType(existingTarget.target_type)
        setAmount(existingTarget.amount)
        setTargetDate(existingTarget.target_date || '')
      } else {
        setTargetType('MONTHLY_NEEDED')
        setAmount('')
        setTargetDate('')
      }
      setError(null)
    }
  }, [isOpen, existingTarget])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validate
    const amountNum = parseFloat(amount)
    if (isNaN(amountNum) || amountNum <= 0) {
      setError('Amount must be greater than zero')
      return
    }

    if (targetType === 'TARGET_BY_DATE' && !targetDate) {
      setError('Please select a target date')
      return
    }

    setIsSubmitting(true)
    try {
      let savedTarget: CategoryTarget

      if (existingTarget) {
        // Update existing target
        const updateData: CategoryTargetUpdate = {
          target_type: targetType,
          amount: amountNum.toFixed(2),
          target_date: targetType === 'TARGET_BY_DATE' ? targetDate : null,
        }
        savedTarget = await targetService.updateTarget(existingTarget.id, updateData)
      } else {
        // Create new target
        const createData: CategoryTargetCreate = {
          category_id: categoryId,
          target_type: targetType,
          amount: amountNum.toFixed(2),
          target_date: targetType === 'TARGET_BY_DATE' ? targetDate : undefined,
        }
        savedTarget = await targetService.createTarget(createData)
      }

      onSave(savedTarget)
      onClose()
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to save target')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!existingTarget || !onDelete) return

    if (!confirm('Are you sure you want to delete this target?')) return

    setIsSubmitting(true)
    try {
      await targetService.deleteTarget(existingTarget.id)
      onDelete()
      onClose()
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to delete target')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  // Get minimum date (tomorrow)
  const getMinDate = () => {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    const isoStr = tomorrow.toISOString()
    return isoStr.split('T')[0] ?? isoStr.substring(0, 10)
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <DialogTitle>
              {existingTarget ? 'Edit Target' : 'Set Target'}
            </DialogTitle>
            <span className="px-3 py-1 bg-muted rounded text-sm text-muted-foreground">
              {categoryName}
            </span>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-4 rounded-md bg-destructive/15 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Target Type</Label>
              <div className="flex flex-col gap-3">
                {(Object.keys(TARGET_TYPE_LABELS) as TargetType[]).map((type) => (
                  <label
                    key={type}
                    className={cn(
                      'flex flex-col p-4 border-2 rounded-lg cursor-pointer transition-all',
                      targetType === type
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    )}
                  >
                    <input
                      type="radio"
                      name="targetType"
                      value={type}
                      checked={targetType === type}
                      onChange={() => setTargetType(type)}
                      disabled={isSubmitting}
                      className="sr-only"
                    />
                    <span className="font-medium text-foreground mb-1">
                      {TARGET_TYPE_LABELS[type]}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {TARGET_TYPE_DESCRIPTIONS[type]}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="amount">Amount</Label>
              <div className="flex items-center border rounded-md overflow-hidden focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2">
                <span className="px-3 py-2 bg-muted text-muted-foreground font-medium">$</span>
                <Input
                  id="amount"
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                  disabled={isSubmitting}
                  required
                  className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
                />
              </div>
            </div>

            {targetType === 'TARGET_BY_DATE' && (
              <div className="space-y-2">
                <Label htmlFor="targetDate">Target Date</Label>
                <Input
                  id="targetDate"
                  type="date"
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                  min={getMinDate()}
                  disabled={isSubmitting}
                  required
                />
              </div>
            )}
          </div>

          <DialogFooter className="mt-6 flex justify-between gap-2">
            {existingTarget && onDelete && (
              <Button
                type="button"
                variant="outline"
                className="border-destructive text-destructive hover:bg-destructive/10"
                onClick={handleDelete}
                disabled={isSubmitting}
              >
                Delete Target
              </Button>
            )}
            <div className="flex gap-2 ml-auto">
              <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Saving...' : existingTarget ? 'Update' : 'Create'}
              </Button>
            </div>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default TargetModal
