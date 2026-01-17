/**
 * Category Modal component.
 *
 * Modal dialog for creating and editing categories.
 */

import { useState, useEffect, type FormEvent } from 'react'
import type { Category, CategoryGroup, CategoryCreate, CategoryUpdate } from '@/types/category'
import { categoryService } from '@/services/categoryService'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
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

  // Show message if no groups exist
  if (groups.length === 0 && isOpen) {
    return (
      <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Create Category</DialogTitle>
            <DialogDescription className="text-center py-4">
              Please create a category group first before adding categories.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
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
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>
            {existingCategory ? 'Edit Category' : 'Create Category'}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-4 rounded-md bg-destructive/15 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="categoryName">Category Name</Label>
              <Input
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

            <div className="space-y-2">
              <Label htmlFor="categoryGroup">Category Group</Label>
              <Select
                value={groupId}
                onValueChange={setGroupId}
                disabled={isLoading}
              >
                <SelectTrigger id="categoryGroup">
                  <SelectValue placeholder="Select a group..." />
                </SelectTrigger>
                <SelectContent>
                  {groups.map((group) => (
                    <SelectItem key={group.id} value={group.id}>
                      {group.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter className="mt-6 flex justify-between gap-2">
            {existingCategory && onDelete && (
              <Button
                type="button"
                variant="outline"
                className="border-destructive text-destructive hover:bg-destructive/10"
                onClick={handleDelete}
                disabled={isLoading}
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </Button>
            )}
            <div className="flex gap-2 ml-auto">
              <Button type="button" variant="outline" onClick={onClose} disabled={isLoading}>
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isSubmitting ? 'Saving...' : existingCategory ? 'Update' : 'Create'}
              </Button>
            </div>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default CategoryModal
