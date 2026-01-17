/**
 * Reconciliation types for MyBudget.
 */

export type ReconciliationStatus = 'IN_PROGRESS' | 'COMPLETED'

export interface Reconciliation {
  id: string
  user_id: string
  account_id: string
  statement_balance: string
  statement_date: string
  status: ReconciliationStatus
  adjustment_transaction_id: string | null
  created_at: string
  completed_at: string | null
  cleared_balance: string
  discrepancy: string
}

export interface ReconciliationCreate {
  account_id: string
  statement_balance: string
  statement_date: string
}

export interface ReconciliationMarkCleared {
  transaction_ids: string[]
}

export interface ReconciliationUnmarkCleared {
  transaction_ids: string[]
}

export interface ReconciliationCreateAdjustment {
  category_id: string
}

export interface ReconciliationBalanceResponse {
  cleared_balance: string
  discrepancy: string
}

export interface ReconciliationAdjustmentResponse {
  adjustment_transaction: {
    id: string
    amount: string
    payee: string
    memo: string | null
  }
}

export interface TransactionForReconciliation {
  id: string
  payee: string
  amount: string
  date: string
  state: 'APPROVED' | 'CLEARED'
}
