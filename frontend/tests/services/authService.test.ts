/**
 * Unit tests for authService.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { authService } from '@/services/authService'
import { ApiError } from '@/services/api'

// Mock the global fetch function
const mockFetch = vi.fn()
globalThis.fetch = mockFetch as typeof fetch

describe('authService', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('login', () => {
    it('should return login response on successful login', async () => {
      const mockResponse = { message: 'Login successful', user_id: '123' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await authService.login({
        email: 'test@example.com',
        password: 'password123',
      })

      expect(result).toEqual(mockResponse)
      expect(mockFetch).toHaveBeenCalledWith('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password123',
        }),
      })
    })

    it('should throw ApiError on invalid credentials', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: () => Promise.resolve({ detail: 'Invalid email or password' }),
      })

      try {
        await authService.login({
          email: 'test@example.com',
          password: 'wrongpassword',
        })
        // Should not reach here
        expect(true).toBe(false)
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError)
        expect((error as ApiError).status).toBe(401)
        expect((error as ApiError).detail).toBe('Invalid email or password')
      }
    })
  })

  describe('logout', () => {
    it('should return logout response on successful logout', async () => {
      const mockResponse = { message: 'Logout successful' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await authService.logout()

      expect(result).toEqual(mockResponse)
      expect(mockFetch).toHaveBeenCalledWith('/api/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      })
    })
  })

  describe('register', () => {
    it('should return user on successful registration', async () => {
      const mockUser = {
        id: '123',
        email: 'newuser@example.com',
        timezone: 'UTC',
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T00:00:00Z',
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUser),
      })

      const result = await authService.register({
        email: 'newuser@example.com',
        password: 'password123',
        timezone: 'UTC',
      })

      expect(result).toEqual(mockUser)
      expect(mockFetch).toHaveBeenCalledWith('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          email: 'newuser@example.com',
          password: 'password123',
          timezone: 'UTC',
        }),
      })
    })

    it('should throw ApiError on duplicate email', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 409,
        statusText: 'Conflict',
        json: () => Promise.resolve({ detail: 'Email already registered' }),
      })

      await expect(
        authService.register({
          email: 'existing@example.com',
          password: 'password123',
          timezone: 'UTC',
        })
      ).rejects.toThrow(ApiError)
    })
  })

  describe('getCurrentUser', () => {
    it('should return current user when authenticated', async () => {
      const mockUser = {
        id: '123',
        email: 'test@example.com',
        timezone: 'UTC',
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T00:00:00Z',
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUser),
      })

      const result = await authService.getCurrentUser()

      expect(result).toEqual(mockUser)
      expect(mockFetch).toHaveBeenCalledWith('/api/me', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      })
    })

    it('should throw ApiError when not authenticated', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: () => Promise.resolve({ detail: 'Not authenticated' }),
      })

      await expect(authService.getCurrentUser()).rejects.toThrow(ApiError)
    })
  })

  describe('isAuthenticated', () => {
    it('should return true when user is authenticated', async () => {
      const mockUser = {
        id: '123',
        email: 'test@example.com',
        timezone: 'UTC',
        created_at: '2026-01-17T00:00:00Z',
        updated_at: '2026-01-17T00:00:00Z',
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUser),
      })

      const result = await authService.isAuthenticated()

      expect(result).toBe(true)
    })

    it('should return false when user is not authenticated', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: () => Promise.resolve({ detail: 'Not authenticated' }),
      })

      const result = await authService.isAuthenticated()

      expect(result).toBe(false)
    })

    it('should throw error on unexpected errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: () => Promise.resolve({ detail: 'Server error' }),
      })

      await expect(authService.isAuthenticated()).rejects.toThrow(ApiError)
    })
  })
})
