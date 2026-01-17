/**
 * Authentication service for MyBudget.
 *
 * Handles user authentication operations including login, logout,
 * registration, and fetching the current user.
 */

import { api, ApiError } from './api'
import type {
  User,
  LoginCredentials,
  RegisterData,
  LoginResponse,
  LogoutResponse,
} from '@/types/auth'

/**
 * Authentication service with methods for managing user sessions.
 */
export const authService = {
  /**
   * Login with email and password.
   *
   * @param credentials - User login credentials
   * @returns Login response with user_id
   * @throws ApiError if authentication fails
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    return api.post<LoginResponse>('/login', credentials)
  },

  /**
   * Logout the current user.
   *
   * Clears the session cookie on the server side.
   *
   * @returns Logout confirmation message
   */
  async logout(): Promise<LogoutResponse> {
    return api.post<LogoutResponse>('/logout')
  },

  /**
   * Register a new user.
   *
   * @param data - User registration data
   * @returns The created user
   * @throws ApiError if registration fails (e.g., email already exists)
   */
  async register(data: RegisterData): Promise<User> {
    return api.post<User>('/register', data)
  },

  /**
   * Get the currently authenticated user.
   *
   * @returns The current user if authenticated
   * @throws ApiError with status 401 if not authenticated
   */
  async getCurrentUser(): Promise<User> {
    return api.get<User>('/me')
  },

  /**
   * Check if the user is currently authenticated.
   *
   * This is a convenience method that attempts to fetch the current user
   * and returns true if successful, false otherwise.
   *
   * @returns true if authenticated, false otherwise
   */
  async isAuthenticated(): Promise<boolean> {
    try {
      await this.getCurrentUser()
      return true
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        return false
      }
      // Re-throw unexpected errors
      throw error
    }
  },
}

export default authService
