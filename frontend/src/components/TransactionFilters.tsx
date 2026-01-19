/**
 * TransactionFilters component.
 *
 * Provides advanced filtering options for transactions including
 * date range, amount range, category, state, and uncategorized filter.
 */

import { useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export interface TransactionFiltersState {
  date_from?: string
  date_to?: string
  amount_min?: string
  amount_max?: string
  category_id?: string
  state?: string
  uncategorized_only?: boolean
}

interface TransactionFiltersProps {
  filters: TransactionFiltersState
  categories: Array<{ id: string; name: string }>
  onChange: (filters: TransactionFiltersProps['filters']) => void
  onClear: () => void
}

export function TransactionFilters({
  filters,
  categories,
  onChange,
  onClear,
}: TransactionFiltersProps) {
  const activeFilterCount = useMemo(() => {
    let count = 0
    if (filters.date_from) count++
    if (filters.date_to) count++
    if (filters.amount_min) count++
    if (filters.amount_max) count++
    if (filters.category_id) count++
    if (filters.state) count++
    if (filters.uncategorized_only) count++
    return count
  }, [filters])

  function updateFilter<K extends keyof TransactionFiltersState>(
    key: K,
    value: TransactionFiltersState[K]
  ) {
    onChange({
      ...filters,
      [key]: value || undefined,
    })
  }

  return (
    <div className="flex flex-wrap items-end gap-4">
      {/* Date Range */}
      <div className="flex items-end gap-2">
        <div className="space-y-1">
          <Label htmlFor="date_from" className="text-xs text-muted-foreground">
            From
          </Label>
          <Input
            id="date_from"
            type="date"
            value={filters.date_from || ''}
            onChange={(e) => updateFilter('date_from', e.target.value)}
            className="w-[140px]"
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="date_to" className="text-xs text-muted-foreground">
            To
          </Label>
          <Input
            id="date_to"
            type="date"
            value={filters.date_to || ''}
            onChange={(e) => updateFilter('date_to', e.target.value)}
            className="w-[140px]"
          />
        </div>
      </div>

      {/* Amount Range */}
      <div className="flex items-end gap-2">
        <div className="space-y-1">
          <Label htmlFor="amount_min" className="text-xs text-muted-foreground">
            Min Amount
          </Label>
          <Input
            id="amount_min"
            type="number"
            step="0.01"
            placeholder="0.00"
            value={filters.amount_min || ''}
            onChange={(e) => updateFilter('amount_min', e.target.value)}
            className="w-[100px]"
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="amount_max" className="text-xs text-muted-foreground">
            Max Amount
          </Label>
          <Input
            id="amount_max"
            type="number"
            step="0.01"
            placeholder="0.00"
            value={filters.amount_max || ''}
            onChange={(e) => updateFilter('amount_max', e.target.value)}
            className="w-[100px]"
          />
        </div>
      </div>

      {/* Category Filter */}
      <div className="space-y-1">
        <Label htmlFor="category_filter" className="text-xs text-muted-foreground">
          Category
        </Label>
        <Select
          value={filters.category_id || 'all'}
          onValueChange={(value) => updateFilter('category_id', value === 'all' ? undefined : value)}
        >
          <SelectTrigger id="category_filter" className="w-[180px]">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map((category) => (
              <SelectItem key={category.id} value={category.id}>
                {category.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Status Filter */}
      <div className="space-y-1">
        <Label htmlFor="state_filter" className="text-xs text-muted-foreground">
          Status
        </Label>
        <Select
          value={filters.state || 'all'}
          onValueChange={(value) => updateFilter('state', value === 'all' ? undefined : value)}
        >
          <SelectTrigger id="state_filter" className="w-[140px]">
            <SelectValue placeholder="All" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="INBOX">Inbox</SelectItem>
            <SelectItem value="APPROVED">Approved</SelectItem>
            <SelectItem value="CLEARED">Cleared</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Uncategorized Only Checkbox */}
      <div className="flex items-center gap-2 pb-0.5">
        <Checkbox
          id="uncategorized_only"
          checked={filters.uncategorized_only || false}
          onCheckedChange={(checked) =>
            updateFilter('uncategorized_only', checked === true ? true : undefined)
          }
        />
        <Label
          htmlFor="uncategorized_only"
          className="text-sm text-muted-foreground cursor-pointer"
        >
          Uncategorized only
        </Label>
      </div>

      {/* Clear Filters Button */}
      <Button
        variant="outline"
        size="sm"
        onClick={onClear}
        disabled={activeFilterCount === 0}
      >
        Clear Filters
        {activeFilterCount > 0 && (
          <span className="ml-1.5 rounded-full bg-primary px-1.5 py-0.5 text-xs text-primary-foreground">
            {activeFilterCount}
          </span>
        )}
      </Button>
    </div>
  )
}

export default TransactionFilters
