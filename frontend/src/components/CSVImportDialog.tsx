/**
 * CSVImportDialog component.
 *
 * Multi-step dialog for importing transactions from CSV files.
 */

import { useState, useCallback, useRef } from 'react'
import { Upload, FileSpreadsheet, Settings, Eye, CheckCircle2, Loader2, AlertCircle } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ColumnMappingForm } from './ColumnMappingForm'
import { ImportPreviewTable } from './ImportPreviewTable'
import { useToast } from '@/components/Toast'
import {
  csvImportService,
  type ImportOptions,
  type ImportPreview,
  type ImportResult,
} from '@/services/csvImportService'
import type { Account } from '@/types/account'
import { cn } from '@/lib/utils'

type ImportStep = 'upload' | 'mapping' | 'preview' | 'result'

interface CSVImportDialogProps {
  /** Whether the dialog is open */
  isOpen: boolean
  /** Callback when dialog should close */
  onClose: () => void
  /** Callback when import completes successfully */
  onImportComplete?: (result: ImportResult) => void
  /** List of accounts for selection */
  accounts: Account[]
  /** Pre-selected account ID */
  preselectedAccountId?: string
}

const STEPS: { key: ImportStep; label: string; icon: React.ReactNode }[] = [
  { key: 'upload', label: 'Upload', icon: <Upload className="h-4 w-4" /> },
  { key: 'mapping', label: 'Configure', icon: <Settings className="h-4 w-4" /> },
  { key: 'preview', label: 'Preview', icon: <Eye className="h-4 w-4" /> },
  { key: 'result', label: 'Done', icon: <CheckCircle2 className="h-4 w-4" /> },
]

/**
 * Multi-step dialog for CSV import.
 */
export function CSVImportDialog({
  isOpen,
  onClose,
  onImportComplete,
  accounts,
  preselectedAccountId,
}: CSVImportDialogProps) {
  const [step, setStep] = useState<ImportStep>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [accountId, setAccountId] = useState(preselectedAccountId || '')
  const [options, setOptions] = useState<Partial<ImportOptions>>({
    delimiter: ',',
    has_header: true,
    amount_sign_mode: 'signed',
  })
  const [columns, setColumns] = useState<string[]>([])
  const [preview, setPreview] = useState<ImportPreview | null>(null)
  const [excludedRows, setExcludedRows] = useState<Set<number>>(new Set())
  const [result, setResult] = useState<ImportResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const { showSuccess, showError } = useToast()

  const resetState = useCallback(() => {
    setStep('upload')
    setFile(null)
    setAccountId(preselectedAccountId || '')
    setOptions({
      delimiter: ',',
      has_header: true,
      amount_sign_mode: 'signed',
    })
    setColumns([])
    setPreview(null)
    setExcludedRows(new Set())
    setResult(null)
    setError(null)
  }, [preselectedAccountId])

  const handleClose = useCallback(() => {
    resetState()
    onClose()
  }, [resetState, onClose])

  const handleFileSelect = useCallback((selectedFile: File) => {
    if (!selectedFile.name.endsWith('.csv')) {
      setError('Please select a CSV file')
      return
    }

    setFile(selectedFile)
    setError(null)

    // Read first few lines to get columns
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      const lines = text.split('\n')
      const firstLine = lines[0]
      if (firstLine) {
        // Try to detect delimiter
        let delimiter: ',' | ';' | '\t' = ','
        if (firstLine.includes(';') && !firstLine.includes(',')) {
          delimiter = ';'
        } else if (firstLine.includes('\t') && !firstLine.includes(',')) {
          delimiter = '\t'
        }

        // Parse columns from first line
        const cols = firstLine.split(delimiter).map((c) => c.trim().replace(/^["']|["']$/g, ''))
        setColumns(cols)
        setOptions((prev) => ({ ...prev, delimiter }))
      }
    }
    reader.readAsText(selectedFile)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile) {
        handleFileSelect(droppedFile)
      }
    },
    [handleFileSelect]
  )

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0]
      if (selectedFile) {
        handleFileSelect(selectedFile)
      }
    },
    [handleFileSelect]
  )

  const handlePreview = useCallback(async () => {
    if (!file || !accountId) return

    const completeOptions: ImportOptions = {
      account_id: accountId,
      delimiter: options.delimiter || ',',
      date_column: options.date_column || '',
      date_format: options.date_format || 'YYYY-MM-DD',
      amount_column: options.amount_column || '',
      payee_column: options.payee_column || '',
      memo_column: options.memo_column,
      has_header: options.has_header !== false,
      amount_sign_mode: options.amount_sign_mode || 'signed',
    }

    try {
      setIsLoading(true)
      setError(null)
      const previewResult = await csvImportService.previewImport(file, completeOptions)
      setPreview(previewResult)

      // Auto-exclude duplicates
      const duplicateRows = new Set(
        previewResult.preview_transactions
          .filter((tx) => tx.is_duplicate)
          .map((tx) => tx.row_number)
      )
      setExcludedRows(duplicateRows)

      setStep('preview')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to preview import'
      setError(message)
      showError(message)
    } finally {
      setIsLoading(false)
    }
  }, [file, accountId, options, showError])

  const handleImport = useCallback(async () => {
    if (!file || !accountId || !preview) return

    const completeOptions: ImportOptions = {
      account_id: accountId,
      delimiter: options.delimiter || ',',
      date_column: options.date_column || '',
      date_format: options.date_format || 'YYYY-MM-DD',
      amount_column: options.amount_column || '',
      payee_column: options.payee_column || '',
      memo_column: options.memo_column,
      has_header: options.has_header !== false,
      amount_sign_mode: options.amount_sign_mode || 'signed',
    }

    try {
      setIsLoading(true)
      setError(null)
      const importResult = await csvImportService.executeImport(
        file,
        completeOptions,
        Array.from(excludedRows)
      )
      setResult(importResult)
      setStep('result')
      showSuccess(`Successfully imported ${importResult.imported_count} transactions`)
      onImportComplete?.(importResult)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to import'
      setError(message)
      showError(message)
    } finally {
      setIsLoading(false)
    }
  }, [file, accountId, options, preview, excludedRows, showSuccess, showError, onImportComplete])

  const handleToggleRow = useCallback((rowNumber: number) => {
    setExcludedRows((prev) => {
      const next = new Set(prev)
      if (next.has(rowNumber)) {
        next.delete(rowNumber)
      } else {
        next.add(rowNumber)
      }
      return next
    })
  }, [])

  const handleToggleAll = useCallback(() => {
    if (!preview) return
    if (excludedRows.size === 0) {
      // Exclude all
      setExcludedRows(new Set(preview.preview_transactions.map((tx) => tx.row_number)))
    } else {
      // Include all
      setExcludedRows(new Set())
    }
  }, [preview, excludedRows])

  const canProceedFromUpload = file && accountId
  const canProceedFromMapping =
    options.date_column && options.date_format && options.amount_column && options.payee_column

  const currentStepIndex = STEPS.findIndex((s) => s.key === step)

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Import Transactions from CSV</DialogTitle>
          <DialogDescription>
            Upload a CSV file and configure how columns should be mapped.
          </DialogDescription>
        </DialogHeader>

        {/* Step indicator */}
        <div className="flex justify-between mb-6">
          {STEPS.map((s, idx) => (
            <div
              key={s.key}
              className={cn(
                'flex items-center gap-2 text-sm',
                idx <= currentStepIndex ? 'text-primary' : 'text-muted-foreground'
              )}
            >
              <div
                className={cn(
                  'flex items-center justify-center w-8 h-8 rounded-full border-2',
                  idx < currentStepIndex
                    ? 'bg-primary text-primary-foreground border-primary'
                    : idx === currentStepIndex
                      ? 'border-primary text-primary'
                      : 'border-muted text-muted-foreground'
                )}
              >
                {idx < currentStepIndex ? <CheckCircle2 className="h-4 w-4" /> : s.icon}
              </div>
              <span className="hidden sm:inline">{s.label}</span>
            </div>
          ))}
        </div>

        {/* Error display */}
        {error && (
          <div className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive mb-4">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* Step content */}
        <div className="min-h-[300px]">
          {step === 'upload' && (
            <div className="space-y-6">
              {/* Account selection */}
              <div className="space-y-2">
                <Label htmlFor="account">
                  Account <span className="text-destructive">*</span>
                </Label>
                <Select value={accountId} onValueChange={setAccountId}>
                  <SelectTrigger id="account">
                    <SelectValue placeholder="Select account" />
                  </SelectTrigger>
                  <SelectContent>
                    {accounts.map((account) => (
                      <SelectItem key={account.id} value={account.id}>
                        {account.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* File drop zone */}
              <div
                className={cn(
                  'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
                  file
                    ? 'border-primary bg-primary/5'
                    : 'border-muted-foreground/25 hover:border-primary/50'
                )}
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={handleFileInputChange}
                />
                {file ? (
                  <div className="flex flex-col items-center gap-2">
                    <FileSpreadsheet className="h-12 w-12 text-primary" />
                    <p className="font-medium">{file.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        setFile(null)
                        setColumns([])
                      }}
                    >
                      Remove
                    </Button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <Upload className="h-12 w-12 text-muted-foreground" />
                    <p className="font-medium">Drop your CSV file here</p>
                    <p className="text-sm text-muted-foreground">or click to browse</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {step === 'mapping' && (
            <ColumnMappingForm
              columns={columns}
              options={options}
              onChange={setOptions}
              autoDetect={true}
            />
          )}

          {step === 'preview' && preview && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span>
                  Total rows: <strong>{preview.total_rows}</strong>
                </span>
                <span>
                  Selected:{' '}
                  <strong>
                    {preview.preview_transactions.length - excludedRows.size}
                  </strong>{' '}
                  / {preview.preview_transactions.length}
                </span>
                {preview.duplicates.length > 0 && (
                  <span className="text-yellow-600">
                    Duplicates: <strong>{preview.duplicates.length}</strong>
                  </span>
                )}
              </div>

              <ImportPreviewTable
                transactions={preview.preview_transactions}
                excludedRows={excludedRows}
                onToggleRow={handleToggleRow}
                onToggleAll={handleToggleAll}
              />

              {preview.errors.length > 0 && (
                <div className="p-3 rounded-md bg-destructive/10">
                  <p className="text-sm font-medium text-destructive mb-2">
                    Errors ({preview.errors.length})
                  </p>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    {preview.errors.slice(0, 5).map((err) => (
                      <li key={err.row_number}>
                        Row {err.row_number}: {err.message}
                      </li>
                    ))}
                    {preview.errors.length > 5 && (
                      <li>...and {preview.errors.length - 5} more</li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          )}

          {step === 'result' && result && (
            <div className="flex flex-col items-center justify-center py-8 space-y-4">
              <CheckCircle2 className="h-16 w-16 text-green-600" />
              <h3 className="text-xl font-semibold">Import Complete</h3>
              <div className="text-center space-y-1">
                <p>
                  <strong>{result.imported_count}</strong> transactions imported
                </p>
                {result.skipped_count > 0 && (
                  <p className="text-muted-foreground">
                    {result.skipped_count} skipped
                  </p>
                )}
                {result.error_count > 0 && (
                  <p className="text-destructive">{result.error_count} errors</p>
                )}
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          {step === 'upload' && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                onClick={() => setStep('mapping')}
                disabled={!canProceedFromUpload}
              >
                Next
              </Button>
            </>
          )}

          {step === 'mapping' && (
            <>
              <Button variant="outline" onClick={() => setStep('upload')}>
                Back
              </Button>
              <Button
                onClick={handlePreview}
                disabled={!canProceedFromMapping || isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Loading...
                  </>
                ) : (
                  'Preview'
                )}
              </Button>
            </>
          )}

          {step === 'preview' && (
            <>
              <Button variant="outline" onClick={() => setStep('mapping')}>
                Back
              </Button>
              <Button
                onClick={handleImport}
                disabled={
                  isLoading ||
                  !preview ||
                  preview.preview_transactions.length === excludedRows.size
                }
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Importing...
                  </>
                ) : (
                  `Import ${preview ? preview.preview_transactions.length - excludedRows.size : 0} Transactions`
                )}
              </Button>
            </>
          )}

          {step === 'result' && (
            <Button onClick={handleClose}>Close</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default CSVImportDialog
