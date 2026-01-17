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
import { TargetBadge } from './TargetBadge'
import { TargetModal } from './TargetModal'

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
  if (num < 0) return 'negative'
  if (num > 0) return 'positive'
  return 'zero'
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
    <div className="category-row">
      <div className="category-info">
        <button
          className="category-name-button"
          onClick={handleEditCategory}
          title="Click to edit category"
        >
          {category.name}
        </button>
        <div className="category-target">
          {target ? (
            <>
              <TargetBadge
                targetType={target.target_type}
                underfunded={underfunded?.underfunded}
                onClick={() => setShowTargetModal(true)}
              />
              {hasUnderfunded && onFundUnderfunded && (
                <button
                  className="fund-category-btn"
                  onClick={handleFundUnderfunded}
                  disabled={isFunding || !canFund}
                  title={
                    !canFund
                      ? 'No funds available to assign'
                      : `Fund $${formatAmount(underfunded!.underfunded)}`
                  }
                >
                  {isFunding ? '...' : 'Fund'}
                </button>
              )}
            </>
          ) : (
            <button
              className="set-target-btn"
              onClick={() => setShowTargetModal(true)}
              title="Set target"
            >
              + Target
            </button>
          )}
        </div>
      </div>
      <div className="category-amounts">
        <span className="funded" onClick={handleStartEdit}>
          {isEditing ? (
            <input
              ref={inputRef}
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={handleSubmit}
              disabled={isSubmitting}
              className="funded-input"
            />
          ) : (
            formatAmount(category.funded_this_month)
          )}
        </span>
        <span className="activity">{formatAmount(category.activity)}</span>
        <span className={`available ${getAvailableClass(category.available)}`}>
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

      <style>{`
        .category-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.75rem 1rem;
          background: white;
          border-bottom: 1px solid #eee;
        }

        .category-row:last-child {
          border-bottom: none;
        }

        .category-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .category-name-button {
          font-weight: 400;
          color: #333;
          background: none;
          border: none;
          cursor: pointer;
          padding: 0.25rem 0.5rem;
          margin: -0.25rem -0.5rem;
          border-radius: 4px;
          font-size: inherit;
          font-family: inherit;
          text-align: left;
          transition: background-color 0.15s;
        }

        .category-name-button:hover {
          background-color: rgba(0, 0, 0, 0.05);
        }

        .category-target {
          display: flex;
          align-items: center;
        }

        .set-target-btn {
          padding: 0.125rem 0.5rem;
          border: 1px dashed #ccc;
          border-radius: 12px;
          background: none;
          color: #999;
          font-size: 0.6875rem;
          font-weight: 500;
          text-transform: uppercase;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .set-target-btn:hover {
          border-color: #0066cc;
          color: #0066cc;
          background: #f0f7ff;
        }

        .fund-category-btn {
          margin-left: 0.5rem;
          padding: 0.125rem 0.5rem;
          border: none;
          border-radius: 4px;
          background-color: #0066cc;
          color: white;
          font-size: 0.6875rem;
          font-weight: 500;
          text-transform: uppercase;
          cursor: pointer;
          transition: background-color 0.15s ease;
        }

        .fund-category-btn:hover:not(:disabled) {
          background-color: #0055aa;
        }

        .fund-category-btn:disabled {
          background-color: #ccc;
          cursor: not-allowed;
        }

        .category-amounts {
          display: flex;
          gap: 2rem;
          text-align: right;
        }

        .funded,
        .activity,
        .available {
          min-width: 100px;
          text-align: right;
          font-variant-numeric: tabular-nums;
        }

        .funded {
          cursor: pointer;
          padding: 0.25rem 0.5rem;
          margin: -0.25rem -0.5rem;
          border-radius: 4px;
        }

        .funded:hover {
          background-color: #f0f0f0;
        }

        .funded-input {
          width: 100px;
          text-align: right;
          padding: 0.25rem 0.5rem;
          border: 1px solid #0066cc;
          border-radius: 4px;
          font-size: inherit;
          font-family: inherit;
          font-variant-numeric: tabular-nums;
        }

        .activity {
          color: #666;
        }

        .available.positive {
          color: #22a722;
          font-weight: 500;
        }

        .available.negative {
          color: #c00;
          font-weight: 500;
        }

        .available.zero {
          color: #666;
        }
      `}</style>
    </div>
  )
}

export default CategoryRow
