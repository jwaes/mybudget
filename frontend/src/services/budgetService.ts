/**
 * Budget service for MyBudget.
 *
 * Handles budget month view and fund assignment operations.
 */

import { api } from './api'
import type {
  BudgetMonthView,
  Assignment,
  AssignmentCreate,
  UnderfundedSummary,
  FundSingleResult,
  FundAllResult,
} from '@/types/budget'

/**
 * Budget service with methods for budget operations.
 */
export const budgetService = {
  /**
   * Get budget month view.
   *
   * @param month - Month in YYYY-MM format
   * @returns Budget month view with all categories and their budget info
   */
  async getMonthView(month: string): Promise<BudgetMonthView> {
    return api.get<BudgetMonthView>(`/budget/${month}`)
  },

  /**
   * Assign (or unassign) funds to a category.
   *
   * @param categoryId - Category ID to assign funds to
   * @param data - Assignment data (amount and month)
   * @returns The created assignment
   */
  async assignFunds(categoryId: string, data: AssignmentCreate): Promise<Assignment> {
    return api.post<Assignment>(`/categories/${categoryId}/assign`, data)
  },

  /**
   * Get underfunded summary for a month.
   *
   * @param month - Month in YYYY-MM format
   * @returns Summary with total underfunded and per-category breakdown
   */
  async getUnderfundedSummary(month: string): Promise<UnderfundedSummary> {
    return api.get<UnderfundedSummary>(`/budget/${month}/underfunded-summary`)
  },

  /**
   * Fund a single underfunded category.
   *
   * @param month - Month in YYYY-MM format
   * @param categoryId - Category ID to fund
   * @returns Funding result with amount funded and partial status
   */
  async fundUnderfunded(month: string, categoryId: string): Promise<FundSingleResult> {
    return api.post<FundSingleResult>(`/budget/${month}/fund-underfunded/${categoryId}`)
  },

  /**
   * Fund all underfunded categories in priority order.
   *
   * @param month - Month in YYYY-MM format
   * @returns Funding result with total funded and funded categories
   */
  async fundAllUnderfunded(month: string): Promise<FundAllResult> {
    return api.post<FundAllResult>(`/budget/${month}/fund-all-underfunded`)
  },
}

export default budgetService
