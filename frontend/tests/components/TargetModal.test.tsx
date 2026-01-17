/**
 * Unit tests for TargetModal component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TargetModal } from '@/components/TargetModal'

// Mock the targetService
vi.mock('@/services/targetService', () => ({
  targetService: {
    createTarget: vi.fn(),
    updateTarget: vi.fn(),
    deleteTarget: vi.fn(),
  },
}))

import { targetService } from '@/services/targetService'

const mockTarget = {
  id: 'target-1',
  category_id: 'cat-1',
  category_name: 'Groceries',
  target_type: 'MONTHLY_NEEDED' as const,
  amount: '400.00',
  target_date: null,
  created_at: '2026-01-17T00:00:00Z',
  updated_at: '2026-01-17T00:00:00Z',
}

describe('TargetModal', () => {
  const defaultProps = {
    categoryId: 'cat-1',
    categoryName: 'Groceries',
    existingTarget: null,
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
      render(<TargetModal {...defaultProps} />)

      expect(screen.getByText('Set Target')).toBeInTheDocument()
      expect(screen.getByText('Groceries')).toBeInTheDocument()
    })

    it('should not display modal when isOpen is false', () => {
      render(<TargetModal {...defaultProps} isOpen={false} />)

      expect(screen.queryByText('Set Target')).not.toBeInTheDocument()
    })

    it('should display all target type options', () => {
      render(<TargetModal {...defaultProps} />)

      expect(screen.getByText('Monthly Needed')).toBeInTheDocument()
      expect(screen.getByText('Target Balance')).toBeInTheDocument()
      expect(screen.getByText('Target by Date')).toBeInTheDocument()
    })

    it('should call onClose when close button is clicked', async () => {
      const user = userEvent.setup()
      render(<TargetModal {...defaultProps} />)

      await user.click(screen.getByLabelText('Close'))

      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('should create target when form is submitted', async () => {
      const user = userEvent.setup()
      vi.mocked(targetService.createTarget).mockResolvedValue(mockTarget)

      render(<TargetModal {...defaultProps} />)

      // Enter amount
      const amountInput = screen.getByPlaceholderText('0.00')
      await user.type(amountInput, '400')

      // Submit
      await user.click(screen.getByText('Create'))

      await waitFor(() => {
        expect(targetService.createTarget).toHaveBeenCalledWith({
          category_id: 'cat-1',
          target_type: 'MONTHLY_NEEDED',
          amount: '400.00',
          target_date: undefined,
        })
      })

      expect(defaultProps.onSave).toHaveBeenCalledWith(mockTarget)
    })

    it('should validate amount with HTML5 validation', async () => {
      render(<TargetModal {...defaultProps} />)

      // Amount input should have min="0.01" and required attributes
      const amountInput = screen.getByPlaceholderText('0.00')
      expect(amountInput).toHaveAttribute('min', '0.01')
      expect(amountInput).toHaveAttribute('required')
    })

    it('should show date picker when Target by Date is selected', async () => {
      const user = userEvent.setup()
      render(<TargetModal {...defaultProps} />)

      // Click Target by Date option
      await user.click(screen.getByText('Target by Date'))

      // Date input should appear
      expect(screen.getByLabelText('Target Date')).toBeInTheDocument()
    })

    it('should have required date input for TARGET_BY_DATE', async () => {
      const user = userEvent.setup()
      render(<TargetModal {...defaultProps} />)

      // Select Target by Date
      await user.click(screen.getByText('Target by Date'))

      // Date input should have required attribute
      const dateInput = screen.getByLabelText('Target Date')
      expect(dateInput).toHaveAttribute('required')
    })
  })

  describe('Edit mode', () => {
    const editProps = {
      ...defaultProps,
      existingTarget: mockTarget,
    }

    it('should display "Edit Target" title when editing', () => {
      render(<TargetModal {...editProps} />)

      expect(screen.getByText('Edit Target')).toBeInTheDocument()
    })

    it('should pre-fill form with existing target values', () => {
      render(<TargetModal {...editProps} />)

      // Amount should be pre-filled
      const amountInput = screen.getByDisplayValue('400.00')
      expect(amountInput).toBeInTheDocument()
    })

    it('should show delete button when editing', () => {
      render(<TargetModal {...editProps} />)

      expect(screen.getByText('Delete Target')).toBeInTheDocument()
    })

    it('should update target when form is submitted', async () => {
      const user = userEvent.setup()
      const updatedTarget = { ...mockTarget, amount: '500.00' }
      vi.mocked(targetService.updateTarget).mockResolvedValue(updatedTarget)

      render(<TargetModal {...editProps} />)

      // Change amount
      const amountInput = screen.getByDisplayValue('400.00')
      await user.clear(amountInput)
      await user.type(amountInput, '500')

      // Submit
      await user.click(screen.getByText('Update'))

      await waitFor(() => {
        expect(targetService.updateTarget).toHaveBeenCalledWith('target-1', {
          target_type: 'MONTHLY_NEEDED',
          amount: '500.00',
          target_date: null,
        })
      })

      expect(editProps.onSave).toHaveBeenCalledWith(updatedTarget)
    })

    it('should delete target when delete button is clicked and confirmed', async () => {
      const user = userEvent.setup()
      vi.mocked(targetService.deleteTarget).mockResolvedValue(undefined)
      // Mock window.confirm to return true
      vi.spyOn(window, 'confirm').mockReturnValue(true)

      render(<TargetModal {...editProps} />)

      await user.click(screen.getByText('Delete Target'))

      await waitFor(() => {
        expect(targetService.deleteTarget).toHaveBeenCalledWith('target-1')
      })

      expect(editProps.onDelete).toHaveBeenCalled()
    })

    it('should not delete target when delete is cancelled', async () => {
      const user = userEvent.setup()
      // Mock window.confirm to return false
      vi.spyOn(window, 'confirm').mockReturnValue(false)

      render(<TargetModal {...editProps} />)

      await user.click(screen.getByText('Delete Target'))

      expect(targetService.deleteTarget).not.toHaveBeenCalled()
      expect(editProps.onDelete).not.toHaveBeenCalled()
    })
  })

  describe('Target types', () => {
    it('should select Monthly Needed by default', () => {
      render(<TargetModal {...defaultProps} />)

      // Monthly Needed should be checked by default (first radio)
      const monthlyOption = screen.getByText('Monthly Needed').closest('label')
      expect(monthlyOption).toHaveClass('selected')
    })

    it('should allow switching between target types', async () => {
      const user = userEvent.setup()
      render(<TargetModal {...defaultProps} />)

      // Click Target Balance
      await user.click(screen.getByText('Target Balance'))
      expect(screen.getByText('Target Balance').closest('label')).toHaveClass('selected')

      // Click Target by Date
      await user.click(screen.getByText('Target by Date'))
      expect(screen.getByText('Target by Date').closest('label')).toHaveClass('selected')
    })
  })

  describe('Error handling', () => {
    it('should display error message when createTarget fails', async () => {
      const user = userEvent.setup()
      vi.mocked(targetService.createTarget).mockRejectedValue(new Error('Network error'))

      render(<TargetModal {...defaultProps} />)

      const amountInput = screen.getByPlaceholderText('0.00')
      await user.type(amountInput, '400')
      await user.click(screen.getByText('Create'))

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument()
      })
    })
  })
})
