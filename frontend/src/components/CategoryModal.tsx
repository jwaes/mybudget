/**
 * Category Modal component.
 *
 * Modal dialog for creating and editing categories.
 */

import { useState, useEffect, type FormEvent } from 'react'
import type { Category, CategoryGroup, CategoryCreate, CategoryUpdate } from '@/types/category'
import { categoryService } from '@/services/categoryService'

interface CategoryModalProps {
  existingCategory?: Category | null
  groups: CategoryGroup[]
  defaultGroupId?: string
  isOpen: boolean
  onClose: () => void
  onSave: (category: Category) => void
  onDelete?: () => void
}

export function CategoryModal({
  existingCategory,
  groups,
  defaultGroupId,
  isOpen,
  onClose,
  onSave,
  onDelete,
}: CategoryModalProps) {
  const [name, setName] = useState('')
  const [groupId, setGroupId] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset form when modal opens or category changes
  useEffect(() => {
    if (isOpen) {
      if (existingCategory) {
        setName(existingCategory.name)
        setGroupId(existingCategory.group_id)
      } else {
        setName('')
        setGroupId(defaultGroupId || groups[0]?.id || '')
      }
      setError(null)
      setIsSubmitting(false)
      setIsDeleting(false)
    }
  }, [isOpen, existingCategory, defaultGroupId, groups])

  if (!isOpen) return null

  // Show message if no groups exist
  if (groups.length === 0) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <header className="modal-header">
            <h2>Create Category</h2>
            <button className="close-btn" onClick={onClose} aria-label="Close">
              &times;
            </button>
          </header>
          <div className="modal-body">
            <p className="no-groups-message">
              Please create a category group first before adding categories.
            </p>
            <div className="modal-actions">
              <button className="cancel-btn" onClick={onClose}>
                Close
              </button>
            </div>
          </div>

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
              max-width: 420px;
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

            .close-btn {
              margin-left: auto;
              background: none;
              border: none;
              font-size: 1.5rem;
              cursor: pointer;
              color: #666;
              padding: 0.25rem 0.5rem;
            }

            .modal-body {
              padding: 1.5rem;
            }

            .no-groups-message {
              color: #666;
              text-align: center;
              margin-bottom: 1.5rem;
            }

            .modal-actions {
              display: flex;
              justify-content: flex-end;
            }

            .cancel-btn {
              padding: 0.75rem 1.5rem;
              border-radius: 4px;
              font-size: 0.875rem;
              font-weight: 500;
              cursor: pointer;
              background: white;
              border: 1px solid #ccc;
              color: #666;
            }

            .cancel-btn:hover {
              background: #f5f5f5;
            }
          `}</style>
        </div>
      </div>
    )
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    const trimmedName = name.trim()
    if (!trimmedName) {
      setError('Category name is required')
      return
    }

    if (!groupId) {
      setError('Please select a category group')
      return
    }

    setIsSubmitting(true)
    try {
      let savedCategory: Category

      if (existingCategory) {
        // Update existing category
        const updateData: CategoryUpdate = {
          name: trimmedName,
          group_id: groupId,
        }
        savedCategory = await categoryService.update(existingCategory.id, updateData)
      } else {
        // Create new category
        const createData: CategoryCreate = {
          name: trimmedName,
          group_id: groupId,
        }
        savedCategory = await categoryService.create(createData)
      }

      onSave(savedCategory)
      onClose()
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to save category')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!existingCategory || !onDelete) return

    const confirmed = confirm(
      `Are you sure you want to delete "${existingCategory.name}"? This action cannot be undone.`
    )
    if (!confirmed) return

    setIsDeleting(true)
    try {
      await categoryService.delete(existingCategory.id)
      onDelete()
      onClose()
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to delete category')
      }
    } finally {
      setIsDeleting(false)
    }
  }

  const isLoading = isSubmitting || isDeleting

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>{existingCategory ? 'Edit Category' : 'Create Category'}</h2>
          <button className="close-btn" onClick={onClose} aria-label="Close">
            &times;
          </button>
        </header>

        <form onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="categoryName">Category Name</label>
            <input
              id="categoryName"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Rent, Groceries"
              disabled={isLoading}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="categoryGroup">Category Group</label>
            <select
              id="categoryGroup"
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
              disabled={isLoading}
              required
            >
              {groups.map((group) => (
                <option key={group.id} value={group.id}>
                  {group.name}
                </option>
              ))}
            </select>
          </div>

          <div className="modal-actions">
            {existingCategory && onDelete && (
              <button
                type="button"
                className="delete-btn"
                onClick={handleDelete}
                disabled={isLoading}
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            )}
            <div className="right-actions">
              <button type="button" className="cancel-btn" onClick={onClose} disabled={isLoading}>
                Cancel
              </button>
              <button type="submit" className="save-btn" disabled={isLoading}>
                {isSubmitting ? 'Saving...' : existingCategory ? 'Update' : 'Create'}
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
            max-width: 420px;
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

          .form-group input,
          .form-group select {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 1rem;
            box-sizing: border-box;
          }

          .form-group input:focus,
          .form-group select:focus {
            border-color: #0066cc;
            outline: none;
            box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
          }

          .modal-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1.5rem;
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

export default CategoryModal
