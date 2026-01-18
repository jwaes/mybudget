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
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { MonthNavigator } from './MonthNavigator'
import { CategoryGroupSection } from './CategoryGroupSection'
import { CategoryGroupModal } from './CategoryGroupModal'
import { useToast } from './Toast'
import { cn } from '@/lib/utils'

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
  if (num < 0) return 'text-destructive'
  if (num > 0) return 'text-green-600'
  return 'text-foreground'
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
      <div className="max-w-4xl mx-auto p-4">
        <div className="flex justify-between items-center mb-6">
          <Skeleton className="h-10 w-[250px]" />
          <Skeleton className="h-10 w-[150px]" />
        </div>
        <Skeleton className="h-10 w-full mb-4" />
        <Skeleton className="h-32 w-full mb-4" />
        <Skeleton className="h-32 w-full mb-4" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] gap-4 text-muted-foreground">
        <span>{error}</span>
        <Button onClick={loadBudget}>Retry</Button>
      </div>
    )
  }

  if (!budgetData) {
    return null
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <MonthNavigator month={month} onMonthChange={handleMonthChange} />
        <div className="flex flex-col items-end gap-3">
          <div className="flex flex-col items-end">
            <span className="text-sm text-muted-foreground mb-1">To Assign:</span>
            <span className={cn('text-2xl font-semibold tabular-nums to-assign-amount', getToAssignClass(budgetData.to_assign))}>
              ${formatAmount(budgetData.to_assign)}
            </span>
          </div>
          {underfundedSummary && underfundedSummary.categories_underfunded > 0 && (
            <div className="flex items-center gap-4">
              <div className="flex flex-col items-end">
                <span className="text-xs text-muted-foreground">Underfunded:</span>
                <span className="text-base font-semibold text-orange-500 tabular-nums">
                  ${formatAmount(underfundedSummary.total_underfunded)}
                </span>
              </div>
              <Button
                onClick={handleFundAll}
                disabled={isFunding || parseFloat(budgetData.to_assign) <= 0}
                title={
                  parseFloat(budgetData.to_assign) <= 0
                    ? 'No funds available to assign'
                    : `Fund ${underfundedSummary.categories_underfunded} underfunded categories`
                }
              >
                {isFunding ? 'Funding...' : 'Fund Underfunded'}
              </Button>
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-between items-center py-2 px-4 bg-muted rounded mb-4 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
        <span>Category</span>
        <div className="flex gap-8">
          <span className="min-w-[100px] text-right">Funded</span>
          <span className="min-w-[100px] text-right">Activity</span>
          <span className="min-w-[100px] text-right">Available</span>
        </div>
      </div>

      <div className="min-h-[200px]">
        {budgetData.groups.length === 0 ? (
          <Card className="text-center p-12 text-muted-foreground">
            <p className="mb-2">No categories yet.</p>
            <p className="mb-4">Create some category groups and categories to start budgeting.</p>
            <Button onClick={handleAddGroup}>
              Add Category Group
            </Button>
          </Card>
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
            <Button
              variant="outline"
              className="w-full mt-4 border-dashed text-muted-foreground hover:text-primary hover:border-primary"
              onClick={handleAddGroup}
            >
              + Add Category Group
            </Button>
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
    </div>
  )
}

export default BudgetMonthView
