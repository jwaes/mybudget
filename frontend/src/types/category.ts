/**
 * Category types for MyBudget.
 */

export interface Category {
  id: string
  user_id: string
  group_id: string
  name: string
  created_at: string
  updated_at: string
}

export interface CategoryGroup {
  id: string
  user_id: string
  name: string
  display_order: number
  created_at: string
  updated_at: string
}

export interface CategoryGroupCreate {
  name: string
  display_order?: number
}

export interface CategoryGroupUpdate {
  name?: string
  display_order?: number
}

export interface CategoryCreate {
  group_id: string
  name: string
}

export interface CategoryUpdate {
  group_id?: string
  name?: string
}

export interface CategoryGroupWithCategories extends CategoryGroup {
  categories: Category[]
}

export interface CategoryListResponse {
  groups: CategoryGroupWithCategories[]
  total_groups: number
  total_categories: number
}
