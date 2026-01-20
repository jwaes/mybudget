/**
 * ColumnMappingForm component.
 *
 * Form for configuring CSV column mappings during import.
 */

import { useEffect } from 'react'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  csvImportService,
  type ImportOptions,
  type AmountSignMode,
  type CSVDelimiter,
} from '@/services/csvImportService'

interface ColumnMappingFormProps {
  /** Available columns from CSV header */
  columns: string[]
  /** Current import options */
  options: Partial<ImportOptions>
  /** Callback when options change */
  onChange: (options: Partial<ImportOptions>) => void
  /** Auto-detect column mappings on mount */
  autoDetect?: boolean
}

const NONE_VALUE = '__none__'

/**
 * Form for mapping CSV columns to transaction fields.
 */
export function ColumnMappingForm({
  columns,
  options,
  onChange,
  autoDetect = true,
}: ColumnMappingFormProps) {
  // Auto-detect columns on mount
  useEffect(() => {
    if (autoDetect && columns.length > 0 && !options.date_column) {
      const detected = csvImportService.autoDetectColumns(columns)
      onChange({
        ...options,
        ...detected,
      })
    }
  }, [columns, autoDetect, options, onChange])

  const handleSelectChange = (field: keyof ImportOptions, value: string) => {
    const actualValue = value === NONE_VALUE ? undefined : value
    onChange({
      ...options,
      [field]: actualValue,
    })
  }

  const handleCheckboxChange = (field: keyof ImportOptions, checked: boolean) => {
    onChange({
      ...options,
      [field]: checked,
    })
  }

  return (
    <div className="space-y-6">
      {/* Delimiter */}
      <div className="space-y-2">
        <Label htmlFor="delimiter">Delimiter</Label>
        <Select
          value={options.delimiter || ','}
          onValueChange={(value) => handleSelectChange('delimiter', value as CSVDelimiter)}
        >
          <SelectTrigger id="delimiter" className="w-full">
            <SelectValue placeholder="Select delimiter" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value=",">Comma (,)</SelectItem>
            <SelectItem value=";">Semicolon (;)</SelectItem>
            <SelectItem value={'\t'}>Tab</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Has Header */}
      <div className="flex items-center space-x-2">
        <Checkbox
          id="has_header"
          checked={options.has_header !== false}
          onCheckedChange={(checked) => handleCheckboxChange('has_header', checked === true)}
        />
        <Label htmlFor="has_header" className="text-sm font-normal">
          First row contains column headers
        </Label>
      </div>

      <div className="border-t pt-4">
        <h4 className="text-sm font-medium mb-4">Column Mapping</h4>

        <div className="grid grid-cols-2 gap-4">
          {/* Date Column */}
          <div className="space-y-2">
            <Label htmlFor="date_column">
              Date Column <span className="text-destructive">*</span>
            </Label>
            <Select
              value={options.date_column || ''}
              onValueChange={(value) => handleSelectChange('date_column', value)}
            >
              <SelectTrigger id="date_column">
                <SelectValue placeholder="Select column" />
              </SelectTrigger>
              <SelectContent>
                {columns.map((col) => (
                  <SelectItem key={col} value={col}>
                    {col}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Date Format */}
          <div className="space-y-2">
            <Label htmlFor="date_format">
              Date Format <span className="text-destructive">*</span>
            </Label>
            <Select
              value={options.date_format || ''}
              onValueChange={(value) => handleSelectChange('date_format', value)}
            >
              <SelectTrigger id="date_format">
                <SelectValue placeholder="Select format" />
              </SelectTrigger>
              <SelectContent>
                {csvImportService.DATE_FORMATS.map((format) => (
                  <SelectItem key={format.value} value={format.value}>
                    {format.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Amount Column */}
          <div className="space-y-2">
            <Label htmlFor="amount_column">
              Amount Column <span className="text-destructive">*</span>
            </Label>
            <Select
              value={options.amount_column || ''}
              onValueChange={(value) => handleSelectChange('amount_column', value)}
            >
              <SelectTrigger id="amount_column">
                <SelectValue placeholder="Select column" />
              </SelectTrigger>
              <SelectContent>
                {columns.map((col) => (
                  <SelectItem key={col} value={col}>
                    {col}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Amount Sign Mode */}
          <div className="space-y-2">
            <Label htmlFor="amount_sign_mode">
              Amount Sign Mode <span className="text-destructive">*</span>
            </Label>
            <Select
              value={options.amount_sign_mode || 'signed'}
              onValueChange={(value) =>
                handleSelectChange('amount_sign_mode', value as AmountSignMode)
              }
            >
              <SelectTrigger id="amount_sign_mode">
                <SelectValue placeholder="Select mode" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="signed">Signed (negative = expense)</SelectItem>
                <SelectItem value="negative_expense">
                  Negative = expense, positive = income
                </SelectItem>
                <SelectItem value="positive_expense">
                  Positive = expense, negative = income
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Payee Column */}
          <div className="space-y-2">
            <Label htmlFor="payee_column">
              Payee/Description Column <span className="text-destructive">*</span>
            </Label>
            <Select
              value={options.payee_column || ''}
              onValueChange={(value) => handleSelectChange('payee_column', value)}
            >
              <SelectTrigger id="payee_column">
                <SelectValue placeholder="Select column" />
              </SelectTrigger>
              <SelectContent>
                {columns.map((col) => (
                  <SelectItem key={col} value={col}>
                    {col}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Memo Column (optional) */}
          <div className="space-y-2">
            <Label htmlFor="memo_column">Memo/Note Column (optional)</Label>
            <Select
              value={options.memo_column || NONE_VALUE}
              onValueChange={(value) => handleSelectChange('memo_column', value)}
            >
              <SelectTrigger id="memo_column">
                <SelectValue placeholder="Select column (optional)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NONE_VALUE}>None</SelectItem>
                {columns.map((col) => (
                  <SelectItem key={col} value={col}>
                    {col}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ColumnMappingForm
