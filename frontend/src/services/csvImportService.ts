/**
 * CSV Import service for MyBudget.
 *
 * Handles CSV file upload, preview, and import operations.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

/**
 * Amount sign mode for CSV import.
 */
export type AmountSignMode = 'negative_expense' | 'positive_expense' | 'signed'

/**
 * CSV delimiter options.
 */
export type CSVDelimiter = ',' | ';' | '\t'

/**
 * Import options for CSV file.
 */
export interface ImportOptions {
  account_id: string
  delimiter: CSVDelimiter
  date_column: string
  date_format: string
  amount_column: string
  payee_column: string
  memo_column?: string
  has_header: boolean
  amount_sign_mode: AmountSignMode
}

/**
 * Preview transaction from CSV import.
 */
export interface PreviewTransaction {
  row_number: number
  date: string
  payee: string
  amount: string
  memo: string | null
  is_duplicate: boolean
  duplicate_reason: string | null
}

/**
 * Import preview response.
 */
export interface ImportPreview {
  total_rows: number
  preview_transactions: PreviewTransaction[]
  duplicates: PreviewTransaction[]
  errors: Array<{
    row_number: number
    message: string
  }>
  columns: string[]
}

/**
 * Import result response.
 */
export interface ImportResult {
  imported_count: number
  skipped_count: number
  error_count: number
}

/**
 * CSV Import service with methods for importing transactions from CSV files.
 */
export const csvImportService = {
  /**
   * Preview a CSV import without actually importing.
   *
   * @param file - The CSV file to preview
   * @param options - Import options
   * @returns Preview of the import including duplicates and errors
   */
  async previewImport(file: File, options: ImportOptions): Promise<ImportPreview> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('account_id', options.account_id)
    formData.append('delimiter', options.delimiter)
    formData.append('date_column', options.date_column)
    formData.append('date_format', options.date_format)
    formData.append('amount_column', options.amount_column)
    formData.append('payee_column', options.payee_column)
    if (options.memo_column) {
      formData.append('memo_column', options.memo_column)
    }
    formData.append('has_header', options.has_header.toString())
    formData.append('amount_sign_mode', options.amount_sign_mode)

    const response = await fetch(`${API_BASE_URL}/import/csv/preview`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || 'Failed to preview CSV import')
    }

    return response.json()
  },

  /**
   * Execute a CSV import.
   *
   * @param file - The CSV file to import
   * @param options - Import options
   * @param excludeRows - Row numbers to exclude from import (optional)
   * @returns Import result with counts
   */
  async executeImport(
    file: File,
    options: ImportOptions,
    excludeRows?: number[]
  ): Promise<ImportResult> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('account_id', options.account_id)
    formData.append('delimiter', options.delimiter)
    formData.append('date_column', options.date_column)
    formData.append('date_format', options.date_format)
    formData.append('amount_column', options.amount_column)
    formData.append('payee_column', options.payee_column)
    if (options.memo_column) {
      formData.append('memo_column', options.memo_column)
    }
    formData.append('has_header', options.has_header.toString())
    formData.append('amount_sign_mode', options.amount_sign_mode)
    if (excludeRows && excludeRows.length > 0) {
      formData.append('exclude_rows', JSON.stringify(excludeRows))
    }

    const response = await fetch(`${API_BASE_URL}/import/csv`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || 'Failed to import CSV')
    }

    return response.json()
  },

  /**
   * Common date formats for CSV import.
   */
  DATE_FORMATS: [
    { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD (2024-01-15)' },
    { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY (01/15/2024)' },
    { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY (15/01/2024)' },
    { value: 'MM-DD-YYYY', label: 'MM-DD-YYYY (01-15-2024)' },
    { value: 'DD-MM-YYYY', label: 'DD-MM-YYYY (15-01-2024)' },
    { value: 'YYYY/MM/DD', label: 'YYYY/MM/DD (2024/01/15)' },
    { value: 'DD.MM.YYYY', label: 'DD.MM.YYYY (15.01.2024)' },
  ],

  /**
   * Auto-detect column mappings based on common column names.
   */
  autoDetectColumns(columns: string[]): Partial<{
    date_column: string
    amount_column: string
    payee_column: string
    memo_column: string
  }> {
    const lowercaseColumns = columns.map((c) => c.toLowerCase().trim())
    const result: Partial<{
      date_column: string
      amount_column: string
      payee_column: string
      memo_column: string
    }> = {}

    // Date column detection
    const datePatterns = ['date', 'datum', 'transaction_date', 'trans_date', 'posting_date']
    for (const pattern of datePatterns) {
      const idx = lowercaseColumns.findIndex((c) => c.includes(pattern))
      if (idx !== -1) {
        result.date_column = columns[idx]
        break
      }
    }

    // Amount column detection
    const amountPatterns = ['amount', 'betrag', 'value', 'sum', 'debit', 'credit']
    for (const pattern of amountPatterns) {
      const idx = lowercaseColumns.findIndex((c) => c.includes(pattern))
      if (idx !== -1) {
        result.amount_column = columns[idx]
        break
      }
    }

    // Payee column detection
    const payeePatterns = ['payee', 'description', 'merchant', 'name', 'vendor', 'recipient', 'empfanger']
    for (const pattern of payeePatterns) {
      const idx = lowercaseColumns.findIndex((c) => c.includes(pattern))
      if (idx !== -1) {
        result.payee_column = columns[idx]
        break
      }
    }

    // Memo column detection
    const memoPatterns = ['memo', 'note', 'reference', 'comment', 'verwendungszweck', 'remarks']
    for (const pattern of memoPatterns) {
      const idx = lowercaseColumns.findIndex((c) => c.includes(pattern))
      if (idx !== -1) {
        result.memo_column = columns[idx]
        break
      }
    }

    return result
  },
}

export default csvImportService
