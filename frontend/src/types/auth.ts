/**
 * Authentication types for MyBudget.
 */

export interface User {
  id: string
  email: string
  timezone: string
  created_at: string
  updated_at: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  timezone: string
}

export interface LoginResponse {
  message: string
  user_id: string
}

export interface LogoutResponse {
  message: string
}
