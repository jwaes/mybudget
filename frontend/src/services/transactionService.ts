/**
 * Transaction service for MyBudget.
 *
 * Handles transaction CRUD operations and approval workflow.
 */

import { api } from './api'
import type {
  Transaction,
  TransactionCreate,
  TransactionUpdate,
  TransactionApprove,
  TransactionListResponse,
  TransactionState,
  TransactionBulkApprove,
  TransactionBulkResult,
} from '@/types/transaction'

/**
 * Transaction query parameters.
 */
interface TransactionQueryParams {
  account_id?: string
  state?: TransactionState
  payee_search?: string
  memo_search?: string
  date_from?: string  // ISO date string YYYY-MM-DD
  date_to?: string    // ISO date string YYYY-MM-DD
  amount_min?: string // decimal string
  amount_max?: string // decimal string
  category_id?: string
  uncategorized_only?: boolean
  limit?: number
  offset?: number
}

/**
 * Transaction service with methods for managing transactions.
 */
export const transactionService = {
  /**
   * Create a new transaction.
   *
   * @param data - Transaction creation data
   * @returns The created transaction
   */
  async create(data: TransactionCreate): Promise<Transaction> {
    return api.post<Transaction>('/transactions/', data)
  },

  /**
   * Get all transactions for the current user with optional filters.
   *
   * @param params - Query parameters for filtering
   * @returns List of transactions
   */
  async list(params?: TransactionQueryParams): Promise<TransactionListResponse> {
    const queryParams = new URLSearchParams()
    if (params?.account_id) queryParams.set('account_id', params.account_id)
    if (params?.state) queryParams.set('state', params.state)
    if (params?.payee_search) queryParams.set('payee_search', params.payee_search)
    if (params?.memo_search) queryParams.set('memo_search', params.memo_search)
    if (params?.date_from) queryParams.set('date_from', params.date_from)
    if (params?.date_to) queryParams.set('date_to', params.date_to)
    if (params?.amount_min) queryParams.set('amount_min', params.amount_min)
    if (params?.amount_max) queryParams.set('amount_max', params.amount_max)
    if (params?.category_id) queryParams.set('category_id', params.category_id)
    if (params?.uncategorized_only) queryParams.set('uncategorized_only', 'true')
    if (params?.limit) queryParams.set('limit', params.limit.toString())
    if (params?.offset) queryParams.set('offset', params.offset.toString())

    const query = queryParams.toString()
    const url = query ? `/transactions/?${query}` : '/transactions/'
    return api.get<TransactionListResponse>(url)
  },

  /**
   * Get inbox (unapproved) transactions.
   *
   * @param params - Query parameters for filtering
   * @returns List of inbox transactions
   */
  async listInbox(params?: Omit<TransactionQueryParams, 'state'>): Promise<TransactionListResponse> {
    const queryParams = new URLSearchParams()
    if (params?.account_id) queryParams.set('account_id', params.account_id)
    if (params?.limit) queryParams.set('limit', params.limit.toString())
    if (params?.offset) queryParams.set('offset', params.offset.toString())

    const query = queryParams.toString()
    const url = query ? `/transactions/inbox?${query}` : '/transactions/inbox'
    return api.get<TransactionListResponse>(url)
  },

  /**
   * Get a single transaction by ID.
   *
   * @param id - Transaction ID
   * @returns The transaction
   */
  async get(id: string): Promise<Transaction> {
    return api.get<Transaction>(`/transactions/${id}`)
  },

  /**
   * Update a transaction.
   *
   * @param id - Transaction ID
   * @param data - Update data
   * @returns The updated transaction
   */
  async update(id: string, data: TransactionUpdate): Promise<Transaction> {
    return api.put<Transaction>(`/transactions/${id}`, data)
  },

  /**
   * Approve a transaction with a category.
   *
   * @param id - Transaction ID
   * @param data - Approval data with category
   * @returns The approved transaction
   */
  async approve(id: string, data: TransactionApprove): Promise<Transaction> {
    return api.post<Transaction>(`/transactions/${id}/approve`, data)
  },

  /**
   * Unapprove a transaction (move back to inbox).
   *
   * @param id - Transaction ID
   * @returns The unapproved transaction
   */
  async unapprove(id: string): Promise<Transaction> {
    return api.post<Transaction>(`/transactions/${id}/unapprove`)
  },

  /**
   * Delete a transaction.
   *
   * @param id - Transaction ID
   */
  async delete(id: string): Promise<void> {
    return api.delete(`/transactions/${id}`)
  },

  /**
   * Get count of uncategorized transactions.
   *
   * @returns Number of uncategorized transactions
   */
  async getUncategorizedCount(): Promise<number> {
    const response = await this.list({ uncategorized_only: true, limit: 1 })
    return response.total
  },

  /**
   * Batch approve multiple transactions with the same category (FR-045).
   *
   * @param data - Bulk approval data with transaction IDs and category
   * @returns Result with success/failure counts
   */
  async batchApprove(data: TransactionBulkApprove): Promise<TransactionBulkResult> {
    return api.post<TransactionBulkResult>('/transactions/batch-approve', data)
  },
}

export default transactionService
