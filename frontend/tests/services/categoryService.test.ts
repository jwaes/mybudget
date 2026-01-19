/**
 * Unit tests for categoryService.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { categoryService } from '@/services/categoryService'

vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import { api } from '@/services/api'

describe('categoryService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // Category Group operations

  describe('createGroup', () => {
    it('should call POST /categories/groups with group data', async () => {
      const mockGroup = {
        id: 'grp-123',
        name: 'Bills',
        sort_order: 1,
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T00:00:00Z',
      }
      vi.mocked(api.post).mockResolvedValue(mockGroup)

      const createData = { name: 'Bills', sort_order: 1 }
      const result = await categoryService.createGroup(createData)

      expect(api.post).toHaveBeenCalledWith('/categories/groups', createData)
      expect(result).toEqual(mockGroup)
    })

    it('should propagate errors from api.post', async () => {
      const error = new Error('Validation error')
      vi.mocked(api.post).mockRejectedValue(error)

      await expect(
        categoryService.createGroup({ name: '', sort_order: 0 })
      ).rejects.toThrow('Validation error')
    })
  })

  describe('listGroups', () => {
    it('should call GET /categories/groups', async () => {
      const mockGroups = [
        {
          id: 'grp-1',
          name: 'Bills',
          sort_order: 1,
          created_at: '2026-01-17T00:00:00Z',
          updated_at: '2026-01-17T00:00:00Z',
        },
        {
          id: 'grp-2',
          name: 'Savings',
          sort_order: 2,
          created_at: '2026-01-17T00:00:00Z',
          updated_at: '2026-01-17T00:00:00Z',
        },
      ]
      vi.mocked(api.get).mockResolvedValue(mockGroups)

      const result = await categoryService.listGroups()

      expect(api.get).toHaveBeenCalledWith('/categories/groups')
      expect(result).toEqual(mockGroups)
      expect(result).toHaveLength(2)
    })

    it('should return empty array when no groups exist', async () => {
      vi.mocked(api.get).mockResolvedValue([])

      const result = await categoryService.listGroups()

      expect(result).toEqual([])
    })
  })

  describe('updateGroup', () => {
    it('should call PUT /categories/groups/:id with update data', async () => {
      const mockGroup = {
        id: 'grp-123',
        name: 'Updated Bills',
        sort_order: 1,
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T01:00:00Z',
      }
      vi.mocked(api.put).mockResolvedValue(mockGroup)

      const updateData = { name: 'Updated Bills' }
      const result = await categoryService.updateGroup('grp-123', updateData)

      expect(api.put).toHaveBeenCalledWith('/categories/groups/grp-123', updateData)
      expect(result).toEqual(mockGroup)
    })
  })

  describe('deleteGroup', () => {
    it('should call DELETE /categories/groups/:id', async () => {
      vi.mocked(api.delete).mockResolvedValue(undefined)

      await categoryService.deleteGroup('grp-123')

      expect(api.delete).toHaveBeenCalledWith('/categories/groups/grp-123')
    })

    it('should propagate errors when group has categories', async () => {
      const error = new Error('Cannot delete group with categories')
      vi.mocked(api.delete).mockRejectedValue(error)

      await expect(categoryService.deleteGroup('grp-123')).rejects.toThrow(
        'Cannot delete group with categories'
      )
    })
  })

  // Category operations

  describe('create', () => {
    it('should call POST /categories/ with category data', async () => {
      const mockCategory = {
        id: 'cat-123',
        name: 'Electricity',
        group_id: 'grp-1',
        sort_order: 1,
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T00:00:00Z',
      }
      vi.mocked(api.post).mockResolvedValue(mockCategory)

      const createData = {
        name: 'Electricity',
        group_id: 'grp-1',
        sort_order: 1,
      }
      const result = await categoryService.create(createData)

      expect(api.post).toHaveBeenCalledWith('/categories/', createData)
      expect(result).toEqual(mockCategory)
    })

    it('should propagate errors from api.post', async () => {
      const error = new Error('Group not found')
      vi.mocked(api.post).mockRejectedValue(error)

      await expect(
        categoryService.create({
          name: 'Test',
          group_id: 'invalid',
          sort_order: 1,
        })
      ).rejects.toThrow('Group not found')
    })
  })

  describe('list', () => {
    it('should call GET /categories/', async () => {
      const mockResponse = {
        groups: [
          {
            id: 'grp-1',
            name: 'Bills',
            sort_order: 1,
            categories: [
              {
                id: 'cat-1',
                name: 'Electricity',
                group_id: 'grp-1',
                sort_order: 1,
              },
              {
                id: 'cat-2',
                name: 'Water',
                group_id: 'grp-1',
                sort_order: 2,
              },
            ],
          },
        ],
        total_categories: 2,
      }
      vi.mocked(api.get).mockResolvedValue(mockResponse)

      const result = await categoryService.list()

      expect(api.get).toHaveBeenCalledWith('/categories/')
      expect(result).toEqual(mockResponse)
    })

    it('should return empty groups when no categories exist', async () => {
      const mockResponse = { groups: [], total_categories: 0 }
      vi.mocked(api.get).mockResolvedValue(mockResponse)

      const result = await categoryService.list()

      expect(result.groups).toHaveLength(0)
      expect(result.total_categories).toBe(0)
    })
  })

  describe('get', () => {
    it('should call GET /categories/:id', async () => {
      const mockCategory = {
        id: 'cat-123',
        name: 'Groceries',
        group_id: 'grp-1',
        sort_order: 3,
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T00:00:00Z',
      }
      vi.mocked(api.get).mockResolvedValue(mockCategory)

      const result = await categoryService.get('cat-123')

      expect(api.get).toHaveBeenCalledWith('/categories/cat-123')
      expect(result).toEqual(mockCategory)
    })

    it('should propagate errors when category not found', async () => {
      const error = new Error('Category not found')
      vi.mocked(api.get).mockRejectedValue(error)

      await expect(categoryService.get('nonexistent')).rejects.toThrow(
        'Category not found'
      )
    })
  })

  describe('update', () => {
    it('should call PUT /categories/:id with update data', async () => {
      const mockCategory = {
        id: 'cat-123',
        name: 'Updated Category',
        group_id: 'grp-1',
        sort_order: 3,
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T01:00:00Z',
      }
      vi.mocked(api.put).mockResolvedValue(mockCategory)

      const updateData = { name: 'Updated Category' }
      const result = await categoryService.update('cat-123', updateData)

      expect(api.put).toHaveBeenCalledWith('/categories/cat-123', updateData)
      expect(result).toEqual(mockCategory)
    })

    it('should allow moving category to a different group', async () => {
      const mockCategory = {
        id: 'cat-123',
        name: 'Category',
        group_id: 'grp-2',
        sort_order: 1,
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T01:00:00Z',
      }
      vi.mocked(api.put).mockResolvedValue(mockCategory)

      const updateData = { group_id: 'grp-2' }
      const result = await categoryService.update('cat-123', updateData)

      expect(api.put).toHaveBeenCalledWith('/categories/cat-123', updateData)
      expect(result.group_id).toBe('grp-2')
    })
  })

  describe('delete', () => {
    it('should call DELETE /categories/:id', async () => {
      vi.mocked(api.delete).mockResolvedValue(undefined)

      await categoryService.delete('cat-123')

      expect(api.delete).toHaveBeenCalledWith('/categories/cat-123')
    })

    it('should propagate errors when category has transactions', async () => {
      const error = new Error('Cannot delete category with transactions')
      vi.mocked(api.delete).mockRejectedValue(error)

      await expect(categoryService.delete('cat-123')).rejects.toThrow(
        'Cannot delete category with transactions'
      )
    })
  })

  describe('assignFunds', () => {
    it('should call POST /categories/:id/assign with assignment data', async () => {
      const mockAssignment = {
        id: 'asgn-123',
        category_id: 'cat-123',
        amount: 500,
        month: '2026-01',
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T00:00:00Z',
      }
      vi.mocked(api.post).mockResolvedValue(mockAssignment)

      const assignData = { amount: 500, month: '2026-01' }
      const result = await categoryService.assignFunds('cat-123', assignData)

      expect(api.post).toHaveBeenCalledWith('/categories/cat-123/assign', assignData)
      expect(result).toEqual(mockAssignment)
    })

    it('should allow assigning negative amounts (unassigning)', async () => {
      const mockAssignment = {
        id: 'asgn-123',
        category_id: 'cat-123',
        amount: -200,
        month: '2026-01',
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T00:00:00Z',
      }
      vi.mocked(api.post).mockResolvedValue(mockAssignment)

      const assignData = { amount: -200, month: '2026-01' }
      const result = await categoryService.assignFunds('cat-123', assignData)

      expect(api.post).toHaveBeenCalledWith('/categories/cat-123/assign', assignData)
      expect(result.amount).toBe(-200)
    })

    it('should propagate errors when assignment fails', async () => {
      const error = new Error('Insufficient funds')
      vi.mocked(api.post).mockRejectedValue(error)

      await expect(
        categoryService.assignFunds('cat-123', { amount: 1000000, month: '2026-01' })
      ).rejects.toThrow('Insufficient funds')
    })
  })
})
