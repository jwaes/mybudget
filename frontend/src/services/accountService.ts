/**
 * Account service for MyBudget.
 *
 * Handles account CRUD operations.
 */

import { api } from './api'
import type {
  Account,
  AccountCreate,
  AccountUpdate,
  AccountListResponse,
} from '@/types/account'

/**
 * Account service with methods for managing accounts.
 */
export const accountService = {
  /**
   * Create a new account.
   *
   * @param data - Account creation data
   * @returns The created account
   */
  async create(data: AccountCreate): Promise<Account> {
    return api.post<Account>('/accounts/', data)
  },

  /**
   * Get all accounts for the current user.
   *
   * @returns List of accounts
   */
  async list(): Promise<AccountListResponse> {
    return api.get<AccountListResponse>('/accounts/')
  },

  /**
   * Get a single account by ID.
   *
   * @param id - Account ID
   * @returns The account
   */
  async get(id: string): Promise<Account> {
    return api.get<Account>(`/accounts/${id}`)
  },

  /**
   * Update an account.
   *
   * @param id - Account ID
   * @param data - Update data
   * @returns The updated account
   */
  async update(id: string, data: AccountUpdate): Promise<Account> {
    return api.put<Account>(`/accounts/${id}`, data)
  },

  /**
   * Delete an account.
   *
   * @param id - Account ID
   */
  async delete(id: string): Promise<void> {
    return api.delete(`/accounts/${id}`)
  },

  /**
   * Retry sync for an account.
   *
   * @param id - Account ID
   * @returns The updated account with new sync status
   */
  async retrySync(id: string): Promise<Account> {
    return api.post<Account>(`/accounts/${id}/retry-sync`)
  },
}

export default accountService
