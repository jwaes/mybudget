/**
 * Target Modal component.
 *
 * Modal dialog for creating and editing category spending targets.
 * Supports three target types: Monthly Needed, Target Balance, Target by Date.
 */

import { useState, useEffect, type FormEvent } from 'react'
import type { CategoryTarget, TargetType, CategoryTargetCreate, CategoryTargetUpdate } from '@/types/target'
import { targetService } from '@/services/targetService'

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

  if (!isOpen) return null

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
    return tomorrow.toISOString().split('T')[0]
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>{existingTarget ? 'Edit Target' : 'Set Target'}</h2>
          <span className="category-name-display">{categoryName}</span>
          <button className="close-btn" onClick={onClose} aria-label="Close">
            &times;
          </button>
        </header>

        <form onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label>Target Type</label>
            <div className="target-type-selector">
              {(Object.keys(TARGET_TYPE_LABELS) as TargetType[]).map((type) => (
                <label
                  key={type}
                  className={`target-type-option ${targetType === type ? 'selected' : ''}`}
                >
                  <input
                    type="radio"
                    name="targetType"
                    value={type}
                    checked={targetType === type}
                    onChange={() => setTargetType(type)}
                    disabled={isSubmitting}
                  />
                  <span className="type-label">{TARGET_TYPE_LABELS[type]}</span>
                  <span className="type-description">{TARGET_TYPE_DESCRIPTIONS[type]}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="amount">Amount</label>
            <div className="amount-input-wrapper">
              <span className="currency-symbol">€</span>
              <input
                id="amount"
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                disabled={isSubmitting}
                required
              />
            </div>
          </div>

          {targetType === 'TARGET_BY_DATE' && (
            <div className="form-group">
              <label htmlFor="targetDate">Target Date</label>
              <input
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

          <div className="modal-actions">
            {existingTarget && onDelete && (
              <button
                type="button"
                className="delete-btn"
                onClick={handleDelete}
                disabled={isSubmitting}
              >
                Delete Target
              </button>
            )}
            <div className="right-actions">
              <button type="button" className="cancel-btn" onClick={onClose} disabled={isSubmitting}>
                Cancel
              </button>
              <button type="submit" className="save-btn" disabled={isSubmitting}>
                {isSubmitting ? 'Saving...' : existingTarget ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </form>

        <style>{`
          .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
          }

          .modal-content {
            background: white;
            border-radius: 8px;
            width: 100%;
            max-width: 480px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
          }

          .modal-header {
            display: flex;
            align-items: center;
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #eee;
          }

          .modal-header h2 {
            margin: 0;
            font-size: 1.25rem;
            font-weight: 600;
          }

          .category-name-display {
            margin-left: 1rem;
            padding: 0.25rem 0.75rem;
            background: #f0f0f0;
            border-radius: 4px;
            font-size: 0.875rem;
            color: #666;
          }

          .close-btn {
            margin-left: auto;
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #666;
            padding: 0.25rem 0.5rem;
          }

          .close-btn:hover {
            color: #333;
          }

          form {
            padding: 1.5rem;
          }

          .error-message {
            background: #fee;
            color: #c00;
            padding: 0.75rem 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
            font-size: 0.875rem;
          }

          .form-group {
            margin-bottom: 1.5rem;
          }

          .form-group > label {
            display: block;
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: #333;
          }

          .target-type-selector {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
          }

          .target-type-option {
            display: flex;
            flex-direction: column;
            padding: 1rem;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s ease;
          }

          .target-type-option:hover {
            border-color: #0066cc;
          }

          .target-type-option.selected {
            border-color: #0066cc;
            background: #f0f7ff;
          }

          .target-type-option input {
            position: absolute;
            opacity: 0;
          }

          .type-label {
            font-weight: 500;
            color: #333;
            margin-bottom: 0.25rem;
          }

          .type-description {
            font-size: 0.875rem;
            color: #666;
          }

          .amount-input-wrapper {
            display: flex;
            align-items: center;
            border: 1px solid #ccc;
            border-radius: 4px;
            overflow: hidden;
          }

          .currency-symbol {
            padding: 0.75rem;
            background: #f5f5f5;
            color: #666;
            font-weight: 500;
          }

          .amount-input-wrapper input {
            flex: 1;
            padding: 0.75rem;
            border: none;
            font-size: 1rem;
            outline: none;
          }

          .amount-input-wrapper:focus-within {
            border-color: #0066cc;
            box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
          }

          input[type="date"] {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 1rem;
          }

          input[type="date"]:focus {
            border-color: #0066cc;
            outline: none;
            box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
          }

          .modal-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #eee;
          }

          .right-actions {
            display: flex;
            gap: 0.75rem;
            margin-left: auto;
          }

          .cancel-btn,
          .save-btn,
          .delete-btn {
            padding: 0.75rem 1.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s ease;
          }

          .cancel-btn {
            background: white;
            border: 1px solid #ccc;
            color: #666;
          }

          .cancel-btn:hover:not(:disabled) {
            background: #f5f5f5;
          }

          .save-btn {
            background: #0066cc;
            border: none;
            color: white;
          }

          .save-btn:hover:not(:disabled) {
            background: #0052a3;
          }

          .delete-btn {
            background: white;
            border: 1px solid #c00;
            color: #c00;
          }

          .delete-btn:hover:not(:disabled) {
            background: #fee;
          }

          button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
          }
        `}</style>
      </div>
    </div>
  )
}

export default TargetModal
