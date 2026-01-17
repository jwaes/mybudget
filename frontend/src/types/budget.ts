/**
 * Budget types for MyBudget.
 */

export interface CategoryBudget {
  id: string
  name: string
  funded_this_month: string
  activity: string
  available: string
}

export interface CategoryGroupBudget {
  id: string
  name: string
  display_order: number
  categories: CategoryBudget[]
}

export interface BudgetMonthView {
  month: string
  to_assign: string
  groups: CategoryGroupBudget[]
}

export interface AssignmentCreate {
  amount: string
  month: string
}

export interface Assignment {
  id: string
  user_id: string
  category_id: string
  amount: string
  month: string
  created_at: string
}

export interface UnderfundedCategory {
  category_id: string
  category_name: string
  underfunded: string
}

export interface UnderfundedSummary {
  total_underfunded: string
  categories_underfunded: number
  categories: UnderfundedCategory[]
}

export interface FundSingleResult {
  category_id: string
  amount_funded: string
  amount_requested: string
  is_partial: boolean
}

export interface FundedCategory {
  category_id: string
  category_name: string
  amount_funded: string
}

export interface FundAllResult {
  total_funded: string
  total_underfunded: string
  categories_funded: number
  funded_categories: FundedCategory[]
  is_partial: boolean
}
