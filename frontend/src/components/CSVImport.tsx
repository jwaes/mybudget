/**
 * CSVImport component.
 *
 * Allows users to upload CSV files with transactions.
 * Note: This is a placeholder for the CSV import functionality.
 * The actual CSV parsing will be done on the backend.
 */

import { useState, useRef, type ChangeEvent } from 'react'

interface CSVImportProps {
  accountId: string
  onImportComplete?: (count: number) => void
}

export function CSVImport({ accountId, onImportComplete }: CSVImportProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.csv')) {
      setError('Please select a CSV file')
      return
    }

    setIsUploading(true)
    setError(null)
    setSuccess(null)

    try {
      // For now, we'll just show a placeholder message
      // The actual import endpoint will be implemented later
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // TODO: Implement actual CSV upload
      // const formData = new FormData()
      // formData.append('file', file)
      // formData.append('account_id', accountId)
      // const response = await api.post('/transactions/import', formData)

      setSuccess(`CSV import for account ${accountId} will be available soon.`)
      onImportComplete?.(0)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import CSV')
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  function handleButtonClick() {
    fileInputRef.current?.click()
  }

  return (
    <div className="csv-import">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept=".csv"
        style={{ display: 'none' }}
        aria-label="Upload CSV file"
      />
      <button
        onClick={handleButtonClick}
        disabled={isUploading}
        className="import-button"
      >
        {isUploading ? 'Uploading...' : 'Import CSV'}
      </button>
      {error && <p className="error-message">{error}</p>}
      {success && <p className="success-message">{success}</p>}
    </div>
  )
}

export default CSVImport
