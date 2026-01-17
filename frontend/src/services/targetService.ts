/**
 * Target service for MyBudget.
 *
 * Handles all API calls related to spending targets.
 */

import { api } from './api'
import type {
  CategoryTarget,
  CategoryTargetCreate,
  CategoryTargetUpdate,
  UnderfundedResponse,
} from '@/types/target'

/**
 * Create a new category target.
 */
export async function createTarget(data: CategoryTargetCreate): Promise<CategoryTarget> {
  return api.post<CategoryTarget>('/targets/', data)
}

/**
 * Get all targets for the current user.
 */
export async function getTargets(): Promise<CategoryTarget[]> {
  return api.get<CategoryTarget[]>('/targets/')
}

/**
 * Get a specific target by ID.
 */
export async function getTarget(targetId: string): Promise<CategoryTarget> {
  return api.get<CategoryTarget>(`/targets/${targetId}`)
}

/**
 * Update a target.
 */
export async function updateTarget(
  targetId: string,
  data: CategoryTargetUpdate
): Promise<CategoryTarget> {
  return api.put<CategoryTarget>(`/targets/${targetId}`, data)
}

/**
 * Delete a target.
 */
export async function deleteTarget(targetId: string): Promise<void> {
  return api.delete<void>(`/targets/${targetId}`)
}

/**
 * Calculate underfunded amount for a target.
 * @param targetId - The target ID
 * @param month - Optional month (YYYY-MM-DD format), defaults to current month
 */
export async function getUnderfunded(
  targetId: string,
  month?: string
): Promise<UnderfundedResponse> {
  const params = month ? `?month=${month}` : ''
  return api.get<UnderfundedResponse>(`/targets/${targetId}/underfunded${params}`)
}

/**
 * Get target for a specific category (convenience function).
 * Returns null if the category has no target.
 */
export async function getTargetByCategory(categoryId: string): Promise<CategoryTarget | null> {
  const targets = await getTargets()
  return targets.find((t) => t.category_id === categoryId) || null
}

export const targetService = {
  createTarget,
  getTargets,
  getTarget,
  updateTarget,
  deleteTarget,
  getUnderfunded,
  getTargetByCategory,
}

export default targetService
