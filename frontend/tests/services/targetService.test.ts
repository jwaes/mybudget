/**
 * Unit tests for targetService.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  targetService,
  createTarget,
  getTargets,
  getTarget,
  updateTarget,
  deleteTarget,
  getUnderfunded,
  getTargetByCategory,
} from '@/services/targetService'

vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import { api } from '@/services/api'

describe('targetService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('createTarget', () => {
    it('should call POST /targets/ with target data', async () => {
      const mockTarget = {
        id: 'target-123',
        category_id: 'cat-1',
        category_name: 'Groceries',
        target_type: 'MONTHLY_NEEDED' as const,
        amount: '500.00',
        target_date: null,
        created_at: '2026-01-19T00:00:00Z',
        updated_at: '2026-01-19T00:00:00Z',
      }
      vi.mocked(api.post).mockResolvedValue(mockTarget)

      const createData = {
        category_id: 'cat-1',
        target_type: 'MONTHLY_NEEDED' as const,
        amount: '500.00',
      }
      const result = await createTarget(createData)

      expect(api.post).toHaveBeenCalledWith('/targets/', createData)
      expect(result).toEqual(mockTarget)
    })

    it('should create target with target_date for TARGET_BY_DATE type', async () => {
      const mockTarget = {
        id: 'target-124',
        category_id: 'cat-2',
        category_name: 'Vacation',
        target_type: 'TARGET_BY_DATE' as const,
        amount: '3000.00',
        target_date: '2026-06-01',
        created_at: '2026-01-19T00:00:00Z',
        updated_at: '2026-01-19T00:00:00Z',
      }
      vi.mocked(api.post).mockResolvedValue(mockTarget)

      const createData = {
        category_id: 'cat-2',
        target_type: 'TARGET_BY_DATE' as const,
        amount: '3000.00',
        target_date: '2026-06-01',
      }
      const result = await createTarget(createData)

      expect(api.post).toHaveBeenCalledWith('/targets/', createData)
      expect(result.target_date).toBe('2026-06-01')
    })

    it('should create target with TARGET_BALANCE type', async () => {
      const mockTarget = {
        id: 'target-125',
        category_id: 'cat-3',
        category_name: 'Emergency Fund',
        target_type: 'TARGET_BALANCE' as const,
        amount: '10000.00',
        target_date: null,
        created_at: '2026-01-19T00:00:00Z',
        updated_at: '2026-01-19T00:00:00Z',
      }
      vi.mocked(api.post).mockResolvedValue(mockTarget)

      const createData = {
        category_id: 'cat-3',
        target_type: 'TARGET_BALANCE' as const,
        amount: '10000.00',
      }
      const result = await createTarget(createData)

      expect(result.target_type).toBe('TARGET_BALANCE')
    })

    it('should propagate errors from api.post', async () => {
      const error = new Error('Category already has a target')
      vi.mocked(api.post).mockRejectedValue(error)

      await expect(
        createTarget({
          category_id: 'cat-1',
          target_type: 'MONTHLY_NEEDED',
          amount: '500.00',
        })
      ).rejects.toThrow('Category already has a target')
    })
  })

  describe('getTargets', () => {
    it('should call GET /targets/', async () => {
      const mockTargets = [
        {
          id: 'target-1',
          category_id: 'cat-1',
          category_name: 'Groceries',
          target_type: 'MONTHLY_NEEDED' as const,
          amount: '500.00',
          target_date: null,
          created_at: '2026-01-19T00:00:00Z',
          updated_at: '2026-01-19T00:00:00Z',
        },
        {
          id: 'target-2',
          category_id: 'cat-2',
          category_name: 'Rent',
          target_type: 'MONTHLY_NEEDED' as const,
          amount: '1500.00',
          target_date: null,
          created_at: '2026-01-19T00:00:00Z',
          updated_at: '2026-01-19T00:00:00Z',
        },
      ]
      vi.mocked(api.get).mockResolvedValue(mockTargets)

      const result = await getTargets()

      expect(api.get).toHaveBeenCalledWith('/targets/')
      expect(result).toEqual(mockTargets)
      expect(result).toHaveLength(2)
    })

    it('should return empty array when no targets exist', async () => {
      vi.mocked(api.get).mockResolvedValue([])

      const result = await getTargets()

      expect(result).toHaveLength(0)
    })

    it('should propagate errors from api.get', async () => {
      const error = new Error('Network error')
      vi.mocked(api.get).mockRejectedValue(error)

      await expect(getTargets()).rejects.toThrow('Network error')
    })
  })

  describe('getTarget', () => {
    it('should call GET /targets/:targetId', async () => {
      const mockTarget = {
        id: 'target-123',
        category_id: 'cat-1',
        category_name: 'Groceries',
        target_type: 'MONTHLY_NEEDED' as const,
        amount: '500.00',
        target_date: null,
        created_at: '2026-01-19T00:00:00Z',
        updated_at: '2026-01-19T00:00:00Z',
      }
      vi.mocked(api.get).mockResolvedValue(mockTarget)

      const result = await getTarget('target-123')

      expect(api.get).toHaveBeenCalledWith('/targets/target-123')
      expect(result).toEqual(mockTarget)
    })

    it('should propagate errors when target not found', async () => {
      const error = new Error('Target not found')
      vi.mocked(api.get).mockRejectedValue(error)

      await expect(getTarget('nonexistent')).rejects.toThrow('Target not found')
    })
  })

  describe('updateTarget', () => {
    it('should call PUT /targets/:targetId with update data', async () => {
      const mockTarget = {
        id: 'target-123',
        category_id: 'cat-1',
        category_name: 'Groceries',
        target_type: 'MONTHLY_NEEDED' as const,
        amount: '600.00',
        target_date: null,
        created_at: '2026-01-19T00:00:00Z',
        updated_at: '2026-01-19T01:00:00Z',
      }
      vi.mocked(api.put).mockResolvedValue(mockTarget)

      const updateData = { amount: '600.00' }
      const result = await updateTarget('target-123', updateData)

      expect(api.put).toHaveBeenCalledWith('/targets/target-123', updateData)
      expect(result).toEqual(mockTarget)
    })

    it('should allow updating target_type', async () => {
      const mockTarget = {
        id: 'target-123',
        category_id: 'cat-1',
        category_name: 'Savings',
        target_type: 'TARGET_BALANCE' as const,
        amount: '5000.00',
        target_date: null,
        created_at: '2026-01-19T00:00:00Z',
        updated_at: '2026-01-19T01:00:00Z',
      }
      vi.mocked(api.put).mockResolvedValue(mockTarget)

      const updateData = { target_type: 'TARGET_BALANCE' as const }
      const result = await updateTarget('target-123', updateData)

      expect(api.put).toHaveBeenCalledWith('/targets/target-123', updateData)
      expect(result.target_type).toBe('TARGET_BALANCE')
    })

    it('should allow updating target_date', async () => {
      const mockTarget = {
        id: 'target-123',
        category_id: 'cat-1',
        category_name: 'Vacation',
        target_type: 'TARGET_BY_DATE' as const,
        amount: '3000.00',
        target_date: '2026-12-01',
        created_at: '2026-01-19T00:00:00Z',
        updated_at: '2026-01-19T01:00:00Z',
      }
      vi.mocked(api.put).mockResolvedValue(mockTarget)

      const updateData = { target_date: '2026-12-01' }
      const result = await updateTarget('target-123', updateData)

      expect(result.target_date).toBe('2026-12-01')
    })

    it('should allow clearing target_date', async () => {
      const mockTarget = {
        id: 'target-123',
        category_id: 'cat-1',
        category_name: 'Groceries',
        target_type: 'MONTHLY_NEEDED' as const,
        amount: '500.00',
        target_date: null,
        created_at: '2026-01-19T00:00:00Z',
        updated_at: '2026-01-19T01:00:00Z',
      }
      vi.mocked(api.put).mockResolvedValue(mockTarget)

      const updateData = { target_date: null }
      const result = await updateTarget('target-123', updateData)

      expect(api.put).toHaveBeenCalledWith('/targets/target-123', updateData)
      expect(result.target_date).toBeNull()
    })

    it('should propagate errors from api.put', async () => {
      const error = new Error('Invalid amount')
      vi.mocked(api.put).mockRejectedValue(error)

      await expect(updateTarget('target-123', { amount: '-100.00' })).rejects.toThrow(
        'Invalid amount'
      )
    })
  })

  describe('deleteTarget', () => {
    it('should call DELETE /targets/:targetId', async () => {
      vi.mocked(api.delete).mockResolvedValue(undefined)

      await deleteTarget('target-123')

      expect(api.delete).toHaveBeenCalledWith('/targets/target-123')
    })

    it('should propagate errors from api.delete', async () => {
      const error = new Error('Target not found')
      vi.mocked(api.delete).mockRejectedValue(error)

      await expect(deleteTarget('nonexistent')).rejects.toThrow('Target not found')
    })
  })

  describe('getUnderfunded', () => {
    it('should call GET /targets/:targetId/underfunded without month param', async () => {
      const mockResponse = {
        target_id: 'target-123',
        category_id: 'cat-1',
        month: '2026-01-01',
        target_type: 'MONTHLY_NEEDED' as const,
        target_amount: '500.00',
        funded_this_month: '300.00',
        available_now: '200.00',
        suggested_monthly: null,
        months_left: null,
        underfunded: '200.00',
        status: 'UNDERFUNDED' as const,
      }
      vi.mocked(api.get).mockResolvedValue(mockResponse)

      const result = await getUnderfunded('target-123')

      expect(api.get).toHaveBeenCalledWith('/targets/target-123/underfunded')
      expect(result).toEqual(mockResponse)
    })

    it('should call GET /targets/:targetId/underfunded with month param', async () => {
      const mockResponse = {
        target_id: 'target-123',
        category_id: 'cat-1',
        month: '2026-03-01',
        target_type: 'MONTHLY_NEEDED' as const,
        target_amount: '500.00',
        funded_this_month: '500.00',
        available_now: '500.00',
        suggested_monthly: null,
        months_left: null,
        underfunded: '0.00',
        status: 'FUNDED' as const,
      }
      vi.mocked(api.get).mockResolvedValue(mockResponse)

      const result = await getUnderfunded('target-123', '2026-03-01')

      expect(api.get).toHaveBeenCalledWith('/targets/target-123/underfunded?month=2026-03-01')
      expect(result).toEqual(mockResponse)
    })

    it('should handle OVERFUNDED status', async () => {
      const mockResponse = {
        target_id: 'target-123',
        category_id: 'cat-1',
        month: '2026-01-01',
        target_type: 'MONTHLY_NEEDED' as const,
        target_amount: '500.00',
        funded_this_month: '700.00',
        available_now: '700.00',
        suggested_monthly: null,
        months_left: null,
        underfunded: '0.00',
        status: 'OVERFUNDED' as const,
      }
      vi.mocked(api.get).mockResolvedValue(mockResponse)

      const result = await getUnderfunded('target-123')

      expect(result.status).toBe('OVERFUNDED')
    })

    it('should handle TARGET_BY_DATE with suggested_monthly and months_left', async () => {
      const mockResponse = {
        target_id: 'target-124',
        category_id: 'cat-2',
        month: '2026-01-01',
        target_type: 'TARGET_BY_DATE' as const,
        target_amount: '3000.00',
        funded_this_month: '0.00',
        available_now: '500.00',
        suggested_monthly: '500.00',
        months_left: 5,
        underfunded: '500.00',
        status: 'UNDERFUNDED' as const,
      }
      vi.mocked(api.get).mockResolvedValue(mockResponse)

      const result = await getUnderfunded('target-124')

      expect(result.suggested_monthly).toBe('500.00')
      expect(result.months_left).toBe(5)
    })

    it('should propagate errors from api.get', async () => {
      const error = new Error('Target not found')
      vi.mocked(api.get).mockRejectedValue(error)

      await expect(getUnderfunded('nonexistent')).rejects.toThrow('Target not found')
    })
  })

  describe('getTargetByCategory', () => {
    it('should return target when category has one', async () => {
      const mockTargets = [
        {
          id: 'target-1',
          category_id: 'cat-1',
          category_name: 'Groceries',
          target_type: 'MONTHLY_NEEDED' as const,
          amount: '500.00',
          target_date: null,
          created_at: '2026-01-19T00:00:00Z',
          updated_at: '2026-01-19T00:00:00Z',
        },
        {
          id: 'target-2',
          category_id: 'cat-2',
          category_name: 'Rent',
          target_type: 'MONTHLY_NEEDED' as const,
          amount: '1500.00',
          target_date: null,
          created_at: '2026-01-19T00:00:00Z',
          updated_at: '2026-01-19T00:00:00Z',
        },
      ]
      vi.mocked(api.get).mockResolvedValue(mockTargets)

      const result = await getTargetByCategory('cat-1')

      expect(api.get).toHaveBeenCalledWith('/targets/')
      expect(result).toEqual(mockTargets[0])
    })

    it('should return null when category has no target', async () => {
      const mockTargets = [
        {
          id: 'target-1',
          category_id: 'cat-1',
          category_name: 'Groceries',
          target_type: 'MONTHLY_NEEDED' as const,
          amount: '500.00',
          target_date: null,
          created_at: '2026-01-19T00:00:00Z',
          updated_at: '2026-01-19T00:00:00Z',
        },
      ]
      vi.mocked(api.get).mockResolvedValue(mockTargets)

      const result = await getTargetByCategory('cat-999')

      expect(result).toBeNull()
    })

    it('should return null when no targets exist', async () => {
      vi.mocked(api.get).mockResolvedValue([])

      const result = await getTargetByCategory('cat-1')

      expect(result).toBeNull()
    })

    it('should propagate errors from api.get', async () => {
      const error = new Error('Network error')
      vi.mocked(api.get).mockRejectedValue(error)

      await expect(getTargetByCategory('cat-1')).rejects.toThrow('Network error')
    })
  })

  describe('targetService object', () => {
    it('should expose all service methods', () => {
      expect(targetService.createTarget).toBe(createTarget)
      expect(targetService.getTargets).toBe(getTargets)
      expect(targetService.getTarget).toBe(getTarget)
      expect(targetService.updateTarget).toBe(updateTarget)
      expect(targetService.deleteTarget).toBe(deleteTarget)
      expect(targetService.getUnderfunded).toBe(getUnderfunded)
      expect(targetService.getTargetByCategory).toBe(getTargetByCategory)
    })
  })
})
