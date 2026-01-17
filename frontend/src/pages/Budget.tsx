/**
 * Budget page component.
 *
 * Main page for viewing and managing the monthly budget.
 */

import { BudgetMonthView } from '@/components/BudgetMonthView'

export function BudgetPage() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold text-foreground mb-6">Budget</h1>
      <BudgetMonthView />
    </div>
  )
}

export default BudgetPage
