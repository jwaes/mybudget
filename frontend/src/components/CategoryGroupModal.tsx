/**
 * Category Group Modal component.
 *
 * Modal dialog for creating and editing category groups.
 */

import { useState, useEffect, type FormEvent } from 'react'
import type { CategoryGroup, CategoryGroupCreate, CategoryGroupUpdate } from '@/types/category'
import { categoryService } from '@/services/categoryService'
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

interface CategoryGroupModalProps {
  existingGroup?: CategoryGroup | null
  isOpen: boolean
  onClose: () => void
  onSave: (group: CategoryGroup) => void
  onDelete?: () => void
}

export function CategoryGroupModal({
  existingGroup,
  isOpen,
  onClose,
  onSave,
  onDelete,
}: CategoryGroupModalProps) {
  const [name, setName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset form when modal opens or group changes
  useEffect(() => {
    if (isOpen) {
      if (existingGroup) {
        setName(existingGroup.name)
      } else {
        setName('')
      }
      setError(null)
      setIsSubmitting(false)
      setIsDeleting(false)
    }
  }, [isOpen, existingGroup])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    const trimmedName = name.trim()
    if (!trimmedName) {
      setError('Group name is required')
      return
    }

    setIsSubmitting(true)
    try {
      let savedGroup: CategoryGroup

      if (existingGroup) {
        // Update existing group
        const updateData: CategoryGroupUpdate = {
          name: trimmedName,
        }
        savedGroup = await categoryService.updateGroup(existingGroup.id, updateData)
      } else {
        // Create new group
        const createData: CategoryGroupCreate = {
          name: trimmedName,
        }
        savedGroup = await categoryService.createGroup(createData)
      }

      onSave(savedGroup)
      onClose()
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to save category group')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!existingGroup || !onDelete) return

    const confirmed = confirm(
      `Are you sure you want to delete "${existingGroup.name}"? This will also delete all categories in this group.`
    )
    if (!confirmed) return

    setIsDeleting(true)
    try {
      await categoryService.deleteGroup(existingGroup.id)
      onDelete()
      onClose()
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to delete category group')
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
            {existingGroup ? 'Edit Category Group' : 'Create Category Group'}
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
              <Label htmlFor="groupName">Group Name</Label>
              <Input
                id="groupName"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Monthly Bills"
                disabled={isLoading}
                required
                autoFocus
              />
            </div>
          </div>

          <DialogFooter className="mt-6 flex justify-between gap-2">
            {existingGroup && onDelete && (
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
                {isSubmitting ? 'Saving...' : existingGroup ? 'Update' : 'Create'}
              </Button>
            </div>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default CategoryGroupModal
