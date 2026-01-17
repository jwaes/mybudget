/**
 * Category service for MyBudget.
 *
 * Handles category and category group CRUD operations.
 */

import { api } from './api'
import type {
  Category,
  CategoryGroup,
  CategoryCreate,
  CategoryUpdate,
  CategoryGroupCreate,
  CategoryGroupUpdate,
  CategoryListResponse,
} from '@/types/category'
import type { Assignment, AssignmentCreate } from '@/types/budget'

/**
 * Category service with methods for managing categories and groups.
 */
export const categoryService = {
  // Category Group operations

  /**
   * Create a new category group.
   *
   * @param data - Category group creation data
   * @returns The created category group
   */
  async createGroup(data: CategoryGroupCreate): Promise<CategoryGroup> {
    return api.post<CategoryGroup>('/categories/groups', data)
  },

  /**
   * Get all category groups for the current user.
   *
   * @returns List of category groups
   */
  async listGroups(): Promise<CategoryGroup[]> {
    return api.get<CategoryGroup[]>('/categories/groups')
  },

  /**
   * Update a category group.
   *
   * @param id - Category group ID
   * @param data - Update data
   * @returns The updated category group
   */
  async updateGroup(id: string, data: CategoryGroupUpdate): Promise<CategoryGroup> {
    return api.put<CategoryGroup>(`/categories/groups/${id}`, data)
  },

  /**
   * Delete a category group.
   *
   * @param id - Category group ID
   */
  async deleteGroup(id: string): Promise<void> {
    return api.delete(`/categories/groups/${id}`)
  },

  // Category operations

  /**
   * Create a new category.
   *
   * @param data - Category creation data
   * @returns The created category
   */
  async create(data: CategoryCreate): Promise<Category> {
    return api.post<Category>('/categories/', data)
  },

  /**
   * Get all categories with their groups.
   *
   * @returns Categories organized by groups
   */
  async list(): Promise<CategoryListResponse> {
    return api.get<CategoryListResponse>('/categories/')
  },

  /**
   * Get a single category by ID.
   *
   * @param id - Category ID
   * @returns The category
   */
  async get(id: string): Promise<Category> {
    return api.get<Category>(`/categories/${id}`)
  },

  /**
   * Update a category.
   *
   * @param id - Category ID
   * @param data - Update data
   * @returns The updated category
   */
  async update(id: string, data: CategoryUpdate): Promise<Category> {
    return api.put<Category>(`/categories/${id}`, data)
  },

  /**
   * Delete a category.
   *
   * @param id - Category ID
   */
  async delete(id: string): Promise<void> {
    return api.delete(`/categories/${id}`)
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
}

export default categoryService
