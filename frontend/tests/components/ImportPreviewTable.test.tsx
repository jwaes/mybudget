/**
 * Unit tests for ImportPreviewTable component.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ImportPreviewTable } from '@/components/ImportPreviewTable'
import type { PreviewTransaction } from '@/services/csvImportService'

const mockTransactions: PreviewTransaction[] = [
  {
    row_number: 1,
    date: '2024-01-15',
    payee: 'Coffee Shop',
    amount: '-4.50',
    memo: 'Morning coffee',
    is_duplicate: false,
    duplicate_reason: null,
  },
  {
    row_number: 2,
    date: '2024-01-16',
    payee: 'Grocery Store',
    amount: '-125.00',
    memo: null,
    is_duplicate: true,
    duplicate_reason: 'Transaction with same date, payee, and amount already exists',
  },
  {
    row_number: 3,
    date: '2024-01-17',
    payee: 'Salary Deposit',
    amount: '3000.00',
    memo: 'January salary',
    is_duplicate: false,
    duplicate_reason: null,
  },
]

describe('ImportPreviewTable', () => {
  it('should render table with transactions', () => {
    render(
      <ImportPreviewTable
        transactions={mockTransactions}
        excludedRows={new Set()}
        onToggleRow={vi.fn()}
        onToggleAll={vi.fn()}
      />
    )

    // Check headers
    expect(screen.getByText('Row')).toBeInTheDocument()
    expect(screen.getByText('Date')).toBeInTheDocument()
    expect(screen.getByText('Payee')).toBeInTheDocument()
    expect(screen.getByText('Amount')).toBeInTheDocument()
    expect(screen.getByText('Memo')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()

    // Check transaction data
    expect(screen.getByText('Coffee Shop')).toBeInTheDocument()
    expect(screen.getByText('Grocery Store')).toBeInTheDocument()
    expect(screen.getByText('Salary Deposit')).toBeInTheDocument()
  })

  it('should display formatted currency amounts', () => {
    render(
      <ImportPreviewTable
        transactions={mockTransactions}
        excludedRows={new Set()}
        onToggleRow={vi.fn()}
        onToggleAll={vi.fn()}
      />
    )

    expect(screen.getByText('-$4.50')).toBeInTheDocument()
    expect(screen.getByText('-$125.00')).toBeInTheDocument()
    expect(screen.getByText('$3,000.00')).toBeInTheDocument()
  })

  it('should highlight duplicate transactions', () => {
    render(
      <ImportPreviewTable
        transactions={mockTransactions}
        excludedRows={new Set()}
        onToggleRow={vi.fn()}
        onToggleAll={vi.fn()}
      />
    )

    // Find the duplicate row (Grocery Store)
    const duplicateRow = screen.getByText('Grocery Store').closest('tr')
    expect(duplicateRow).toBeInTheDocument()
    expect(duplicateRow).toHaveClass('bg-yellow-50')

    // Should show duplicate badge
    if (duplicateRow) {
      expect(within(duplicateRow).getByText('Duplicate')).toBeInTheDocument()
    }
  })

  it('should show "Ready" status for non-duplicate transactions', () => {
    render(
      <ImportPreviewTable
        transactions={mockTransactions}
        excludedRows={new Set()}
        onToggleRow={vi.fn()}
        onToggleAll={vi.fn()}
      />
    )

    // Find the non-duplicate row (Coffee Shop)
    const coffeeRow = screen.getByText('Coffee Shop').closest('tr')
    expect(coffeeRow).toBeInTheDocument()
    if (coffeeRow) {
      expect(within(coffeeRow).getByText('Ready')).toBeInTheDocument()
    }
  })

  it('should show checkboxes for row selection', () => {
    render(
      <ImportPreviewTable
        transactions={mockTransactions}
        excludedRows={new Set()}
        onToggleRow={vi.fn()}
        onToggleAll={vi.fn()}
      />
    )

    // Check for checkbox in header (select all)
    const headerRow = screen.getAllByRole('row')[0]
    if (headerRow) {
      expect(within(headerRow).getByRole('checkbox')).toBeInTheDocument()
    }

    // Check for checkboxes in data rows
    const dataRows = screen.getAllByRole('row').slice(1)
    dataRows.forEach((row) => {
      expect(within(row).getByRole('checkbox')).toBeInTheDocument()
    })
  })

  it('should call onToggleRow when row checkbox is clicked', async () => {
    const user = userEvent.setup()
    const onToggleRow = vi.fn()

    render(
      <ImportPreviewTable
        transactions={mockTransactions}
        excludedRows={new Set()}
        onToggleRow={onToggleRow}
        onToggleAll={vi.fn()}
      />
    )

    // Click the checkbox for the first data row
    const coffeeRow = screen.getByText('Coffee Shop').closest('tr')!
    const checkbox = within(coffeeRow).getByRole('checkbox')
    await user.click(checkbox)

    expect(onToggleRow).toHaveBeenCalledWith(1)
  })

  it('should call onToggleAll when header checkbox is clicked', async () => {
    const user = userEvent.setup()
    const onToggleAll = vi.fn()

    render(
      <ImportPreviewTable
        transactions={mockTransactions}
        excludedRows={new Set()}
        onToggleRow={vi.fn()}
        onToggleAll={onToggleAll}
      />
    )

    // Click the header checkbox
    const headerRow = screen.getAllByRole('row')[0]
    expect(headerRow).toBeDefined()
    if (headerRow) {
      const headerCheckbox = within(headerRow).getByRole('checkbox')
      await user.click(headerCheckbox)
      expect(onToggleAll).toHaveBeenCalled()
    }
  })

  it('should show excluded rows as unchecked', () => {
    render(
      <ImportPreviewTable
        transactions={mockTransactions}
        excludedRows={new Set([1, 2])}
        onToggleRow={vi.fn()}
        onToggleAll={vi.fn()}
      />
    )

    // Row 1 (Coffee Shop) should be unchecked
    const coffeeRow = screen.getByText('Coffee Shop').closest('tr')!
    const coffeeCheckbox = within(coffeeRow).getByRole('checkbox')
    expect(coffeeCheckbox).not.toBeChecked()

    // Row 2 (Grocery Store) should be unchecked
    const groceryRow = screen.getByText('Grocery Store').closest('tr')!
    const groceryCheckbox = within(groceryRow).getByRole('checkbox')
    expect(groceryCheckbox).not.toBeChecked()

    // Row 3 (Salary) should be checked
    const salaryRow = screen.getByText('Salary Deposit').closest('tr')!
    const salaryCheckbox = within(salaryRow).getByRole('checkbox')
    expect(salaryCheckbox).toBeChecked()
  })

  it('should show "Skipped" status for excluded rows', () => {
    render(
      <ImportPreviewTable
        transactions={mockTransactions}
        excludedRows={new Set([1])}
        onToggleRow={vi.fn()}
        onToggleAll={vi.fn()}
      />
    )

    const coffeeRow = screen.getByText('Coffee Shop').closest('tr')!
    expect(within(coffeeRow).getByText('Skipped')).toBeInTheDocument()
  })

  it('should apply opacity to excluded rows', () => {
    render(
      <ImportPreviewTable
        transactions={mockTransactions}
        excludedRows={new Set([1])}
        onToggleRow={vi.fn()}
        onToggleAll={vi.fn()}
      />
    )

    const coffeeRow = screen.getByText('Coffee Shop').closest('tr')!
    expect(coffeeRow).toHaveClass('opacity-50')
  })

  it('should display row numbers', () => {
    render(
      <ImportPreviewTable
        transactions={mockTransactions}
        excludedRows={new Set()}
        onToggleRow={vi.fn()}
        onToggleAll={vi.fn()}
      />
    )

    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('should show empty state when no transactions', () => {
    render(
      <ImportPreviewTable
        transactions={[]}
        excludedRows={new Set()}
        onToggleRow={vi.fn()}
        onToggleAll={vi.fn()}
      />
    )

    expect(screen.getByText(/no transactions to preview/i)).toBeInTheDocument()
  })

  it('should display memo or dash for null memo', () => {
    render(
      <ImportPreviewTable
        transactions={mockTransactions}
        excludedRows={new Set()}
        onToggleRow={vi.fn()}
        onToggleAll={vi.fn()}
      />
    )

    // Coffee Shop has memo
    expect(screen.getByText('Morning coffee')).toBeInTheDocument()

    // Grocery Store has null memo - should show dash
    const groceryRow = screen.getByText('Grocery Store').closest('tr')!
    expect(within(groceryRow).getByText('-')).toBeInTheDocument()
  })

  it('should color negative amounts as destructive', () => {
    render(
      <ImportPreviewTable
        transactions={mockTransactions}
        excludedRows={new Set()}
        onToggleRow={vi.fn()}
        onToggleAll={vi.fn()}
      />
    )

    // Negative amount should have text-destructive class
    const negativeAmount = screen.getByText('-$4.50')
    expect(negativeAmount).toHaveClass('text-destructive')
  })

  it('should color positive amounts as green', () => {
    render(
      <ImportPreviewTable
        transactions={mockTransactions}
        excludedRows={new Set()}
        onToggleRow={vi.fn()}
        onToggleAll={vi.fn()}
      />
    )

    // Positive amount should have text-green-600 class
    const positiveAmount = screen.getByText('$3,000.00')
    expect(positiveAmount).toHaveClass('text-green-600')
  })
})
