/**
 * Category group section component for budget view.
 *
 * Displays a category group with its categories, totals, and targets.
 */

import { useState } from 'react'
import type { CategoryGroupBudget } from '@/types/budget'
import type { CategoryTarget, UnderfundedResponse } from '@/types/target'
import type { Category, CategoryGroup } from '@/types/category'
import { CategoryRow } from './CategoryRow'
import { CategoryModal } from './CategoryModal'

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
  if (available < 0) return 'negative'
  if (available > 0) return 'positive'
  return 'zero'
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
    <div className="category-group-section">
      <div className="group-header">
        <button
          className="group-name-button"
          onClick={handleEditGroup}
          title="Click to edit group"
        >
          {group.name}
        </button>
        <div className="group-totals">
          <span className="funded">{formatAmount(totals.funded.toString())}</span>
          <span className="activity">{formatAmount(totals.activity.toString())}</span>
          <span className={`available ${getAvailableClass(totals.available)}`}>
            {formatAmount(totals.available.toString())}
          </span>
        </div>
      </div>
      <div className="category-list">
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
        <button className="add-category-button" onClick={handleAddCategory}>
          + Add Category
        </button>
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

      <style>{`
        .category-group-section {
          margin-bottom: 1.5rem;
          background: white;
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          overflow: hidden;
        }

        .group-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.75rem 1rem;
          background-color: #f5f5f5;
          border-bottom: 1px solid #ddd;
        }

        .group-name-button {
          font-weight: 600;
          color: #333;
          text-transform: uppercase;
          font-size: 0.875rem;
          letter-spacing: 0.05em;
          background: none;
          border: none;
          cursor: pointer;
          padding: 0.25rem 0.5rem;
          margin: -0.25rem -0.5rem;
          border-radius: 4px;
          transition: background-color 0.15s;
        }

        .group-name-button:hover {
          background-color: rgba(0, 0, 0, 0.05);
        }

        .group-totals {
          display: flex;
          gap: 2rem;
          text-align: right;
        }

        .group-totals .funded,
        .group-totals .activity,
        .group-totals .available {
          min-width: 100px;
          text-align: right;
          font-weight: 600;
          font-size: 0.875rem;
          font-variant-numeric: tabular-nums;
        }

        .group-totals .activity {
          color: #666;
        }

        .group-totals .available.positive {
          color: #22a722;
        }

        .group-totals .available.negative {
          color: #c00;
        }

        .group-totals .available.zero {
          color: #666;
        }

        .category-list {
          background: white;
        }

        .add-category-button {
          display: block;
          width: 100%;
          padding: 0.75rem 1rem;
          background: none;
          border: none;
          border-top: 1px dashed #ddd;
          color: #666;
          font-size: 0.875rem;
          cursor: pointer;
          text-align: left;
          transition: background-color 0.15s, color 0.15s;
        }

        .add-category-button:hover {
          background-color: #f0f7ff;
          color: #0066cc;
        }
      `}</style>
    </div>
  )
}

export default CategoryGroupSection
