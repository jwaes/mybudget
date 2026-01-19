/**
 * Unit tests for api client.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { api, ApiError, onSessionExpired } from '@/services/api'

describe('api', () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  afterEach(() => {
    global.fetch = originalFetch
  })

  describe('get', () => {
    it('should make GET request with correct headers', async () => {
      const mockResponse = { data: 'test' }
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockResponse),
      } as Response)

      const result = await api.get('/test')

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/test',
        expect.objectContaining({
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
        })
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('post', () => {
    it('should make POST request with body', async () => {
      const mockResponse = { id: '123' }
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockResponse),
      } as Response)

      const body = { name: 'Test' }
      const result = await api.post('/test', body)

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/test',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(body),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should handle POST without body', async () => {
      const mockResponse = { success: true }
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockResponse),
      } as Response)

      await api.post('/test')

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/test',
        expect.objectContaining({
          method: 'POST',
        })
      )
      // Verify body is not present in the call
      const callArgs = vi.mocked(global.fetch).mock.calls[0]
      expect(callArgs[1]?.body).toBeUndefined()
    })
  })

  describe('put', () => {
    it('should make PUT request with body', async () => {
      const mockResponse = { updated: true }
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockResponse),
      } as Response)

      const body = { name: 'Updated' }
      const result = await api.put('/test/123', body)

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/test/123',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(body),
        })
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('patch', () => {
    it('should make PATCH request with body', async () => {
      const mockResponse = { patched: true }
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockResponse),
      } as Response)

      const body = { field: 'value' }
      const result = await api.patch('/test/123', body)

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/test/123',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(body),
        })
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('delete', () => {
    it('should make DELETE request', async () => {
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        status: 204,
      } as Response)

      await api.delete('/test/123')

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/test/123',
        expect.objectContaining({
          method: 'DELETE',
        })
      )
    })
  })

  describe('error handling', () => {
    it('should throw ApiError on non-ok response with JSON error', async () => {
      vi.mocked(global.fetch).mockResolvedValue({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: () => Promise.resolve({ detail: 'Invalid data' }),
      } as Response)

      await expect(api.get('/test')).rejects.toThrow(ApiError)

      try {
        await api.get('/test')
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError)
        expect((e as ApiError).status).toBe(400)
        expect((e as ApiError).detail).toBe('Invalid data')
      }
    })

    it('should use status text when JSON parsing fails', async () => {
      vi.mocked(global.fetch).mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: () => Promise.reject(new Error('Not JSON')),
      } as Response)

      try {
        await api.get('/test')
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError)
        expect((e as ApiError).detail).toBe('Internal Server Error')
      }
    })

    it('should handle 204 No Content response', async () => {
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        status: 204,
      } as Response)

      const result = await api.delete('/test/123')

      expect(result).toBeUndefined()
    })
  })

  describe('session expiry', () => {
    it('should notify listeners on 401 for non-auth endpoints', async () => {
      const listener = vi.fn()
      const unsubscribe = onSessionExpired(listener)

      vi.mocked(global.fetch).mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: () => Promise.resolve({ detail: 'Session expired' }),
      } as Response)

      try {
        await api.get('/accounts')
      } catch {
        // Expected to throw
      }

      expect(listener).toHaveBeenCalled()
      unsubscribe()
    })

    it('should not notify listeners on 401 for auth endpoints', async () => {
      const listener = vi.fn()
      const unsubscribe = onSessionExpired(listener)

      vi.mocked(global.fetch).mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: () => Promise.resolve({ detail: 'Invalid credentials' }),
      } as Response)

      try {
        await api.post('/login', { email: 'test@test.com', password: 'wrong' })
      } catch {
        // Expected to throw
      }

      expect(listener).not.toHaveBeenCalled()
      unsubscribe()
    })

    it('should allow unsubscribing from session expiry events', async () => {
      const listener = vi.fn()
      const unsubscribe = onSessionExpired(listener)
      unsubscribe()

      vi.mocked(global.fetch).mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: () => Promise.resolve({ detail: 'Session expired' }),
      } as Response)

      try {
        await api.get('/accounts')
      } catch {
        // Expected to throw
      }

      expect(listener).not.toHaveBeenCalled()
    })
  })
})
