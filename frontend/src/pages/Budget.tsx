/**
 * Budget page component.
 *
 * Main page for viewing and managing the monthly budget.
 */

import { BudgetMonthView } from '@/components/BudgetMonthView'

export function BudgetPage() {
  return (
    <div className="budget-page">
      <h1>Budget</h1>
      <BudgetMonthView />

      <style>{`
        .budget-page {
          padding: 1rem;
        }

        .budget-page h1 {
          margin: 0 0 1.5rem;
          font-size: 1.75rem;
          color: #333;
        }
      `}</style>
    </div>
  )
}

export default BudgetPage
