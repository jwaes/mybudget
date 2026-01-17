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
} from '@/types/transaction'

/**
 * Transaction query parameters.
 */
interface TransactionQueryParams {
  account_id?: string
  state?: TransactionState
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
}

export default transactionService
