/**
 * Unit tests for reconciliationService.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { reconciliationService } from '@/services/reconciliationService'
import type {
  Reconciliation,
  ReconciliationBalanceResponse,
  ReconciliationAdjustmentResponse,
} from '@/types/reconciliation'

vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import { api } from '@/services/api'

const mockApi = vi.mocked(api)

// Helper to create a mock reconciliation
function createReconciliation(overrides: Partial<Reconciliation> = {}): Reconciliation {
  return {
    id: 'rec-123',
    user_id: 'user-1',
    account_id: 'acc-1',
    statement_balance: '1000.00',
    statement_date: '2026-01-15',
    status: 'IN_PROGRESS',
    cleared_balance: '950.00',
    created_at: '2026-01-15T10:00:00Z',
    updated_at: '2026-01-15T10:00:00Z',
    completed_at: null,
    ...overrides,
  }
}

describe('reconciliationService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('start', () => {
    it('should call POST /reconciliations/ with data', async () => {
      const mockReconciliation = createReconciliation()
      mockApi.post.mockResolvedValue(mockReconciliation)

      const createData = {
        account_id: 'acc-1',
        statement_balance: '1000.00',
        statement_date: '2026-01-15',
      }
      const result = await reconciliationService.start(createData)

      expect(api.post).toHaveBeenCalledWith('/reconciliations/', createData)
      expect(result).toEqual(mockReconciliation)
    })

    it('should propagate errors from api.post', async () => {
      const error = new Error('Network error')
      mockApi.post.mockRejectedValue(error)

      await expect(
        reconciliationService.start({
          account_id: 'acc-1',
          statement_balance: '1000.00',
          statement_date: '2026-01-15',
        })
      ).rejects.toThrow('Network error')
    })
  })

  describe('get', () => {
    it('should call GET /reconciliations/:id', async () => {
      const mockReconciliation = createReconciliation({ id: 'rec-456' })
      mockApi.get.mockResolvedValue(mockReconciliation)

      const result = await reconciliationService.get('rec-456')

      expect(api.get).toHaveBeenCalledWith('/reconciliations/rec-456')
      expect(result).toEqual(mockReconciliation)
    })

    it('should propagate errors when not found', async () => {
      const error = new Error('Not found')
      mockApi.get.mockRejectedValue(error)

      await expect(reconciliationService.get('nonexistent')).rejects.toThrow('Not found')
    })
  })

  describe('list', () => {
    it('should call GET /reconciliations/ without account filter', async () => {
      const mockReconciliations = [
        createReconciliation({ id: 'rec-1' }),
        createReconciliation({ id: 'rec-2' }),
      ]
      mockApi.get.mockResolvedValue(mockReconciliations)

      const result = await reconciliationService.list()

      expect(api.get).toHaveBeenCalledWith('/reconciliations/')
      expect(result).toEqual(mockReconciliations)
    })

    it('should call GET /reconciliations/?account_id=:id with account filter', async () => {
      const mockReconciliations = [createReconciliation()]
      mockApi.get.mockResolvedValue(mockReconciliations)

      const result = await reconciliationService.list('acc-123')

      expect(api.get).toHaveBeenCalledWith('/reconciliations/?account_id=acc-123')
      expect(result).toEqual(mockReconciliations)
    })
  })

  describe('markCleared', () => {
    it('should call PUT /reconciliations/:id/mark-cleared with transaction IDs', async () => {
      const mockResponse: ReconciliationBalanceResponse = {
        reconciliation_id: 'rec-123',
        cleared_balance: '800.00',
        statement_balance: '1000.00',
        difference: '200.00',
      }
      mockApi.put.mockResolvedValue(mockResponse)

      const data = { transaction_ids: ['txn-1', 'txn-2'] }
      const result = await reconciliationService.markCleared('rec-123', data)

      expect(api.put).toHaveBeenCalledWith('/reconciliations/rec-123/mark-cleared', data)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('unmarkCleared', () => {
    it('should call PUT /reconciliations/:id/unmark-cleared with transaction IDs', async () => {
      const mockResponse: ReconciliationBalanceResponse = {
        reconciliation_id: 'rec-123',
        cleared_balance: '600.00',
        statement_balance: '1000.00',
        difference: '400.00',
      }
      mockApi.put.mockResolvedValue(mockResponse)

      const data = { transaction_ids: ['txn-3'] }
      const result = await reconciliationService.unmarkCleared('rec-123', data)

      expect(api.put).toHaveBeenCalledWith('/reconciliations/rec-123/unmark-cleared', data)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('createAdjustment', () => {
    it('should call POST /reconciliations/:id/create-adjustment with category', async () => {
      const mockResponse: ReconciliationAdjustmentResponse = {
        adjustment_transaction_id: 'txn-adj-1',
        amount: '50.00',
        category_id: 'cat-456',
      }
      mockApi.post.mockResolvedValue(mockResponse)

      const data = { category_id: 'cat-456' }
      const result = await reconciliationService.createAdjustment('rec-123', data)

      expect(api.post).toHaveBeenCalledWith(
        '/reconciliations/rec-123/create-adjustment',
        data
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('complete', () => {
    it('should call POST /reconciliations/:id/complete', async () => {
      const mockReconciliation = createReconciliation({
        id: 'rec-123',
        status: 'COMPLETED',
        completed_at: '2026-01-15T12:00:00Z',
      })
      mockApi.post.mockResolvedValue(mockReconciliation)

      const result = await reconciliationService.complete('rec-123')

      expect(api.post).toHaveBeenCalledWith('/reconciliations/rec-123/complete')
      expect(result).toEqual(mockReconciliation)
      expect(result.status).toBe('COMPLETED')
    })

    it('should propagate errors when completion fails', async () => {
      const error = new Error('Balance mismatch')
      mockApi.post.mockRejectedValue(error)

      await expect(reconciliationService.complete('rec-123')).rejects.toThrow(
        'Balance mismatch'
      )
    })
  })

  describe('cancel', () => {
    it('should call DELETE /reconciliations/:id', async () => {
      mockApi.delete.mockResolvedValue(undefined)

      await reconciliationService.cancel('rec-123')

      expect(api.delete).toHaveBeenCalledWith('/reconciliations/rec-123')
    })

    it('should propagate errors when cancellation fails', async () => {
      const error = new Error('Cannot cancel completed reconciliation')
      mockApi.delete.mockRejectedValue(error)

      await expect(reconciliationService.cancel('rec-123')).rejects.toThrow(
        'Cannot cancel completed reconciliation'
      )
    })
  })
})
