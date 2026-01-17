/**
 * Category group section component for budget view.
 *
 * Displays a category group with its categories, totals, and targets.
 */

import { useState } from 'react'
import type { CategoryGroupBudget } from '@/types/budget'
import type { CategoryTarget, UnderfundedResponse } from '@/types/target'
import type { Category, CategoryGroup } from '@/types/category'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { CategoryRow } from './CategoryRow'
import { CategoryModal } from './CategoryModal'
import { cn } from '@/lib/utils'

interface CategoryGroupSectionProps {
  group: CategoryGroupBudget
  groupData?: CategoryGroup
  allGroups: CategoryGroup[]
  targets: Map<string, CategoryTarget>
  underfunded: Map<string, UnderfundedResponse>
  onAssign: (categoryId: string, amount: string) => Promise<void>
  onTargetChange: (categoryId: string, target: CategoryTarget | null) => void
  onFundUnderfunded?: (categoryId: string) => Promise<void>
  onEditGroup?: (group: CategoryGroup) => void
  onCategoryChange?: () => void
  canFund?: boolean
}

/**
 * Format a decimal string for display.
 */
function formatAmount(amount: string): string {
  const num = parseFloat(amount)
  if (isNaN(num)) return '0.00'
  return num.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

/**
 * Calculate group totals from categories.
 */
function calculateGroupTotals(group: CategoryGroupBudget): {
  funded: number
  activity: number
  available: number
} {
  return group.categories.reduce(
    (acc, cat) => ({
      funded: acc.funded + parseFloat(cat.funded_this_month || '0'),
      activity: acc.activity + parseFloat(cat.activity || '0'),
      available: acc.available + parseFloat(cat.available || '0'),
    }),
    { funded: 0, activity: 0, available: 0 }
  )
}

/**
 * Get CSS class for available amount based on value.
 */
function getAvailableClass(available: number): string {
  if (available < 0) return 'text-destructive'
  if (available > 0) return 'text-green-600'
  return 'text-muted-foreground'
}

export function CategoryGroupSection({
  group,
  groupData,
  allGroups,
  targets,
  underfunded,
  onAssign,
  onTargetChange,
  onFundUnderfunded,
  onEditGroup,
  onCategoryChange,
  canFund,
}: CategoryGroupSectionProps) {
  const totals = calculateGroupTotals(group)
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false)
  const [editingCategory, setEditingCategory] = useState<Category | null>(null)

  const handleEditGroup = () => {
    if (groupData && onEditGroup) {
      onEditGroup(groupData)
    }
  }

  const handleAddCategory = () => {
    setEditingCategory(null)
    setIsCategoryModalOpen(true)
  }

  const handleEditCategory = (category: Category) => {
    setEditingCategory(category)
    setIsCategoryModalOpen(true)
  }

  const handleCategorySaved = () => {
    setIsCategoryModalOpen(false)
    setEditingCategory(null)
    onCategoryChange?.()
  }

  const handleCategoryDeleted = () => {
    setIsCategoryModalOpen(false)
    setEditingCategory(null)
    onCategoryChange?.()
  }

  return (
    <Card className="mb-6 overflow-hidden">
      <div className="flex justify-between items-center py-3 px-4 bg-muted border-b">
        <button
          className="font-semibold text-foreground uppercase text-sm tracking-wide bg-transparent border-0 cursor-pointer py-1 px-2 -my-1 -mx-2 rounded transition-colors hover:bg-background/50"
          onClick={handleEditGroup}
          title="Click to edit group"
        >
          {group.name}
        </button>
        <div className="flex gap-8 text-right">
          <span className="min-w-[100px] text-right font-semibold text-sm tabular-nums">
            {formatAmount(totals.funded.toString())}
          </span>
          <span className="min-w-[100px] text-right font-semibold text-sm tabular-nums text-muted-foreground">
            {formatAmount(totals.activity.toString())}
          </span>
          <span className={cn('min-w-[100px] text-right font-semibold text-sm tabular-nums', getAvailableClass(totals.available))}>
            {formatAmount(totals.available.toString())}
          </span>
        </div>
      </div>
      <div className="bg-background">
        {group.categories.map((category) => (
          <CategoryRow
            key={category.id}
            category={category}
            target={targets.get(category.id)}
            underfunded={underfunded.get(category.id)}
            onAssign={onAssign}
            onTargetChange={(target) => onTargetChange(category.id, target)}
            onFundUnderfunded={onFundUnderfunded}
            onEditCategory={handleEditCategory}
            canFund={canFund}
          />
        ))}
        <Button
          variant="ghost"
          className="w-full justify-start py-3 px-4 text-muted-foreground border-t border-dashed hover:bg-primary/5 hover:text-primary"
          onClick={handleAddCategory}
        >
          + Add Category
        </Button>
      </div>

      <CategoryModal
        existingCategory={editingCategory}
        groups={allGroups}
        defaultGroupId={group.id}
        isOpen={isCategoryModalOpen}
        onClose={() => setIsCategoryModalOpen(false)}
        onSave={handleCategorySaved}
        onDelete={handleCategoryDeleted}
      />
    </Card>
  )
}

export default CategoryGroupSection
