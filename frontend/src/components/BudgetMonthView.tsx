/**
 * Budget month view component.
 *
 * Displays the budget for a specific month with all category groups,
 * their categories, and budget information. Also manages targets.
 */

import { useState, useEffect, useCallback } from 'react'
import type { BudgetMonthView as BudgetMonthViewType, UnderfundedSummary } from '@/types/budget'
import type { CategoryTarget, UnderfundedResponse } from '@/types/target'
import type { CategoryGroup } from '@/types/category'
import { budgetService } from '@/services/budgetService'
import { targetService } from '@/services/targetService'
import { categoryService } from '@/services/categoryService'
import { MonthNavigator } from './MonthNavigator'
import { CategoryGroupSection } from './CategoryGroupSection'
import { CategoryGroupModal } from './CategoryGroupModal'
import { useToast } from './Toast'

interface BudgetMonthViewProps {
  /** Initial month in YYYY-MM format */
  initialMonth?: string
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
 * Get current month in YYYY-MM format.
 */
function getCurrentMonth(): string {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  return `${year}-${month}`
}

/**
 * Get CSS class for to_assign amount.
 */
function getToAssignClass(toAssign: string): string {
  const num = parseFloat(toAssign)
  if (num < 0) return 'overassigned'
  if (num > 0) return 'available'
  return 'zero'
}

export function BudgetMonthView({ initialMonth }: BudgetMonthViewProps) {
  const [month, setMonth] = useState(initialMonth || getCurrentMonth())
  const [budgetData, setBudgetData] = useState<BudgetMonthViewType | null>(null)
  const [targets, setTargets] = useState<Map<string, CategoryTarget>>(new Map())
  const [underfunded, setUnderfunded] = useState<Map<string, UnderfundedResponse>>(new Map())
  const [underfundedSummary, setUnderfundedSummary] = useState<UnderfundedSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isFunding, setIsFunding] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isGroupModalOpen, setIsGroupModalOpen] = useState(false)
  const [editingGroup, setEditingGroup] = useState<CategoryGroup | null>(null)
  const [categoryGroups, setCategoryGroups] = useState<CategoryGroup[]>([])
  const { showToast } = useToast()

  const loadBudget = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      // Load budget data, targets, underfunded summary, and groups in parallel
      const [data, targetList, summary, groups] = await Promise.all([
        budgetService.getMonthView(month),
        targetService.getTargets(),
        budgetService.getUnderfundedSummary(month),
        categoryService.listGroups(),
      ])
      setBudgetData(data)
      setUnderfundedSummary(summary)
      setCategoryGroups(groups)

      // Create a map of category_id -> target for quick lookup
      const targetMap = new Map<string, CategoryTarget>()
      for (const target of targetList) {
        targetMap.set(target.category_id, target)
      }
      setTargets(targetMap)

      // Load underfunded data for all targets
      const monthDate = `${month}-01`
      const underfundedPromises = targetList.map((target) =>
        targetService.getUnderfunded(target.id, monthDate).catch(() => null)
      )
      const underfundedResults = await Promise.all(underfundedPromises)

      const underfundedMap = new Map<string, UnderfundedResponse>()
      for (const result of underfundedResults) {
        if (result) {
          underfundedMap.set(result.category_id, result)
        }
      }
      setUnderfunded(underfundedMap)
    } catch (err) {
      console.error('Failed to load budget:', err)
      setError('Failed to load budget data')
    } finally {
      setIsLoading(false)
    }
  }, [month])

  useEffect(() => {
    loadBudget()
  }, [loadBudget])

  const handleAssign = async (categoryId: string, amount: string) => {
    // Get first day of current month for assignment
    const monthDate = `${month}-01`

    await budgetService.assignFunds(categoryId, {
      amount,
      month: monthDate,
    })

    // Reload budget to get updated values
    await loadBudget()
  }

  const handleMonthChange = (newMonth: string) => {
    setMonth(newMonth)
  }

  const handleFundAll = async () => {
    if (!underfundedSummary || underfundedSummary.categories_underfunded === 0 || !budgetData) return

    // Calculate how much we can fund (minimum of to_assign and total underfunded)
    const toAssign = parseFloat(budgetData.to_assign)
    const totalUnderfunded = parseFloat(underfundedSummary.total_underfunded)
    const amountToFund = Math.min(toAssign, totalUnderfunded)

    if (amountToFund <= 0) return

    // Optimistic update: Update local state immediately
    const previousBudgetData = budgetData
    const previousUnderfundedSummary = underfundedSummary
    const previousUnderfunded = new Map(underfunded)

    // Update to_assign optimistically
    setBudgetData({
      ...budgetData,
      to_assign: (toAssign - amountToFund).toFixed(4),
    })

    // Clear underfunded summary optimistically
    setUnderfundedSummary({
      total_underfunded: '0.00',
      categories_underfunded: 0,
      categories: [],
    })

    // Clear category underfunded amounts
    setUnderfunded(new Map())

    setIsFunding(true)
    try {
      await budgetService.fundAllUnderfunded(month)
      // Reload budget to get accurate server values
      await loadBudget()
      showToast(`Funded $${formatAmount(amountToFund.toString())} to underfunded categories`, 'success')
    } catch (err) {
      console.error('Failed to fund underfunded:', err)
      // Rollback optimistic update on error
      setBudgetData(previousBudgetData)
      setUnderfundedSummary(previousUnderfundedSummary)
      setUnderfunded(previousUnderfunded)
      setError('Failed to fund underfunded categories')
      showToast('Failed to fund underfunded categories', 'error')
    } finally {
      setIsFunding(false)
    }
  }

  const handleFundSingle = async (categoryId: string) => {
    if (!budgetData) return

    const categoryUnderfunded = underfunded.get(categoryId)
    if (!categoryUnderfunded) return

    const toAssign = parseFloat(budgetData.to_assign)
    const underfundedAmount = parseFloat(categoryUnderfunded.underfunded)
    const amountToFund = Math.min(toAssign, underfundedAmount)

    if (amountToFund <= 0) return

    // Optimistic update: Update local state immediately
    const previousBudgetData = budgetData
    const previousUnderfundedSummary = underfundedSummary
    const previousUnderfunded = new Map(underfunded)

    // Update to_assign optimistically
    setBudgetData({
      ...budgetData,
      to_assign: (toAssign - amountToFund).toFixed(4),
    })

    // Update underfunded for this category
    const newUnderfunded = new Map(underfunded)
    newUnderfunded.set(categoryId, {
      ...categoryUnderfunded,
      underfunded: '0.00',
    })
    setUnderfunded(newUnderfunded)

    // Update underfunded summary
    if (underfundedSummary) {
      const newTotal = parseFloat(underfundedSummary.total_underfunded) - amountToFund
      setUnderfundedSummary({
        ...underfundedSummary,
        total_underfunded: newTotal.toFixed(2),
        categories_underfunded: underfundedSummary.categories_underfunded - 1,
      })
    }

    try {
      await budgetService.fundUnderfunded(month, categoryId)
      // Reload budget to get accurate server values
      await loadBudget()
      // Find category name for toast message
      const categoryName = budgetData.groups
        .flatMap((g) => g.categories)
        .find((c) => c.id === categoryId)?.name || 'category'
      showToast(`Funded $${formatAmount(amountToFund.toString())} to ${categoryName}`, 'success')
    } catch (err) {
      console.error('Failed to fund category:', err)
      // Rollback optimistic update on error
      setBudgetData(previousBudgetData)
      setUnderfundedSummary(previousUnderfundedSummary)
      setUnderfunded(previousUnderfunded)
      setError('Failed to fund category')
      showToast('Failed to fund category', 'error')
    }
  }

  const handleTargetChange = async (categoryId: string, target: CategoryTarget | null) => {
    // Update local state immediately
    const newTargets = new Map(targets)
    if (target) {
      newTargets.set(categoryId, target)
    } else {
      newTargets.delete(categoryId)
    }
    setTargets(newTargets)

    // Reload underfunded data if target exists
    if (target) {
      try {
        const monthDate = `${month}-01`
        const result = await targetService.getUnderfunded(target.id, monthDate)
        const newUnderfunded = new Map(underfunded)
        newUnderfunded.set(categoryId, result)
        setUnderfunded(newUnderfunded)
      } catch (err) {
        console.error('Failed to load underfunded:', err)
      }
    } else {
      // Remove underfunded data for deleted target
      const newUnderfunded = new Map(underfunded)
      newUnderfunded.delete(categoryId)
      setUnderfunded(newUnderfunded)
    }
  }

  const handleAddGroup = () => {
    setEditingGroup(null)
    setIsGroupModalOpen(true)
  }

  const handleEditGroup = (group: CategoryGroup) => {
    setEditingGroup(group)
    setIsGroupModalOpen(true)
  }

  const handleGroupSaved = () => {
    setIsGroupModalOpen(false)
    setEditingGroup(null)
    loadBudget()
  }

  const handleGroupDeleted = () => {
    setIsGroupModalOpen(false)
    setEditingGroup(null)
    loadBudget()
  }

  const handleCategoryChange = () => {
    loadBudget()
  }

  if (isLoading && !budgetData) {
    return (
      <div className="budget-loading">
        <span>Loading budget...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="budget-error">
        <span>{error}</span>
        <button onClick={loadBudget}>Retry</button>
      </div>
    )
  }

  if (!budgetData) {
    return null
  }

  return (
    <div className="budget-month-view">
      <div className="budget-header">
        <MonthNavigator month={month} onMonthChange={handleMonthChange} />
        <div className="budget-summary">
          <div className={`to-assign ${getToAssignClass(budgetData.to_assign)}`}>
            <span className="to-assign-label">To Assign:</span>
            <span className="to-assign-amount">${formatAmount(budgetData.to_assign)}</span>
          </div>
          {underfundedSummary && underfundedSummary.categories_underfunded > 0 && (
            <div className="underfunded-section">
              <div className="underfunded-info">
                <span className="underfunded-label">Underfunded:</span>
                <span className="underfunded-amount">
                  ${formatAmount(underfundedSummary.total_underfunded)}
                </span>
              </div>
              <button
                className="fund-all-button"
                onClick={handleFundAll}
                disabled={isFunding || parseFloat(budgetData.to_assign) <= 0}
                title={
                  parseFloat(budgetData.to_assign) <= 0
                    ? 'No funds available to assign'
                    : `Fund ${underfundedSummary.categories_underfunded} underfunded categories`
                }
              >
                {isFunding ? 'Funding...' : 'Fund Underfunded'}
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="column-headers">
        <span className="column-category">Category</span>
        <div className="column-amounts">
          <span className="column-funded">Funded</span>
          <span className="column-activity">Activity</span>
          <span className="column-available">Available</span>
        </div>
      </div>

      <div className="budget-groups">
        {budgetData.groups.length === 0 ? (
          <div className="empty-state">
            <p>No categories yet.</p>
            <p>Create some category groups and categories to start budgeting.</p>
            <button className="add-group-button" onClick={handleAddGroup}>
              Add Category Group
            </button>
          </div>
        ) : (
          <>
            {budgetData.groups.map((group) => {
              const groupData = categoryGroups.find((g) => g.id === group.id)
              return (
                <CategoryGroupSection
                  key={group.id}
                  group={group}
                  groupData={groupData}
                  allGroups={categoryGroups}
                  targets={targets}
                  underfunded={underfunded}
                  onAssign={handleAssign}
                  onTargetChange={handleTargetChange}
                  onFundUnderfunded={handleFundSingle}
                  onEditGroup={handleEditGroup}
                  onCategoryChange={handleCategoryChange}
                  canFund={parseFloat(budgetData.to_assign) > 0}
                />
              )
            })}
            <button className="add-group-button-bottom" onClick={handleAddGroup}>
              + Add Category Group
            </button>
          </>
        )}
      </div>

      <CategoryGroupModal
        existingGroup={editingGroup}
        isOpen={isGroupModalOpen}
        onClose={() => setIsGroupModalOpen(false)}
        onSave={handleGroupSaved}
        onDelete={handleGroupDeleted}
      />

      <style>{`
        .budget-month-view {
          max-width: 900px;
          margin: 0 auto;
          padding: 1rem;
        }

        .budget-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }

        .to-assign {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
        }

        .to-assign-label {
          font-size: 0.875rem;
          color: #666;
          margin-bottom: 0.25rem;
        }

        .to-assign-amount {
          font-size: 1.5rem;
          font-weight: 600;
          font-variant-numeric: tabular-nums;
        }

        .to-assign.available .to-assign-amount {
          color: #22a722;
        }

        .to-assign.overassigned .to-assign-amount {
          color: #c00;
        }

        .to-assign.zero .to-assign-amount {
          color: #333;
        }

        .budget-summary {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 0.75rem;
        }

        .underfunded-section {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .underfunded-info {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
        }

        .underfunded-label {
          font-size: 0.75rem;
          color: #666;
        }

        .underfunded-amount {
          font-size: 1rem;
          font-weight: 600;
          color: #e67700;
          font-variant-numeric: tabular-nums;
        }

        .fund-all-button {
          padding: 0.5rem 1rem;
          background-color: #0066cc;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.875rem;
          font-weight: 500;
          transition: background-color 0.2s;
        }

        .fund-all-button:hover:not(:disabled) {
          background-color: #0055aa;
        }

        .fund-all-button:disabled {
          background-color: #ccc;
          cursor: not-allowed;
        }

        .column-headers {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem 1rem;
          background-color: #e5e5e5;
          border-radius: 4px;
          margin-bottom: 1rem;
          font-size: 0.75rem;
          font-weight: 600;
          color: #666;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .column-amounts {
          display: flex;
          gap: 2rem;
        }

        .column-funded,
        .column-activity,
        .column-available {
          min-width: 100px;
          text-align: right;
        }

        .budget-groups {
          min-height: 200px;
        }

        .empty-state {
          text-align: center;
          padding: 3rem;
          color: #666;
          background: white;
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .empty-state p {
          margin: 0.5rem 0;
        }

        .add-group-button,
        .add-group-button-bottom {
          padding: 0.75rem 1.5rem;
          background-color: #0066cc;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.875rem;
          font-weight: 500;
          transition: background-color 0.2s;
        }

        .add-group-button {
          margin-top: 1rem;
        }

        .add-group-button-bottom {
          display: block;
          width: 100%;
          margin-top: 1rem;
          background-color: #f5f5f5;
          color: #666;
          border: 2px dashed #ccc;
        }

        .add-group-button:hover,
        .add-group-button-bottom:hover {
          background-color: #0055aa;
          color: white;
          border-color: #0055aa;
        }

        .budget-loading,
        .budget-error {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 300px;
          gap: 1rem;
          color: #666;
        }

        .budget-error button {
          padding: 0.5rem 1rem;
          background-color: #0066cc;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }

        .budget-error button:hover {
          background-color: #0055aa;
        }
      `}</style>
    </div>
  )
}

export default BudgetMonthView
