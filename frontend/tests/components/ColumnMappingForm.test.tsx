/**
 * Unit tests for ColumnMappingForm component.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ColumnMappingForm } from '@/components/ColumnMappingForm'
import type { ImportOptions } from '@/services/csvImportService'

// Mock csvImportService
vi.mock('@/services/csvImportService', () => ({
  csvImportService: {
    DATE_FORMATS: [
      { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD (2024-01-15)' },
      { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY (01/15/2024)' },
      { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY (15/01/2024)' },
    ],
    autoDetectColumns: vi.fn((columns: string[]) => {
      const result: Partial<{
        date_column: string
        amount_column: string
        payee_column: string
        memo_column: string
      }> = {}

      const lowercaseColumns = columns.map((c) => c.toLowerCase())

      if (lowercaseColumns.includes('date')) {
        result.date_column = columns[lowercaseColumns.indexOf('date')]
      }
      if (lowercaseColumns.includes('amount')) {
        result.amount_column = columns[lowercaseColumns.indexOf('amount')]
      }
      if (lowercaseColumns.includes('description')) {
        result.payee_column = columns[lowercaseColumns.indexOf('description')]
      }
      if (lowercaseColumns.includes('memo')) {
        result.memo_column = columns[lowercaseColumns.indexOf('memo')]
      }

      return result
    }),
  },
}))

const mockColumns = ['Date', 'Description', 'Amount', 'Memo', 'Category']

describe('ColumnMappingForm', () => {
  it('should render all form fields', () => {
    const onChange = vi.fn()

    render(
      <ColumnMappingForm
        columns={mockColumns}
        options={{}}
        onChange={onChange}
        autoDetect={false}
      />
    )

    // Check for delimiter select
    expect(screen.getByLabelText(/delimiter/i)).toBeInTheDocument()

    // Check for has header checkbox
    expect(screen.getByLabelText(/first row contains column headers/i)).toBeInTheDocument()

    // Check for column mapping fields
    expect(screen.getByLabelText(/date column/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/date format/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/amount column/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/amount sign mode/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/payee.*column/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/memo.*column/i)).toBeInTheDocument()
  })

  it('should auto-detect columns when enabled', () => {
    const onChange = vi.fn()

    render(
      <ColumnMappingForm
        columns={mockColumns}
        options={{}}
        onChange={onChange}
        autoDetect={true}
      />
    )

    // Should call onChange with auto-detected columns
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        date_column: 'Date',
        amount_column: 'Amount',
        payee_column: 'Description',
        memo_column: 'Memo',
      })
    )
  })

  it('should not auto-detect when autoDetect is false', () => {
    const onChange = vi.fn()

    render(
      <ColumnMappingForm
        columns={mockColumns}
        options={{}}
        onChange={onChange}
        autoDetect={false}
      />
    )

    // Should not call onChange for auto-detection
    expect(onChange).not.toHaveBeenCalled()
  })

  it('should call onChange when delimiter is changed', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    render(
      <ColumnMappingForm
        columns={mockColumns}
        options={{ delimiter: ',' }}
        onChange={onChange}
        autoDetect={false}
      />
    )

    // Click the delimiter select trigger
    const delimiterTrigger = screen.getByLabelText(/delimiter/i)
    await user.click(delimiterTrigger)

    // Select semicolon
    const semicolonOption = screen.getByRole('option', { name: /semicolon/i })
    await user.click(semicolonOption)

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        delimiter: ';',
      })
    )
  })

  it('should call onChange when has_header checkbox is toggled', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    render(
      <ColumnMappingForm
        columns={mockColumns}
        options={{ has_header: true }}
        onChange={onChange}
        autoDetect={false}
      />
    )

    const checkbox = screen.getByLabelText(/first row contains column headers/i)
    await user.click(checkbox)

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        has_header: false,
      })
    )
  })

  it('should display current options values', () => {
    const options: Partial<ImportOptions> = {
      delimiter: ';',
      has_header: true,
      date_column: 'Date',
      date_format: 'YYYY-MM-DD',
      amount_column: 'Amount',
      amount_sign_mode: 'negative_expense',
      payee_column: 'Description',
      memo_column: 'Memo',
    }

    render(
      <ColumnMappingForm
        columns={mockColumns}
        options={options}
        onChange={vi.fn()}
        autoDetect={false}
      />
    )

    // Check that has_header checkbox is checked
    const checkbox = screen.getByLabelText(/first row contains column headers/i)
    expect(checkbox).toBeChecked()
  })

  it('should show required field indicators', () => {
    render(
      <ColumnMappingForm
        columns={mockColumns}
        options={{}}
        onChange={vi.fn()}
        autoDetect={false}
      />
    )

    // Check for asterisks on required fields
    const dateColumnLabel = screen.getByText(/date column/i)
    expect(dateColumnLabel.textContent).toContain('*')

    const dateFormatLabel = screen.getByText(/date format/i)
    expect(dateFormatLabel.textContent).toContain('*')

    const amountColumnLabel = screen.getByText(/amount column/i)
    expect(amountColumnLabel.textContent).toContain('*')

    const payeeColumnLabel = screen.getByText(/payee.*column/i)
    expect(payeeColumnLabel.textContent).toContain('*')

    // Memo should not have asterisk (optional)
    const memoColumnLabel = screen.getByText(/memo.*column.*optional/i)
    expect(memoColumnLabel).toBeInTheDocument()
  })

  it('should allow selecting "None" for optional memo column', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    render(
      <ColumnMappingForm
        columns={mockColumns}
        options={{ memo_column: 'Memo' }}
        onChange={onChange}
        autoDetect={false}
      />
    )

    // Click the memo column select trigger
    const memoTrigger = screen.getByLabelText(/memo.*column/i)
    await user.click(memoTrigger)

    // Select "None"
    const noneOption = screen.getByRole('option', { name: /none/i })
    await user.click(noneOption)

    // Should be called with undefined memo_column (or no memo_column key)
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        memo_column: undefined,
      })
    )
  })
})
