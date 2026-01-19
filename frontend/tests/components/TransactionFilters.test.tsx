/**
 * Unit tests for TransactionFilters component.
 *
 * Tests filtering functionality for transactions including
 * date range, amount range, category, state, and uncategorized filter.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TransactionFilters, TransactionFiltersState } from '@/components/TransactionFilters'

const mockCategories = [
  { id: 'cat-1', name: 'Groceries' },
  { id: 'cat-2', name: 'Utilities' },
  { id: 'cat-3', name: 'Entertainment' },
]

const emptyFilters: TransactionFiltersState = {}

describe('TransactionFilters', () => {
  const defaultProps = {
    filters: emptyFilters,
    categories: mockCategories,
    onChange: vi.fn(),
    onClear: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders all filter elements', () => {
      render(<TransactionFilters {...defaultProps} />)

      // Date range inputs
      expect(screen.getByLabelText('From')).toBeInTheDocument()
      expect(screen.getByLabelText('To')).toBeInTheDocument()

      // Amount range inputs
      expect(screen.getByLabelText('Min Amount')).toBeInTheDocument()
      expect(screen.getByLabelText('Max Amount')).toBeInTheDocument()

      // Category dropdown (shadcn Select renders as combobox)
      expect(screen.getByLabelText('Category')).toBeInTheDocument()

      // State dropdown
      expect(screen.getByLabelText('Status')).toBeInTheDocument()

      // Uncategorized checkbox
      expect(screen.getByLabelText('Uncategorized only')).toBeInTheDocument()

      // Clear button
      expect(screen.getByRole('button', { name: /clear filters/i })).toBeInTheDocument()
    })

    it('renders date inputs with correct type', () => {
      render(<TransactionFilters {...defaultProps} />)

      const dateFrom = screen.getByLabelText('From')
      const dateTo = screen.getByLabelText('To')

      expect(dateFrom).toHaveAttribute('type', 'date')
      expect(dateTo).toHaveAttribute('type', 'date')
    })

    it('renders amount inputs with correct type and step', () => {
      render(<TransactionFilters {...defaultProps} />)

      const amountMin = screen.getByLabelText('Min Amount')
      const amountMax = screen.getByLabelText('Max Amount')

      expect(amountMin).toHaveAttribute('type', 'number')
      expect(amountMin).toHaveAttribute('step', '0.01')
      expect(amountMax).toHaveAttribute('type', 'number')
      expect(amountMax).toHaveAttribute('step', '0.01')
    })
  })

  describe('Category dropdown', () => {
    it('populates with provided categories', async () => {
      const user = userEvent.setup()
      render(<TransactionFilters {...defaultProps} />)

      const categorySelect = screen.getByLabelText('Category')
      await user.click(categorySelect)

      await waitFor(() => {
        expect(screen.getByRole('option', { name: 'All Categories' })).toBeInTheDocument()
        expect(screen.getByRole('option', { name: 'Groceries' })).toBeInTheDocument()
        expect(screen.getByRole('option', { name: 'Utilities' })).toBeInTheDocument()
        expect(screen.getByRole('option', { name: 'Entertainment' })).toBeInTheDocument()
      })
    })

    it('shows "All Categories" as default selection', () => {
      render(<TransactionFilters {...defaultProps} />)

      const categorySelect = screen.getByLabelText('Category')
      expect(categorySelect).toHaveTextContent('All Categories')
    })

    it('shows selected category when filter is set', () => {
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{ category_id: 'cat-2' }}
        />
      )

      const categorySelect = screen.getByLabelText('Category')
      expect(categorySelect).toHaveTextContent('Utilities')
    })
  })

  describe('State dropdown', () => {
    it('shows all state options', async () => {
      const user = userEvent.setup()
      render(<TransactionFilters {...defaultProps} />)

      const stateSelect = screen.getByLabelText('Status')
      await user.click(stateSelect)

      await waitFor(() => {
        expect(screen.getByRole('option', { name: 'All' })).toBeInTheDocument()
        expect(screen.getByRole('option', { name: 'Inbox' })).toBeInTheDocument()
        expect(screen.getByRole('option', { name: 'Approved' })).toBeInTheDocument()
        expect(screen.getByRole('option', { name: 'Cleared' })).toBeInTheDocument()
      })
    })

    it('shows "All" as default selection', () => {
      render(<TransactionFilters {...defaultProps} />)

      const stateSelect = screen.getByLabelText('Status')
      expect(stateSelect).toHaveTextContent('All')
    })

    it('shows selected state when filter is set', () => {
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{ state: 'APPROVED' }}
        />
      )

      const stateSelect = screen.getByLabelText('Status')
      expect(stateSelect).toHaveTextContent('Approved')
    })
  })

  describe('onChange callbacks', () => {
    it('calls onChange when date_from filter changes', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<TransactionFilters {...defaultProps} onChange={onChange} />)

      const dateFrom = screen.getByLabelText('From')
      await user.type(dateFrom, '2026-01-01')

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ date_from: '2026-01-01' })
      )
    })

    it('calls onChange when date_to filter changes', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<TransactionFilters {...defaultProps} onChange={onChange} />)

      const dateTo = screen.getByLabelText('To')
      await user.type(dateTo, '2026-01-31')

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ date_to: '2026-01-31' })
      )
    })

    it('calls onChange when amount_min filter changes', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<TransactionFilters {...defaultProps} onChange={onChange} />)

      const amountMin = screen.getByLabelText('Min Amount')
      // Type a single digit to verify onChange is triggered
      await user.type(amountMin, '5')

      expect(onChange).toHaveBeenCalled()
      // Check any call contains amount_min with a value
      const hasAmountMinCall = onChange.mock.calls.some(
        (call) => call[0]?.amount_min !== undefined
      )
      expect(hasAmountMinCall).toBe(true)
    })

    it('calls onChange when amount_max filter changes', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<TransactionFilters {...defaultProps} onChange={onChange} />)

      const amountMax = screen.getByLabelText('Max Amount')
      // Type a single digit to verify onChange is triggered
      await user.type(amountMax, '9')

      expect(onChange).toHaveBeenCalled()
      // Check any call contains amount_max with a value
      const hasAmountMaxCall = onChange.mock.calls.some(
        (call) => call[0]?.amount_max !== undefined
      )
      expect(hasAmountMaxCall).toBe(true)
    })

    it('calls onChange when category changes', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<TransactionFilters {...defaultProps} onChange={onChange} />)

      const categorySelect = screen.getByLabelText('Category')
      await user.click(categorySelect)

      await waitFor(() => {
        expect(screen.getByRole('option', { name: 'Groceries' })).toBeInTheDocument()
      })
      await user.click(screen.getByRole('option', { name: 'Groceries' }))

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ category_id: 'cat-1' })
      )
    })

    it('calls onChange with undefined when category is reset to All', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{ category_id: 'cat-1' }}
          onChange={onChange}
        />
      )

      const categorySelect = screen.getByLabelText('Category')
      await user.click(categorySelect)

      await waitFor(() => {
        expect(screen.getByRole('option', { name: 'All Categories' })).toBeInTheDocument()
      })
      await user.click(screen.getByRole('option', { name: 'All Categories' }))

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ category_id: undefined })
      )
    })

    it('calls onChange when state changes', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<TransactionFilters {...defaultProps} onChange={onChange} />)

      const stateSelect = screen.getByLabelText('Status')
      await user.click(stateSelect)

      await waitFor(() => {
        expect(screen.getByRole('option', { name: 'Approved' })).toBeInTheDocument()
      })
      await user.click(screen.getByRole('option', { name: 'Approved' }))

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ state: 'APPROVED' })
      )
    })

    it('calls onChange with undefined when state is reset to All', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{ state: 'INBOX' }}
          onChange={onChange}
        />
      )

      const stateSelect = screen.getByLabelText('Status')
      await user.click(stateSelect)

      await waitFor(() => {
        expect(screen.getByRole('option', { name: 'All' })).toBeInTheDocument()
      })
      await user.click(screen.getByRole('option', { name: 'All' }))

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ state: undefined })
      )
    })

    it('calls onChange when uncategorized checkbox is clicked', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<TransactionFilters {...defaultProps} onChange={onChange} />)

      const checkbox = screen.getByLabelText('Uncategorized only')
      await user.click(checkbox)

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ uncategorized_only: true })
      )
    })

    it('calls onChange with undefined when uncategorized checkbox is unchecked', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{ uncategorized_only: true }}
          onChange={onChange}
        />
      )

      const checkbox = screen.getByLabelText('Uncategorized only')
      await user.click(checkbox)

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ uncategorized_only: undefined })
      )
    })
  })

  describe('Clear Filters button', () => {
    it('is disabled when no filters are applied', () => {
      render(<TransactionFilters {...defaultProps} />)

      const clearButton = screen.getByRole('button', { name: /clear filters/i })
      expect(clearButton).toBeDisabled()
    })

    it('is enabled when filters are applied', () => {
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{ date_from: '2026-01-01' }}
        />
      )

      const clearButton = screen.getByRole('button', { name: /clear filters/i })
      expect(clearButton).not.toBeDisabled()
    })

    it('calls onClear when clicked', async () => {
      const user = userEvent.setup()
      const onClear = vi.fn()
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{ category_id: 'cat-1' }}
          onClear={onClear}
        />
      )

      const clearButton = screen.getByRole('button', { name: /clear filters/i })
      await user.click(clearButton)

      expect(onClear).toHaveBeenCalled()
    })
  })

  describe('Active filter count badge', () => {
    it('does not show badge when no filters are applied', () => {
      render(<TransactionFilters {...defaultProps} />)

      const clearButton = screen.getByRole('button', { name: /clear filters/i })
      expect(clearButton.querySelector('span')).not.toBeInTheDocument()
    })

    it('shows badge with count 1 when one filter is applied', () => {
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{ date_from: '2026-01-01' }}
        />
      )

      expect(screen.getByText('1')).toBeInTheDocument()
    })

    it('shows badge with count 2 when two filters are applied', () => {
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{ date_from: '2026-01-01', date_to: '2026-01-31' }}
        />
      )

      expect(screen.getByText('2')).toBeInTheDocument()
    })

    it('shows badge with count 3 when amount and category filters are applied', () => {
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{ amount_min: '50', amount_max: '200', category_id: 'cat-1' }}
        />
      )

      expect(screen.getByText('3')).toBeInTheDocument()
    })

    it('shows badge with count 4 when multiple filters are applied', () => {
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{
            date_from: '2026-01-01',
            category_id: 'cat-1',
            state: 'APPROVED',
            uncategorized_only: true,
          }}
        />
      )

      expect(screen.getByText('4')).toBeInTheDocument()
    })

    it('shows badge with count 7 when all filters are applied', () => {
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{
            date_from: '2026-01-01',
            date_to: '2026-01-31',
            amount_min: '50',
            amount_max: '200',
            category_id: 'cat-1',
            state: 'APPROVED',
            uncategorized_only: true,
          }}
        />
      )

      expect(screen.getByText('7')).toBeInTheDocument()
    })
  })

  describe('Filter value persistence', () => {
    it('displays existing date filter values', () => {
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{ date_from: '2026-01-15', date_to: '2026-01-20' }}
        />
      )

      expect(screen.getByLabelText('From')).toHaveValue('2026-01-15')
      expect(screen.getByLabelText('To')).toHaveValue('2026-01-20')
    })

    it('displays existing amount filter values', () => {
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{ amount_min: '100.50', amount_max: '500.00' }}
        />
      )

      expect(screen.getByLabelText('Min Amount')).toHaveValue(100.5)
      expect(screen.getByLabelText('Max Amount')).toHaveValue(500)
    })

    it('displays uncategorized checkbox as checked when filter is true', () => {
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{ uncategorized_only: true }}
        />
      )

      const checkbox = screen.getByLabelText('Uncategorized only')
      expect(checkbox).toHaveAttribute('data-state', 'checked')
    })

    it('displays uncategorized checkbox as unchecked when filter is false', () => {
      render(
        <TransactionFilters
          {...defaultProps}
          filters={{ uncategorized_only: false }}
        />
      )

      const checkbox = screen.getByLabelText('Uncategorized only')
      expect(checkbox).toHaveAttribute('data-state', 'unchecked')
    })
  })

  describe('Empty categories', () => {
    it('renders category dropdown with only All option when no categories provided', async () => {
      const user = userEvent.setup()
      render(<TransactionFilters {...defaultProps} categories={[]} />)

      const categorySelect = screen.getByLabelText('Category')
      await user.click(categorySelect)

      await waitFor(() => {
        expect(screen.getByRole('option', { name: 'All Categories' })).toBeInTheDocument()
      })

      // Only "All Categories" option should be visible
      const options = screen.getAllByRole('option')
      expect(options).toHaveLength(1)
    })
  })
})
