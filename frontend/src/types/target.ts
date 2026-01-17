/**
 * Target types for MyBudget.
 */

export type TargetType = 'MONTHLY_NEEDED' | 'TARGET_BALANCE' | 'TARGET_BY_DATE'

export interface CategoryTarget {
  id: string
  category_id: string
  category_name: string | null
  target_type: TargetType
  amount: string
  target_date: string | null
  created_at: string
  updated_at: string
}

export interface CategoryTargetCreate {
  category_id: string
  target_type: TargetType
  amount: string
  target_date?: string
}

export interface CategoryTargetUpdate {
  target_type?: TargetType
  amount?: string
  target_date?: string | null
}

export interface UnderfundedResponse {
  target_id: string
  category_id: string
  month: string
  target_type: TargetType
  target_amount: string
  funded_this_month: string
  available_now: string
  suggested_monthly: string | null
  months_left: number | null
  underfunded: string
  status: 'UNDERFUNDED' | 'FUNDED' | 'OVERFUNDED'
}
