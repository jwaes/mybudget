/**
 * Unit tests for budgetService.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { budgetService } from '@/services/budgetService'

vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import { api } from '@/services/api'

describe('budgetService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getMonthView', () => {
    it('should call GET /budget/:month with month parameter', async () => {
      const mockBudgetView = {
        month: '2026-01',
        to_assign: '1500.00',
        groups: [
          {
            id: 'grp-1',
            name: 'Bills',
            display_order: 1,
            categories: [
              {
                id: 'cat-1',
                name: 'Rent',
                funded_this_month: '1000.00',
                activity: '0.00',
                available: '1000.00',
              },
            ],
          },
        ],
      }
      vi.mocked(api.get).mockResolvedValue(mockBudgetView)

      const result = await budgetService.getMonthView('2026-01')

      expect(api.get).toHaveBeenCalledWith('/budget/2026-01')
      expect(result).toEqual(mockBudgetView)
    })

    it('should handle empty groups', async () => {
      const mockBudgetView = {
        month: '2026-02',
        to_assign: '0.00',
        groups: [],
      }
      vi.mocked(api.get).mockResolvedValue(mockBudgetView)

      const result = await budgetService.getMonthView('2026-02')

      expect(result.groups).toHaveLength(0)
      expect(result.to_assign).toBe('0.00')
    })

    it('should propagate errors from api.get', async () => {
      const error = new Error('Network error')
      vi.mocked(api.get).mockRejectedValue(error)

      await expect(budgetService.getMonthView('2026-01')).rejects.toThrow('Network error')
    })
  })

  describe('assignFunds', () => {
    it('should call POST /categories/:categoryId/assign with assignment data', async () => {
      const mockAssignment = {
        id: 'assign-123',
        user_id: 'user-1',
        category_id: 'cat-1',
        amount: '500.00',
        month: '2026-01',
        created_at: '2026-01-19T00:00:00Z',
      }
      vi.mocked(api.post).mockResolvedValue(mockAssignment)

      const assignData = {
        amount: '500.00',
        month: '2026-01',
      }
      const result = await budgetService.assignFunds('cat-1', assignData)

      expect(api.post).toHaveBeenCalledWith('/categories/cat-1/assign', assignData)
      expect(result).toEqual(mockAssignment)
    })

    it('should allow negative amounts for unassigning funds', async () => {
      const mockAssignment = {
        id: 'assign-124',
        user_id: 'user-1',
        category_id: 'cat-1',
        amount: '-200.00',
        month: '2026-01',
        created_at: '2026-01-19T00:00:00Z',
      }
      vi.mocked(api.post).mockResolvedValue(mockAssignment)

      const assignData = {
        amount: '-200.00',
        month: '2026-01',
      }
      const result = await budgetService.assignFunds('cat-1', assignData)

      expect(api.post).toHaveBeenCalledWith('/categories/cat-1/assign', assignData)
      expect(result.amount).toBe('-200.00')
    })

    it('should propagate errors from api.post', async () => {
      const error = new Error('Insufficient funds')
      vi.mocked(api.post).mockRejectedValue(error)

      await expect(
        budgetService.assignFunds('cat-1', { amount: '1000.00', month: '2026-01' })
      ).rejects.toThrow('Insufficient funds')
    })
  })

  describe('getUnderfundedSummary', () => {
    it('should call GET /budget/:month/underfunded-summary', async () => {
      const mockSummary = {
        total_underfunded: '750.00',
        categories_underfunded: 2,
        categories: [
          {
            category_id: 'cat-1',
            category_name: 'Groceries',
            underfunded: '200.00',
          },
          {
            category_id: 'cat-2',
            category_name: 'Utilities',
            underfunded: '550.00',
          },
        ],
      }
      vi.mocked(api.get).mockResolvedValue(mockSummary)

      const result = await budgetService.getUnderfundedSummary('2026-01')

      expect(api.get).toHaveBeenCalledWith('/budget/2026-01/underfunded-summary')
      expect(result).toEqual(mockSummary)
    })

    it('should handle no underfunded categories', async () => {
      const mockSummary = {
        total_underfunded: '0.00',
        categories_underfunded: 0,
        categories: [],
      }
      vi.mocked(api.get).mockResolvedValue(mockSummary)

      const result = await budgetService.getUnderfundedSummary('2026-01')

      expect(result.categories_underfunded).toBe(0)
      expect(result.categories).toHaveLength(0)
    })

    it('should propagate errors from api.get', async () => {
      const error = new Error('Server error')
      vi.mocked(api.get).mockRejectedValue(error)

      await expect(budgetService.getUnderfundedSummary('2026-01')).rejects.toThrow('Server error')
    })
  })

  describe('fundUnderfunded', () => {
    it('should call POST /budget/:month/fund-underfunded/:categoryId', async () => {
      const mockResult = {
        category_id: 'cat-1',
        amount_funded: '200.00',
        amount_requested: '200.00',
        is_partial: false,
      }
      vi.mocked(api.post).mockResolvedValue(mockResult)

      const result = await budgetService.fundUnderfunded('2026-01', 'cat-1')

      expect(api.post).toHaveBeenCalledWith('/budget/2026-01/fund-underfunded/cat-1')
      expect(result).toEqual(mockResult)
    })

    it('should handle partial funding', async () => {
      const mockResult = {
        category_id: 'cat-1',
        amount_funded: '100.00',
        amount_requested: '200.00',
        is_partial: true,
      }
      vi.mocked(api.post).mockResolvedValue(mockResult)

      const result = await budgetService.fundUnderfunded('2026-01', 'cat-1')

      expect(result.is_partial).toBe(true)
      expect(result.amount_funded).not.toBe(result.amount_requested)
    })

    it('should propagate errors from api.post', async () => {
      const error = new Error('Category not found')
      vi.mocked(api.post).mockRejectedValue(error)

      await expect(budgetService.fundUnderfunded('2026-01', 'nonexistent')).rejects.toThrow(
        'Category not found'
      )
    })
  })

  describe('fundAllUnderfunded', () => {
    it('should call POST /budget/:month/fund-all-underfunded', async () => {
      const mockResult = {
        total_funded: '750.00',
        total_underfunded: '750.00',
        categories_funded: 3,
        funded_categories: [
          {
            category_id: 'cat-1',
            category_name: 'Groceries',
            amount_funded: '200.00',
          },
          {
            category_id: 'cat-2',
            category_name: 'Utilities',
            amount_funded: '300.00',
          },
          {
            category_id: 'cat-3',
            category_name: 'Gas',
            amount_funded: '250.00',
          },
        ],
        is_partial: false,
      }
      vi.mocked(api.post).mockResolvedValue(mockResult)

      const result = await budgetService.fundAllUnderfunded('2026-01')

      expect(api.post).toHaveBeenCalledWith('/budget/2026-01/fund-all-underfunded')
      expect(result).toEqual(mockResult)
    })

    it('should handle partial funding when insufficient funds', async () => {
      const mockResult = {
        total_funded: '500.00',
        total_underfunded: '1000.00',
        categories_funded: 2,
        funded_categories: [
          {
            category_id: 'cat-1',
            category_name: 'Groceries',
            amount_funded: '300.00',
          },
          {
            category_id: 'cat-2',
            category_name: 'Utilities',
            amount_funded: '200.00',
          },
        ],
        is_partial: true,
      }
      vi.mocked(api.post).mockResolvedValue(mockResult)

      const result = await budgetService.fundAllUnderfunded('2026-01')

      expect(result.is_partial).toBe(true)
      expect(result.total_funded).not.toBe(result.total_underfunded)
    })

    it('should handle no underfunded categories', async () => {
      const mockResult = {
        total_funded: '0.00',
        total_underfunded: '0.00',
        categories_funded: 0,
        funded_categories: [],
        is_partial: false,
      }
      vi.mocked(api.post).mockResolvedValue(mockResult)

      const result = await budgetService.fundAllUnderfunded('2026-01')

      expect(result.categories_funded).toBe(0)
      expect(result.funded_categories).toHaveLength(0)
    })

    it('should propagate errors from api.post', async () => {
      const error = new Error('No funds available')
      vi.mocked(api.post).mockRejectedValue(error)

      await expect(budgetService.fundAllUnderfunded('2026-01')).rejects.toThrow('No funds available')
    })
  })
})
