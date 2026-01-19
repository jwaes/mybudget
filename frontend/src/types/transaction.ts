/**
 * Transaction types for MyBudget.
 */

export type TransactionState = 'INBOX' | 'APPROVED' | 'CLEARED'

export interface Transaction {
  id: string
  user_id: string
  account_id: string
  category_id: string | null
  date: string
  payee: string
  amount: string
  memo: string | null
  state: TransactionState
  created_at: string
  updated_at: string
  approved_at: string | null
  cleared_at: string | null
}

export interface TransactionCreate {
  account_id: string
  date: string
  payee: string
  amount: string
  memo?: string | null
  category_id?: string | null
}

export interface TransactionUpdate {
  date?: string
  payee?: string
  amount?: string
  memo?: string | null
  category_id?: string | null
}

export interface TransactionApprove {
  category_id?: string
}

export interface TransactionListResponse {
  transactions: Transaction[]
  total: number
}

export interface TransactionBulkApprove {
  transaction_ids: string[]
  category_id: string
}

export interface TransactionBulkResult {
  success_count: number
  failed_count: number
  failed_ids: string[]
}
