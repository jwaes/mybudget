/**
 * Unit tests for transactionService.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { transactionService } from '@/services/transactionService'
import type { Transaction, TransactionListResponse, TransactionBulkResult } from '@/types/transaction'

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

// Helper to create a mock transaction
function createTransaction(overrides: Partial<Transaction> = {}): Transaction {
  return {
    id: 'txn-123',
    user_id: 'user-1',
    account_id: 'acc-1',
    category_id: null,
    date: '2026-01-15',
    payee: 'Test Payee',
    amount: '-50.00',
    memo: null,
    state: 'INBOX',
    created_at: '2026-01-15T10:00:00Z',
    updated_at: '2026-01-15T10:00:00Z',
    approved_at: null,
    cleared_at: null,
    ...overrides,
  }
}

describe('transactionService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('create', () => {
    it('should call POST /transactions/ with transaction data', async () => {
      const mockTransaction = createTransaction()
      mockApi.post.mockResolvedValue(mockTransaction)

      const createData = {
        account_id: 'acc-1',
        date: '2026-01-15',
        payee: 'Test Payee',
        amount: '-50.00',
      }
      const result = await transactionService.create(createData)

      expect(api.post).toHaveBeenCalledWith('/transactions/', createData)
      expect(result).toEqual(mockTransaction)
    })

    it('should propagate errors from api.post', async () => {
      const error = new Error('Network error')
      mockApi.post.mockRejectedValue(error)

      await expect(
        transactionService.create({
          account_id: 'acc-1',
          date: '2026-01-15',
          payee: 'Test',
          amount: '-10.00',
        })
      ).rejects.toThrow('Network error')
    })
  })

  describe('list', () => {
    it('should call GET /transactions/ without params', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [createTransaction()],
        total: 1,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      const result = await transactionService.list()

      expect(api.get).toHaveBeenCalledWith('/transactions/')
      expect(result).toEqual(mockResponse)
    })

    it('should include account_id query param', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [],
        total: 0,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      await transactionService.list({ account_id: 'acc-123' })

      expect(api.get).toHaveBeenCalledWith('/transactions/?account_id=acc-123')
    })

    it('should include state query param', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [],
        total: 0,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      await transactionService.list({ state: 'APPROVED' })

      expect(api.get).toHaveBeenCalledWith('/transactions/?state=APPROVED')
    })

    it('should include payee_search query param', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [],
        total: 0,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      await transactionService.list({ payee_search: 'Coffee' })

      expect(api.get).toHaveBeenCalledWith('/transactions/?payee_search=Coffee')
    })

    it('should include memo_search query param', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [],
        total: 0,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      await transactionService.list({ memo_search: 'work' })

      expect(api.get).toHaveBeenCalledWith('/transactions/?memo_search=work')
    })

    it('should include date range query params', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [],
        total: 0,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      await transactionService.list({
        date_from: '2026-01-01',
        date_to: '2026-01-31',
      })

      expect(api.get).toHaveBeenCalledWith(
        '/transactions/?date_from=2026-01-01&date_to=2026-01-31'
      )
    })

    it('should include amount range query params', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [],
        total: 0,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      await transactionService.list({
        amount_min: '10.00',
        amount_max: '100.00',
      })

      expect(api.get).toHaveBeenCalledWith(
        '/transactions/?amount_min=10.00&amount_max=100.00'
      )
    })

    it('should include category_id query param', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [],
        total: 0,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      await transactionService.list({ category_id: 'cat-456' })

      expect(api.get).toHaveBeenCalledWith('/transactions/?category_id=cat-456')
    })

    it('should include uncategorized_only query param', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [],
        total: 0,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      await transactionService.list({ uncategorized_only: true })

      expect(api.get).toHaveBeenCalledWith('/transactions/?uncategorized_only=true')
    })

    it('should include pagination params', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [],
        total: 0,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      await transactionService.list({ limit: 20, offset: 40 })

      expect(api.get).toHaveBeenCalledWith('/transactions/?limit=20&offset=40')
    })

    it('should combine multiple query params', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [],
        total: 0,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      await transactionService.list({
        account_id: 'acc-1',
        state: 'INBOX',
        limit: 10,
      })

      expect(api.get).toHaveBeenCalledWith(
        '/transactions/?account_id=acc-1&state=INBOX&limit=10'
      )
    })
  })

  describe('listInbox', () => {
    it('should call GET /transactions/inbox without params', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [createTransaction({ state: 'INBOX' })],
        total: 1,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      const result = await transactionService.listInbox()

      expect(api.get).toHaveBeenCalledWith('/transactions/inbox')
      expect(result).toEqual(mockResponse)
    })

    it('should include account_id query param', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [],
        total: 0,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      await transactionService.listInbox({ account_id: 'acc-123' })

      expect(api.get).toHaveBeenCalledWith('/transactions/inbox?account_id=acc-123')
    })

    it('should include pagination params', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [],
        total: 0,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      await transactionService.listInbox({ limit: 25, offset: 50 })

      expect(api.get).toHaveBeenCalledWith('/transactions/inbox?limit=25&offset=50')
    })
  })

  describe('get', () => {
    it('should call GET /transactions/:id', async () => {
      const mockTransaction = createTransaction({ id: 'txn-456' })
      mockApi.get.mockResolvedValue(mockTransaction)

      const result = await transactionService.get('txn-456')

      expect(api.get).toHaveBeenCalledWith('/transactions/txn-456')
      expect(result).toEqual(mockTransaction)
    })

    it('should propagate errors when transaction not found', async () => {
      const error = new Error('Not found')
      mockApi.get.mockRejectedValue(error)

      await expect(transactionService.get('nonexistent')).rejects.toThrow('Not found')
    })
  })

  describe('update', () => {
    it('should call PUT /transactions/:id with update data', async () => {
      const mockTransaction = createTransaction({
        id: 'txn-123',
        payee: 'Updated Payee',
      })
      mockApi.put.mockResolvedValue(mockTransaction)

      const updateData = { payee: 'Updated Payee' }
      const result = await transactionService.update('txn-123', updateData)

      expect(api.put).toHaveBeenCalledWith('/transactions/txn-123', updateData)
      expect(result).toEqual(mockTransaction)
    })

    it('should allow updating date', async () => {
      const mockTransaction = createTransaction({
        id: 'txn-123',
        date: '2026-01-20',
      })
      mockApi.put.mockResolvedValue(mockTransaction)

      await transactionService.update('txn-123', { date: '2026-01-20' })

      expect(api.put).toHaveBeenCalledWith('/transactions/txn-123', { date: '2026-01-20' })
    })

    it('should allow updating amount', async () => {
      const mockTransaction = createTransaction({
        id: 'txn-123',
        amount: '-75.50',
      })
      mockApi.put.mockResolvedValue(mockTransaction)

      await transactionService.update('txn-123', { amount: '-75.50' })

      expect(api.put).toHaveBeenCalledWith('/transactions/txn-123', { amount: '-75.50' })
    })

    it('should allow updating memo', async () => {
      const mockTransaction = createTransaction({
        id: 'txn-123',
        memo: 'New memo',
      })
      mockApi.put.mockResolvedValue(mockTransaction)

      await transactionService.update('txn-123', { memo: 'New memo' })

      expect(api.put).toHaveBeenCalledWith('/transactions/txn-123', { memo: 'New memo' })
    })

    it('should allow updating category_id', async () => {
      const mockTransaction = createTransaction({
        id: 'txn-123',
        category_id: 'cat-789',
      })
      mockApi.put.mockResolvedValue(mockTransaction)

      await transactionService.update('txn-123', { category_id: 'cat-789' })

      expect(api.put).toHaveBeenCalledWith('/transactions/txn-123', { category_id: 'cat-789' })
    })
  })

  describe('approve', () => {
    it('should call POST /transactions/:id/approve with category', async () => {
      const mockTransaction = createTransaction({
        id: 'txn-123',
        state: 'APPROVED',
        category_id: 'cat-456',
        approved_at: '2026-01-15T12:00:00Z',
      })
      mockApi.post.mockResolvedValue(mockTransaction)

      const result = await transactionService.approve('txn-123', { category_id: 'cat-456' })

      expect(api.post).toHaveBeenCalledWith('/transactions/txn-123/approve', {
        category_id: 'cat-456',
      })
      expect(result).toEqual(mockTransaction)
      expect(result.state).toBe('APPROVED')
    })

    it('should allow approving without category', async () => {
      const mockTransaction = createTransaction({
        id: 'txn-123',
        state: 'APPROVED',
        approved_at: '2026-01-15T12:00:00Z',
      })
      mockApi.post.mockResolvedValue(mockTransaction)

      await transactionService.approve('txn-123', {})

      expect(api.post).toHaveBeenCalledWith('/transactions/txn-123/approve', {})
    })
  })

  describe('unapprove', () => {
    it('should call POST /transactions/:id/unapprove', async () => {
      const mockTransaction = createTransaction({
        id: 'txn-123',
        state: 'INBOX',
        approved_at: null,
      })
      mockApi.post.mockResolvedValue(mockTransaction)

      const result = await transactionService.unapprove('txn-123')

      expect(api.post).toHaveBeenCalledWith('/transactions/txn-123/unapprove')
      expect(result).toEqual(mockTransaction)
      expect(result.state).toBe('INBOX')
    })

    it('should propagate errors when unapprove fails', async () => {
      const error = new Error('Cannot unapprove cleared transaction')
      mockApi.post.mockRejectedValue(error)

      await expect(transactionService.unapprove('txn-123')).rejects.toThrow(
        'Cannot unapprove cleared transaction'
      )
    })
  })

  describe('delete', () => {
    it('should call DELETE /transactions/:id', async () => {
      mockApi.delete.mockResolvedValue(undefined)

      await transactionService.delete('txn-123')

      expect(api.delete).toHaveBeenCalledWith('/transactions/txn-123')
    })

    it('should propagate errors when delete fails', async () => {
      const error = new Error('Cannot delete transaction')
      mockApi.delete.mockRejectedValue(error)

      await expect(transactionService.delete('txn-123')).rejects.toThrow(
        'Cannot delete transaction'
      )
    })
  })

  describe('getUncategorizedCount', () => {
    it('should return total from list with uncategorized_only', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [createTransaction()],
        total: 15,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      const result = await transactionService.getUncategorizedCount()

      expect(api.get).toHaveBeenCalledWith('/transactions/?uncategorized_only=true&limit=1')
      expect(result).toBe(15)
    })

    it('should return 0 when no uncategorized transactions', async () => {
      const mockResponse: TransactionListResponse = {
        transactions: [],
        total: 0,
      }
      mockApi.get.mockResolvedValue(mockResponse)

      const result = await transactionService.getUncategorizedCount()

      expect(result).toBe(0)
    })
  })

  describe('batchApprove', () => {
    it('should call POST /transactions/batch-approve with data', async () => {
      const mockResult: TransactionBulkResult = {
        success_count: 3,
        failed_count: 0,
        failed_ids: [],
      }
      mockApi.post.mockResolvedValue(mockResult)

      const batchData = {
        transaction_ids: ['txn-1', 'txn-2', 'txn-3'],
        category_id: 'cat-456',
      }
      const result = await transactionService.batchApprove(batchData)

      expect(api.post).toHaveBeenCalledWith('/transactions/batch-approve', batchData)
      expect(result).toEqual(mockResult)
    })

    it('should handle partial failures', async () => {
      const mockResult: TransactionBulkResult = {
        success_count: 2,
        failed_count: 1,
        failed_ids: ['txn-3'],
      }
      mockApi.post.mockResolvedValue(mockResult)

      const result = await transactionService.batchApprove({
        transaction_ids: ['txn-1', 'txn-2', 'txn-3'],
        category_id: 'cat-456',
      })

      expect(result.success_count).toBe(2)
      expect(result.failed_count).toBe(1)
      expect(result.failed_ids).toEqual(['txn-3'])
    })

    it('should propagate errors from batch approve', async () => {
      const error = new Error('Invalid category')
      mockApi.post.mockRejectedValue(error)

      await expect(
        transactionService.batchApprove({
          transaction_ids: ['txn-1'],
          category_id: 'invalid',
        })
      ).rejects.toThrow('Invalid category')
    })
  })
})
