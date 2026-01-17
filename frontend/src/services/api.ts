/**
 * API client utility for MyBudget.
 *
 * Provides a configured fetch wrapper with session cookie handling,
 * error handling, and type-safe request/response handling.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

/**
 * Event emitter for session expiry notifications.
 * Components can subscribe to this to handle session expiry gracefully.
 */
type SessionExpiredListener = () => void
const sessionExpiredListeners: Set<SessionExpiredListener> = new Set()

/**
 * Subscribe to session expiry events.
 * @param listener - Callback to invoke when session expires
 * @returns Unsubscribe function
 */
export function onSessionExpired(listener: SessionExpiredListener): () => void {
  sessionExpiredListeners.add(listener)
  return () => sessionExpiredListeners.delete(listener)
}

/**
 * Notify all listeners that the session has expired.
 */
function notifySessionExpired(): void {
  sessionExpiredListeners.forEach((listener) => listener())
}

/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public response?: Response
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

/**
 * API client configuration options.
 */
interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
}

/**
 * Make an API request with proper error handling and cookie credentials.
 *
 * @param endpoint - The API endpoint (relative to API_BASE_URL)
 * @param options - Fetch options
 * @returns The parsed JSON response
 * @throws ApiError if the request fails
 */
async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers: customHeaders, ...restOptions } = options

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...customHeaders,
  }

  const config: RequestInit = {
    ...restOptions,
    headers,
    credentials: 'include', // Include cookies for session management
  }

  if (body !== undefined) {
    config.body = JSON.stringify(body)
  }

  const url = `${API_BASE_URL}${endpoint}`
  const response = await fetch(url, config)

  // Handle non-2xx responses
  if (!response.ok) {
    let detail = 'An error occurred'
    try {
      const errorData = await response.json()
      detail = errorData.detail || detail
    } catch {
      // If response isn't JSON, use status text
      detail = response.statusText || detail
    }

    // Check for session expiry (401 on non-auth endpoints)
    // Auth endpoints (/login, /logout, /me, /register) handle 401 themselves
    const isAuthEndpoint = ['/login', '/logout', '/me', '/register'].some((path) =>
      endpoint.endsWith(path)
    )
    if (response.status === 401 && !isAuthEndpoint) {
      notifySessionExpired()
    }

    throw new ApiError(response.status, detail, response)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

/**
 * API client with typed methods for common HTTP verbs.
 */
export const api = {
  /**
   * Make a GET request.
   */
  get<T>(endpoint: string, options?: Omit<RequestOptions, 'method' | 'body'>): Promise<T> {
    return request<T>(endpoint, { ...options, method: 'GET' })
  },

  /**
   * Make a POST request.
   */
  post<T>(endpoint: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>): Promise<T> {
    return request<T>(endpoint, { ...options, method: 'POST', body })
  },

  /**
   * Make a PUT request.
   */
  put<T>(endpoint: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>): Promise<T> {
    return request<T>(endpoint, { ...options, method: 'PUT', body })
  },

  /**
   * Make a PATCH request.
   */
  patch<T>(endpoint: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>): Promise<T> {
    return request<T>(endpoint, { ...options, method: 'PATCH', body })
  },

  /**
   * Make a DELETE request.
   */
  delete<T>(endpoint: string, options?: Omit<RequestOptions, 'method' | 'body'>): Promise<T> {
    return request<T>(endpoint, { ...options, method: 'DELETE' })
  },
}

export default api
