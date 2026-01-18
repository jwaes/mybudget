/**
 * Category row component for budget view.
 *
 * Displays a single category with its budget information and
 * allows editing the funded amount. Also shows target badge and
 * allows setting/editing targets.
 */

import { useState, useRef, useEffect, type KeyboardEvent } from 'react'
import type { CategoryBudget } from '@/types/budget'
import type { CategoryTarget, UnderfundedResponse } from '@/types/target'
import type { Category } from '@/types/category'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { TargetBadge } from './TargetBadge'
import { TargetModal } from './TargetModal'
import { cn } from '@/lib/utils'

interface CategoryRowProps {
  category: CategoryBudget
  target?: CategoryTarget | null
  underfunded?: UnderfundedResponse | null
  onAssign: (categoryId: string, amount: string) => Promise<void>
  onTargetChange?: (target: CategoryTarget | null) => void
  onFundUnderfunded?: (categoryId: string) => Promise<void>
  onEditCategory?: (category: Category) => void
  canFund?: boolean
}

/**
 * Format a decimal string for display (removes trailing zeros).
 */
function formatAmount(amount: string): string {
  const num = parseFloat(amount)
  if (isNaN(num)) return '0.00'
  return num.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

/**
 * Get CSS class for available amount based on value.
 */
function getAvailableClass(available: string): string {
  const num = parseFloat(available)
  if (num < 0) return 'text-destructive font-medium'
  if (num > 0) return 'text-green-600 font-medium'
  return 'text-muted-foreground'
}

export function CategoryRow({
  category,
  target,
  underfunded,
  onAssign,
  onTargetChange,
  onFundUnderfunded,
  onEditCategory,
  canFund = true,
}: CategoryRowProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isFunding, setIsFunding] = useState(false)
  const [showTargetModal, setShowTargetModal] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const underfundedAmount = underfunded?.underfunded
    ? parseFloat(underfunded.underfunded)
    : 0
  const hasUnderfunded = underfundedAmount > 0

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  const handleStartEdit = () => {
    setEditValue(formatAmount(category.funded_this_month))
    setIsEditing(true)
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    setEditValue('')
  }

  const handleSubmit = async () => {
    if (isSubmitting) return

    const newAmount = parseFloat(editValue.replace(/,/g, ''))
    const currentAmount = parseFloat(category.funded_this_month)

    if (isNaN(newAmount)) {
      handleCancelEdit()
      return
    }

    // Calculate the difference to assign
    const difference = newAmount - currentAmount

    if (difference === 0) {
      handleCancelEdit()
      return
    }

    setIsSubmitting(true)
    try {
      await onAssign(category.id, difference.toFixed(2))
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to assign funds:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSubmit()
    } else if (e.key === 'Escape') {
      handleCancelEdit()
    }
  }

  const handleTargetSave = (savedTarget: CategoryTarget) => {
    onTargetChange?.(savedTarget)
    setShowTargetModal(false)
  }

  const handleTargetDelete = () => {
    onTargetChange?.(null)
    setShowTargetModal(false)
  }

  const handleFundUnderfunded = async () => {
    if (!onFundUnderfunded || !hasUnderfunded || isFunding) return

    setIsFunding(true)
    try {
      await onFundUnderfunded(category.id)
    } catch (error) {
      console.error('Failed to fund underfunded:', error)
    } finally {
      setIsFunding(false)
    }
  }

  const handleEditCategory = () => {
    if (onEditCategory) {
      // Convert CategoryBudget to Category for editing
      const categoryData: Category = {
        id: category.id,
        user_id: '', // Not needed for editing
        group_id: '', // Will be looked up by modal
        name: category.name,
        created_at: '',
        updated_at: '',
      }
      onEditCategory(categoryData)
    }
  }

  return (
    <div className="category-row flex justify-between items-center py-3 px-4 bg-background border-b last:border-b-0">
      <div className="flex items-center gap-3">
        <button
          className="font-normal text-foreground bg-transparent border-0 cursor-pointer py-1 px-2 -my-1 -mx-2 rounded transition-colors hover:bg-muted"
          onClick={handleEditCategory}
          title="Click to edit category"
        >
          {category.name}
        </button>
        <div className="flex items-center">
          {target ? (
            <>
              <TargetBadge
                targetType={target.target_type}
                underfunded={underfunded?.underfunded}
                onClick={() => setShowTargetModal(true)}
              />
              {hasUnderfunded && onFundUnderfunded && (
                <Button
                  variant="default"
                  size="sm"
                  className="ml-2 h-6 px-2 text-xs font-medium uppercase"
                  onClick={handleFundUnderfunded}
                  disabled={isFunding || !canFund}
                  title={
                    !canFund
                      ? 'No funds available to assign'
                      : `Fund $${formatAmount(underfunded!.underfunded)}`
                  }
                >
                  {isFunding ? '...' : 'Fund'}
                </Button>
              )}
            </>
          ) : (
            <button
              className="py-0.5 px-2 border border-dashed border-muted-foreground/40 rounded-full bg-transparent text-muted-foreground text-[11px] font-medium uppercase cursor-pointer transition-all hover:border-primary hover:text-primary hover:bg-primary/5"
              onClick={() => setShowTargetModal(true)}
              title="Set target"
            >
              + Target
            </button>
          )}
        </div>
      </div>
      <div className="flex gap-8 text-right">
        <span
          className="funded-cell min-w-[100px] text-right tabular-nums cursor-pointer py-1 px-2 -my-1 -mx-2 rounded hover:bg-muted"
          data-column="funded"
          onClick={handleStartEdit}
        >
          {isEditing ? (
            <Input
              ref={inputRef}
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={handleSubmit}
              disabled={isSubmitting}
              className="w-[100px] text-right tabular-nums h-7 px-2"
              name="funded"
            />
          ) : (
            formatAmount(category.funded_this_month)
          )}
        </span>
        <span className="min-w-[100px] text-right tabular-nums text-muted-foreground" data-column="activity">
          {formatAmount(category.activity)}
        </span>
        <span className={cn('available min-w-[100px] text-right tabular-nums', getAvailableClass(category.available))} data-column="available">
          {formatAmount(category.available)}
        </span>
      </div>

      <TargetModal
        categoryId={category.id}
        categoryName={category.name}
        existingTarget={target}
        isOpen={showTargetModal}
        onClose={() => setShowTargetModal(false)}
        onSave={handleTargetSave}
        onDelete={handleTargetDelete}
      />
    </div>
  )
}

export default CategoryRow
