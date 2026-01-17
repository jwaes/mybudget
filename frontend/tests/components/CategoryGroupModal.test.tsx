/**
 * Unit tests for CategoryGroupModal component.
 *
 * Tests create, edit, and delete functionality for category groups.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CategoryGroupModal } from '@/components/CategoryGroupModal'

// Mock the categoryService
vi.mock('@/services/categoryService', () => ({
  categoryService: {
    createGroup: vi.fn(),
    updateGroup: vi.fn(),
    deleteGroup: vi.fn(),
  },
}))

import { categoryService } from '@/services/categoryService'

const mockGroup = {
  id: 'group-1',
  user_id: 'user-1',
  name: 'Monthly Bills',
  display_order: 0,
  created_at: '2026-01-17T00:00:00Z',
  updated_at: '2026-01-17T00:00:00Z',
}

describe('CategoryGroupModal', () => {
  const defaultProps = {
    existingGroup: null,
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
      render(<CategoryGroupModal {...defaultProps} />)

      expect(screen.getByText('Create Category Group')).toBeInTheDocument()
    })

    it('should not display modal when isOpen is false', () => {
      render(<CategoryGroupModal {...defaultProps} isOpen={false} />)

      expect(screen.queryByText('Create Category Group')).not.toBeInTheDocument()
    })

    it('should display name input field', () => {
      render(<CategoryGroupModal {...defaultProps} />)

      expect(screen.getByLabelText('Group Name')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('e.g., Monthly Bills')).toBeInTheDocument()
    })

    it('should call onClose when close button is clicked', async () => {
      const user = userEvent.setup()
      render(<CategoryGroupModal {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: 'Close' }))

      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('should call onClose when Cancel button is clicked', async () => {
      const user = userEvent.setup()
      render(<CategoryGroupModal {...defaultProps} />)

      await user.click(screen.getByText('Cancel'))

      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('should create group when form is submitted', async () => {
      const user = userEvent.setup()
      vi.mocked(categoryService.createGroup).mockResolvedValue(mockGroup)

      render(<CategoryGroupModal {...defaultProps} />)

      const nameInput = screen.getByLabelText('Group Name')
      await user.type(nameInput, 'Monthly Bills')

      await user.click(screen.getByText('Create'))

      await waitFor(() => {
        expect(categoryService.createGroup).toHaveBeenCalledWith({
          name: 'Monthly Bills',
        })
      })

      expect(defaultProps.onSave).toHaveBeenCalledWith(mockGroup)
      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('should require name field', () => {
      render(<CategoryGroupModal {...defaultProps} />)

      const nameInput = screen.getByLabelText('Group Name')
      expect(nameInput).toHaveAttribute('required')
    })

    it('should not submit with empty name', async () => {
      const user = userEvent.setup()
      render(<CategoryGroupModal {...defaultProps} />)

      // Try to submit without entering name
      await user.click(screen.getByText('Create'))

      // Service should not be called
      expect(categoryService.createGroup).not.toHaveBeenCalled()
    })

    it('should display error message when createGroup fails', async () => {
      const user = userEvent.setup()
      vi.mocked(categoryService.createGroup).mockRejectedValue(new Error('Network error'))

      render(<CategoryGroupModal {...defaultProps} />)

      const nameInput = screen.getByLabelText('Group Name')
      await user.type(nameInput, 'Test Group')
      await user.click(screen.getByText('Create'))

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument()
      })
    })

    it('should clear error when modal is closed and reopened', async () => {
      const user = userEvent.setup()
      vi.mocked(categoryService.createGroup).mockRejectedValue(new Error('Network error'))

      const { rerender } = render(<CategoryGroupModal {...defaultProps} />)

      const nameInput = screen.getByLabelText('Group Name')
      await user.type(nameInput, 'Test Group')
      await user.click(screen.getByText('Create'))

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument()
      })

      // Close and reopen
      rerender(<CategoryGroupModal {...defaultProps} isOpen={false} />)
      rerender(<CategoryGroupModal {...defaultProps} isOpen={true} />)

      expect(screen.queryByText('Network error')).not.toBeInTheDocument()
    })
  })

  describe('Edit mode', () => {
    const editProps = {
      ...defaultProps,
      existingGroup: mockGroup,
    }

    it('should display "Edit Category Group" title when editing', () => {
      render(<CategoryGroupModal {...editProps} />)

      expect(screen.getByText('Edit Category Group')).toBeInTheDocument()
    })

    it('should pre-fill form with existing group name', () => {
      render(<CategoryGroupModal {...editProps} />)

      const nameInput = screen.getByDisplayValue('Monthly Bills')
      expect(nameInput).toBeInTheDocument()
    })

    it('should show delete button when editing', () => {
      render(<CategoryGroupModal {...editProps} />)

      expect(screen.getByText('Delete')).toBeInTheDocument()
    })

    it('should show Update button instead of Create when editing', () => {
      render(<CategoryGroupModal {...editProps} />)

      expect(screen.getByText('Update')).toBeInTheDocument()
      expect(screen.queryByText('Create')).not.toBeInTheDocument()
    })

    it('should update group when form is submitted', async () => {
      const user = userEvent.setup()
      const updatedGroup = { ...mockGroup, name: 'Fixed Expenses' }
      vi.mocked(categoryService.updateGroup).mockResolvedValue(updatedGroup)

      render(<CategoryGroupModal {...editProps} />)

      const nameInput = screen.getByDisplayValue('Monthly Bills')
      await user.clear(nameInput)
      await user.type(nameInput, 'Fixed Expenses')

      await user.click(screen.getByText('Update'))

      await waitFor(() => {
        expect(categoryService.updateGroup).toHaveBeenCalledWith('group-1', {
          name: 'Fixed Expenses',
        })
      })

      expect(editProps.onSave).toHaveBeenCalledWith(updatedGroup)
    })

    it('should delete group when delete button is clicked and confirmed', async () => {
      const user = userEvent.setup()
      vi.mocked(categoryService.deleteGroup).mockResolvedValue(undefined)
      vi.spyOn(window, 'confirm').mockReturnValue(true)

      render(<CategoryGroupModal {...editProps} />)

      await user.click(screen.getByText('Delete'))

      await waitFor(() => {
        expect(categoryService.deleteGroup).toHaveBeenCalledWith('group-1')
      })

      expect(editProps.onDelete).toHaveBeenCalled()
      expect(editProps.onClose).toHaveBeenCalled()
    })

    it('should not delete group when delete is cancelled', async () => {
      const user = userEvent.setup()
      vi.spyOn(window, 'confirm').mockReturnValue(false)

      render(<CategoryGroupModal {...editProps} />)

      await user.click(screen.getByText('Delete'))

      expect(categoryService.deleteGroup).not.toHaveBeenCalled()
      expect(editProps.onDelete).not.toHaveBeenCalled()
    })

    it('should show confirmation dialog with group name', async () => {
      const user = userEvent.setup()
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)

      render(<CategoryGroupModal {...editProps} />)

      await user.click(screen.getByText('Delete'))

      expect(confirmSpy).toHaveBeenCalledWith(
        'Are you sure you want to delete "Monthly Bills"? This will also delete all categories in this group.'
      )
    })

    it('should display error message when deleteGroup fails', async () => {
      const user = userEvent.setup()
      vi.spyOn(window, 'confirm').mockReturnValue(true)
      vi.mocked(categoryService.deleteGroup).mockRejectedValue(new Error('Cannot delete'))

      render(<CategoryGroupModal {...editProps} />)

      await user.click(screen.getByText('Delete'))

      await waitFor(() => {
        expect(screen.getByText('Cannot delete')).toBeInTheDocument()
      })
    })
  })

  describe('Loading states', () => {
    it('should disable submit button while saving', async () => {
      const user = userEvent.setup()
      // Create a promise that never resolves to keep loading state
      vi.mocked(categoryService.createGroup).mockImplementation(
        () => new Promise(() => {})
      )

      render(<CategoryGroupModal {...defaultProps} />)

      const nameInput = screen.getByLabelText('Group Name')
      await user.type(nameInput, 'Test Group')
      await user.click(screen.getByText('Create'))

      await waitFor(() => {
        expect(screen.getByText('Saving...')).toBeInTheDocument()
        expect(screen.getByText('Saving...')).toBeDisabled()
      })
    })

    it('should disable delete button while deleting', async () => {
      const user = userEvent.setup()
      vi.spyOn(window, 'confirm').mockReturnValue(true)
      vi.mocked(categoryService.deleteGroup).mockImplementation(
        () => new Promise(() => {})
      )

      render(<CategoryGroupModal {...defaultProps} existingGroup={mockGroup} />)

      await user.click(screen.getByText('Delete'))

      await waitFor(() => {
        expect(screen.getByText('Deleting...')).toBeInTheDocument()
        expect(screen.getByText('Deleting...')).toBeDisabled()
      })
    })
  })
})
