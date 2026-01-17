/**
 * Unit tests for CategoryModal component.
 *
 * Tests create, edit, and delete functionality for categories.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CategoryModal } from '@/components/CategoryModal'

// Mock the categoryService
vi.mock('@/services/categoryService', () => ({
  categoryService: {
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    listGroups: vi.fn(),
  },
}))

import { categoryService } from '@/services/categoryService'

const mockGroups = [
  {
    id: 'group-1',
    user_id: 'user-1',
    name: 'Monthly Bills',
    display_order: 0,
    created_at: '2026-01-17T00:00:00Z',
    updated_at: '2026-01-17T00:00:00Z',
  },
  {
    id: 'group-2',
    user_id: 'user-1',
    name: 'Savings',
    display_order: 1,
    created_at: '2026-01-17T00:00:00Z',
    updated_at: '2026-01-17T00:00:00Z',
  },
]

const mockCategory = {
  id: 'cat-1',
  user_id: 'user-1',
  group_id: 'group-1',
  name: 'Rent',
  created_at: '2026-01-17T00:00:00Z',
  updated_at: '2026-01-17T00:00:00Z',
}

describe('CategoryModal', () => {
  const defaultProps = {
    existingCategory: null,
    groups: mockGroups,
    defaultGroupId: 'group-1',
    isOpen: true,
    onClose: vi.fn(),
    onSave: vi.fn(),
    onDelete: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Create mode', () => {
    it('should display modal when isOpen is true', () => {
      render(<CategoryModal {...defaultProps} />)

      expect(screen.getByText('Create Category')).toBeInTheDocument()
    })

    it('should not display modal when isOpen is false', () => {
      render(<CategoryModal {...defaultProps} isOpen={false} />)

      expect(screen.queryByText('Create Category')).not.toBeInTheDocument()
    })

    it('should display name input field', () => {
      render(<CategoryModal {...defaultProps} />)

      expect(screen.getByLabelText('Category Name')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('e.g., Rent, Groceries')).toBeInTheDocument()
    })

    it('should display group selector with all groups', () => {
      render(<CategoryModal {...defaultProps} />)

      expect(screen.getByLabelText('Category Group')).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Monthly Bills' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Savings' })).toBeInTheDocument()
    })

    it('should pre-select defaultGroupId', () => {
      render(<CategoryModal {...defaultProps} />)

      const select = screen.getByLabelText('Category Group') as HTMLSelectElement
      expect(select.value).toBe('group-1')
    })

    it('should call onClose when close button is clicked', async () => {
      const user = userEvent.setup()
      render(<CategoryModal {...defaultProps} />)

      await user.click(screen.getByLabelText('Close'))

      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('should call onClose when Cancel button is clicked', async () => {
      const user = userEvent.setup()
      render(<CategoryModal {...defaultProps} />)

      await user.click(screen.getByText('Cancel'))

      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('should create category when form is submitted', async () => {
      const user = userEvent.setup()
      vi.mocked(categoryService.create).mockResolvedValue(mockCategory)

      render(<CategoryModal {...defaultProps} />)

      const nameInput = screen.getByLabelText('Category Name')
      await user.type(nameInput, 'Rent')

      await user.click(screen.getByText('Create'))

      await waitFor(() => {
        expect(categoryService.create).toHaveBeenCalledWith({
          name: 'Rent',
          group_id: 'group-1',
        })
      })

      expect(defaultProps.onSave).toHaveBeenCalledWith(mockCategory)
      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('should create category in selected group', async () => {
      const user = userEvent.setup()
      const categoryInGroup2 = { ...mockCategory, group_id: 'group-2' }
      vi.mocked(categoryService.create).mockResolvedValue(categoryInGroup2)

      render(<CategoryModal {...defaultProps} />)

      // Select a different group
      const groupSelect = screen.getByLabelText('Category Group')
      await user.selectOptions(groupSelect, 'group-2')

      const nameInput = screen.getByLabelText('Category Name')
      await user.type(nameInput, 'Emergency Fund')

      await user.click(screen.getByText('Create'))

      await waitFor(() => {
        expect(categoryService.create).toHaveBeenCalledWith({
          name: 'Emergency Fund',
          group_id: 'group-2',
        })
      })
    })

    it('should require name field', () => {
      render(<CategoryModal {...defaultProps} />)

      const nameInput = screen.getByLabelText('Category Name')
      expect(nameInput).toHaveAttribute('required')
    })

    it('should not submit with empty name', async () => {
      const user = userEvent.setup()
      render(<CategoryModal {...defaultProps} />)

      await user.click(screen.getByText('Create'))

      expect(categoryService.create).not.toHaveBeenCalled()
    })

    it('should display error message when create fails', async () => {
      const user = userEvent.setup()
      vi.mocked(categoryService.create).mockRejectedValue(new Error('Category already exists'))

      render(<CategoryModal {...defaultProps} />)

      const nameInput = screen.getByLabelText('Category Name')
      await user.type(nameInput, 'Rent')
      await user.click(screen.getByText('Create'))

      await waitFor(() => {
        expect(screen.getByText('Category already exists')).toBeInTheDocument()
      })
    })
  })

  describe('Edit mode', () => {
    const editProps = {
      ...defaultProps,
      existingCategory: mockCategory,
    }

    it('should display "Edit Category" title when editing', () => {
      render(<CategoryModal {...editProps} />)

      expect(screen.getByText('Edit Category')).toBeInTheDocument()
    })

    it('should pre-fill form with existing category name', () => {
      render(<CategoryModal {...editProps} />)

      const nameInput = screen.getByDisplayValue('Rent')
      expect(nameInput).toBeInTheDocument()
    })

    it('should pre-select existing category group', () => {
      render(<CategoryModal {...editProps} />)

      const select = screen.getByLabelText('Category Group') as HTMLSelectElement
      expect(select.value).toBe('group-1')
    })

    it('should show delete button when editing', () => {
      render(<CategoryModal {...editProps} />)

      expect(screen.getByText('Delete')).toBeInTheDocument()
    })

    it('should show Update button instead of Create when editing', () => {
      render(<CategoryModal {...editProps} />)

      expect(screen.getByText('Update')).toBeInTheDocument()
      expect(screen.queryByText('Create')).not.toBeInTheDocument()
    })

    it('should update category when form is submitted', async () => {
      const user = userEvent.setup()
      const updatedCategory = { ...mockCategory, name: 'Mortgage' }
      vi.mocked(categoryService.update).mockResolvedValue(updatedCategory)

      render(<CategoryModal {...editProps} />)

      const nameInput = screen.getByDisplayValue('Rent')
      await user.clear(nameInput)
      await user.type(nameInput, 'Mortgage')

      await user.click(screen.getByText('Update'))

      await waitFor(() => {
        expect(categoryService.update).toHaveBeenCalledWith('cat-1', {
          name: 'Mortgage',
          group_id: 'group-1',
        })
      })

      expect(editProps.onSave).toHaveBeenCalledWith(updatedCategory)
    })

    it('should allow moving category to different group', async () => {
      const user = userEvent.setup()
      const movedCategory = { ...mockCategory, group_id: 'group-2' }
      vi.mocked(categoryService.update).mockResolvedValue(movedCategory)

      render(<CategoryModal {...editProps} />)

      const groupSelect = screen.getByLabelText('Category Group')
      await user.selectOptions(groupSelect, 'group-2')

      await user.click(screen.getByText('Update'))

      await waitFor(() => {
        expect(categoryService.update).toHaveBeenCalledWith('cat-1', {
          name: 'Rent',
          group_id: 'group-2',
        })
      })
    })

    it('should delete category when delete button is clicked and confirmed', async () => {
      const user = userEvent.setup()
      vi.mocked(categoryService.delete).mockResolvedValue(undefined)
      vi.spyOn(window, 'confirm').mockReturnValue(true)

      render(<CategoryModal {...editProps} />)

      await user.click(screen.getByText('Delete'))

      await waitFor(() => {
        expect(categoryService.delete).toHaveBeenCalledWith('cat-1')
      })

      expect(editProps.onDelete).toHaveBeenCalled()
      expect(editProps.onClose).toHaveBeenCalled()
    })

    it('should not delete category when delete is cancelled', async () => {
      const user = userEvent.setup()
      vi.spyOn(window, 'confirm').mockReturnValue(false)

      render(<CategoryModal {...editProps} />)

      await user.click(screen.getByText('Delete'))

      expect(categoryService.delete).not.toHaveBeenCalled()
      expect(editProps.onDelete).not.toHaveBeenCalled()
    })

    it('should show confirmation dialog with category name', async () => {
      const user = userEvent.setup()
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)

      render(<CategoryModal {...editProps} />)

      await user.click(screen.getByText('Delete'))

      expect(confirmSpy).toHaveBeenCalledWith(
        'Are you sure you want to delete "Rent"? This action cannot be undone.'
      )
    })

    it('should display error message when delete fails', async () => {
      const user = userEvent.setup()
      vi.spyOn(window, 'confirm').mockReturnValue(true)
      vi.mocked(categoryService.delete).mockRejectedValue(
        new Error('Cannot delete category with transactions')
      )

      render(<CategoryModal {...editProps} />)

      await user.click(screen.getByText('Delete'))

      await waitFor(() => {
        expect(screen.getByText('Cannot delete category with transactions')).toBeInTheDocument()
      })
    })
  })

  describe('Loading states', () => {
    it('should disable submit button while saving', async () => {
      const user = userEvent.setup()
      vi.mocked(categoryService.create).mockImplementation(() => new Promise(() => {}))

      render(<CategoryModal {...defaultProps} />)

      const nameInput = screen.getByLabelText('Category Name')
      await user.type(nameInput, 'Test Category')
      await user.click(screen.getByText('Create'))

      await waitFor(() => {
        expect(screen.getByText('Saving...')).toBeInTheDocument()
        expect(screen.getByText('Saving...')).toBeDisabled()
      })
    })

    it('should disable delete button while deleting', async () => {
      const user = userEvent.setup()
      vi.spyOn(window, 'confirm').mockReturnValue(true)
      vi.mocked(categoryService.delete).mockImplementation(() => new Promise(() => {}))

      render(<CategoryModal {...defaultProps} existingCategory={mockCategory} />)

      await user.click(screen.getByText('Delete'))

      await waitFor(() => {
        expect(screen.getByText('Deleting...')).toBeInTheDocument()
        expect(screen.getByText('Deleting...')).toBeDisabled()
      })
    })
  })

  describe('No groups available', () => {
    it('should show message when no groups exist', () => {
      render(<CategoryModal {...defaultProps} groups={[]} />)

      expect(
        screen.getByText('Please create a category group first before adding categories.')
      ).toBeInTheDocument()
    })

    it('should disable form when no groups exist', () => {
      render(<CategoryModal {...defaultProps} groups={[]} />)

      expect(screen.queryByLabelText('Category Name')).not.toBeInTheDocument()
      expect(screen.queryByText('Create')).not.toBeInTheDocument()
    })
  })
})
