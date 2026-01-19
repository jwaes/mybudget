/**
 * Unit tests for accountService.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { accountService } from '@/services/accountService'

vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import { api } from '@/services/api'

describe('accountService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('create', () => {
    it('should call POST /accounts/ with account data', async () => {
      const mockAccount = {
        id: 'acc-123',
        name: 'Checking Account',
        account_type: 'checking',
        balance: 1000,
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T00:00:00Z',
      }
      vi.mocked(api.post).mockResolvedValue(mockAccount)

      const createData = {
        name: 'Checking Account',
        account_type: 'checking',
        balance: 1000,
      }
      const result = await accountService.create(createData)

      expect(api.post).toHaveBeenCalledWith('/accounts/', createData)
      expect(result).toEqual(mockAccount)
    })

    it('should propagate errors from api.post', async () => {
      const error = new Error('Network error')
      vi.mocked(api.post).mockRejectedValue(error)

      await expect(
        accountService.create({
          name: 'Test Account',
          account_type: 'checking',
          balance: 0,
        })
      ).rejects.toThrow('Network error')
    })
  })

  describe('list', () => {
    it('should call GET /accounts/', async () => {
      const mockResponse = {
        accounts: [
          {
            id: 'acc-1',
            name: 'Account 1',
            account_type: 'checking',
            balance: 500,
            created_at: '2026-01-17T00:00:00Z',
            updated_at: '2026-01-17T00:00:00Z',
          },
          {
            id: 'acc-2',
            name: 'Account 2',
            account_type: 'savings',
            balance: 2000,
            created_at: '2026-01-17T00:00:00Z',
            updated_at: '2026-01-17T00:00:00Z',
          },
        ],
        total: 2,
      }
      vi.mocked(api.get).mockResolvedValue(mockResponse)

      const result = await accountService.list()

      expect(api.get).toHaveBeenCalledWith('/accounts/')
      expect(result).toEqual(mockResponse)
    })

    it('should return empty list when no accounts exist', async () => {
      const mockResponse = { accounts: [], total: 0 }
      vi.mocked(api.get).mockResolvedValue(mockResponse)

      const result = await accountService.list()

      expect(result).toEqual(mockResponse)
      expect(result.accounts).toHaveLength(0)
    })
  })

  describe('get', () => {
    it('should call GET /accounts/:id', async () => {
      const mockAccount = {
        id: 'acc-123',
        name: 'My Account',
        account_type: 'checking',
        balance: 1500,
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T00:00:00Z',
      }
      vi.mocked(api.get).mockResolvedValue(mockAccount)

      const result = await accountService.get('acc-123')

      expect(api.get).toHaveBeenCalledWith('/accounts/acc-123')
      expect(result).toEqual(mockAccount)
    })

    it('should propagate errors when account not found', async () => {
      const error = new Error('Not found')
      vi.mocked(api.get).mockRejectedValue(error)

      await expect(accountService.get('nonexistent')).rejects.toThrow('Not found')
    })
  })

  describe('update', () => {
    it('should call PUT /accounts/:id with update data', async () => {
      const mockAccount = {
        id: 'acc-123',
        name: 'Updated Account Name',
        account_type: 'checking',
        balance: 1500,
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T01:00:00Z',
      }
      vi.mocked(api.put).mockResolvedValue(mockAccount)

      const updateData = { name: 'Updated Account Name' }
      const result = await accountService.update('acc-123', updateData)

      expect(api.put).toHaveBeenCalledWith('/accounts/acc-123', updateData)
      expect(result).toEqual(mockAccount)
    })

    it('should allow partial updates', async () => {
      const mockAccount = {
        id: 'acc-123',
        name: 'Account',
        account_type: 'savings',
        balance: 3000,
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T01:00:00Z',
      }
      vi.mocked(api.put).mockResolvedValue(mockAccount)

      const updateData = { balance: 3000 }
      const result = await accountService.update('acc-123', updateData)

      expect(api.put).toHaveBeenCalledWith('/accounts/acc-123', updateData)
      expect(result.balance).toBe(3000)
    })
  })

  describe('delete', () => {
    it('should call DELETE /accounts/:id', async () => {
      vi.mocked(api.delete).mockResolvedValue(undefined)

      await accountService.delete('acc-123')

      expect(api.delete).toHaveBeenCalledWith('/accounts/acc-123')
    })

    it('should propagate errors when deletion fails', async () => {
      const error = new Error('Cannot delete account with transactions')
      vi.mocked(api.delete).mockRejectedValue(error)

      await expect(accountService.delete('acc-123')).rejects.toThrow(
        'Cannot delete account with transactions'
      )
    })
  })

  describe('retrySync', () => {
    it('should call POST /accounts/:id/retry-sync', async () => {
      const mockAccount = {
        id: 'acc-123',
        name: 'Synced Account',
        account_type: 'checking',
        balance: 1500,
        sync_status: 'syncing',
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T02:00:00Z',
      }
      vi.mocked(api.post).mockResolvedValue(mockAccount)

      const result = await accountService.retrySync('acc-123')

      expect(api.post).toHaveBeenCalledWith('/accounts/acc-123/retry-sync')
      expect(result).toEqual(mockAccount)
    })

    it('should propagate errors when sync retry fails', async () => {
      const error = new Error('Sync service unavailable')
      vi.mocked(api.post).mockRejectedValue(error)

      await expect(accountService.retrySync('acc-123')).rejects.toThrow(
        'Sync service unavailable'
      )
    })
  })
})
