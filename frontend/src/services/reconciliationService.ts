/**
 * Reconciliation service for MyBudget.
 *
 * Handles account reconciliation workflow.
 */

import { api } from './api'
import type {
  Reconciliation,
  ReconciliationCreate,
  ReconciliationMarkCleared,
  ReconciliationUnmarkCleared,
  ReconciliationCreateAdjustment,
  ReconciliationBalanceResponse,
  ReconciliationAdjustmentResponse,
} from '@/types/reconciliation'

/**
 * Reconciliation service with methods for managing account reconciliations.
 */
export const reconciliationService = {
  /**
   * Start a new reconciliation session.
   *
   * @param data - Reconciliation creation data
   * @returns The created reconciliation
   */
  async start(data: ReconciliationCreate): Promise<Reconciliation> {
    return api.post<Reconciliation>('/reconciliations/', data)
  },

  /**
   * Get a reconciliation by ID.
   *
   * @param id - Reconciliation ID
   * @returns The reconciliation
   */
  async get(id: string): Promise<Reconciliation> {
    return api.get<Reconciliation>(`/reconciliations/${id}`)
  },

  /**
   * List reconciliations for an account.
   *
   * @param accountId - Optional account ID to filter by
   * @returns List of reconciliations
   */
  async list(accountId?: string): Promise<Reconciliation[]> {
    const params = accountId ? `?account_id=${accountId}` : ''
    return api.get<Reconciliation[]>(`/reconciliations/${params}`)
  },

  /**
   * Mark transactions as cleared during reconciliation.
   *
   * @param reconciliationId - Reconciliation ID
   * @param data - Transaction IDs to mark as cleared
   * @returns Updated balance information
   */
  async markCleared(
    reconciliationId: string,
    data: ReconciliationMarkCleared
  ): Promise<ReconciliationBalanceResponse> {
    return api.put<ReconciliationBalanceResponse>(
      `/reconciliations/${reconciliationId}/mark-cleared`,
      data
    )
  },

  /**
   * Unmark transactions as cleared.
   *
   * @param reconciliationId - Reconciliation ID
   * @param data - Transaction IDs to unmark
   * @returns Updated balance information
   */
  async unmarkCleared(
    reconciliationId: string,
    data: ReconciliationUnmarkCleared
  ): Promise<ReconciliationBalanceResponse> {
    return api.put<ReconciliationBalanceResponse>(
      `/reconciliations/${reconciliationId}/unmark-cleared`,
      data
    )
  },

  /**
   * Create an adjustment transaction to resolve discrepancy.
   *
   * @param reconciliationId - Reconciliation ID
   * @param data - Category ID for the adjustment
   * @returns The created adjustment transaction
   */
  async createAdjustment(
    reconciliationId: string,
    data: ReconciliationCreateAdjustment
  ): Promise<ReconciliationAdjustmentResponse> {
    return api.post<ReconciliationAdjustmentResponse>(
      `/reconciliations/${reconciliationId}/create-adjustment`,
      data
    )
  },

  /**
   * Complete a reconciliation session.
   *
   * @param reconciliationId - Reconciliation ID
   * @returns The completed reconciliation
   */
  async complete(reconciliationId: string): Promise<Reconciliation> {
    return api.post<Reconciliation>(
      `/reconciliations/${reconciliationId}/complete`
    )
  },

  /**
   * Cancel an in-progress reconciliation.
   *
   * @param reconciliationId - Reconciliation ID
   */
  async cancel(reconciliationId: string): Promise<void> {
    return api.delete(`/reconciliations/${reconciliationId}`)
  },
}

export default reconciliationService
