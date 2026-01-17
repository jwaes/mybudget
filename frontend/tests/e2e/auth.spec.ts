/**
 * E2E tests for authentication flows.
 *
 * Tests login and registration user journeys per FR-AUTH-001 through FR-AUTH-009.
 */

import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test.describe('Login Flow', () => {
    test('should redirect to login when accessing protected route while unauthenticated', async ({ page }) => {
      // Try to access a protected route
      await page.goto('/accounts')

      // Should be redirected to login
      await expect(page).toHaveURL(/\/login/)
    })

    test('should show login form with email and password fields', async ({ page }) => {
      await page.goto('/login')

      await expect(page.getByLabel(/email/i)).toBeVisible()
      await expect(page.getByLabel(/password/i)).toBeVisible()
      await expect(page.getByRole('button', { name: /log in|sign in/i })).toBeVisible()
    })

    test('should show validation error for invalid credentials', async ({ page }) => {
      await page.goto('/login')

      await page.getByLabel(/email/i).fill('test@example.com')
      await page.getByLabel(/password/i).fill('wrongpassword')
      await page.getByRole('button', { name: /log in|sign in/i }).click()

      // Should show error message
      await expect(page.getByText(/invalid|incorrect|failed/i)).toBeVisible()
    })

    test('should login successfully and redirect to dashboard', async ({ page }) => {
      // First register a user via the backend API directly
      const testEmail = `test-${Date.now()}@example.com`
      const testPassword = 'testpassword123'

      // Register via API
      await page.request.post('/api/register', {
        data: {
          email: testEmail,
          password: testPassword,
          timezone: 'Europe/Brussels',
        },
      })

      // Now test login flow
      await page.goto('/login')

      await page.getByLabel(/email/i).fill(testEmail)
      await page.getByLabel(/password/i).fill(testPassword)
      await page.getByRole('button', { name: /log in|sign in/i }).click()

      // Should redirect to dashboard or home (ends with / or contains /dashboard)
      await expect(page).toHaveURL(/\/$|\/dashboard/)
    })

    test('should have link to registration page', async ({ page }) => {
      await page.goto('/login')

      const registerLink = page.getByRole('link', { name: /register|sign up|create account/i })
      await expect(registerLink).toBeVisible()

      await registerLink.click()
      await expect(page).toHaveURL(/\/register/)
    })
  })

  test.describe('Registration Flow', () => {
    test('should show registration form with all required fields', async ({ page }) => {
      await page.goto('/register')

      await expect(page.getByLabel(/email/i)).toBeVisible()
      await expect(page.getByLabel(/^password$/i)).toBeVisible()
      await expect(page.getByLabel(/confirm password/i)).toBeVisible()
      await expect(page.getByLabel(/timezone/i)).toBeVisible()
      await expect(page.getByRole('button', { name: /register|sign up|create account/i })).toBeVisible()
    })

    test('should show validation error for password mismatch', async ({ page }) => {
      await page.goto('/register')

      await page.getByLabel(/email/i).fill('test@example.com')
      await page.getByLabel(/^password$/i).fill('password123')
      await page.getByLabel(/confirm password/i).fill('differentpassword')

      // Select timezone using shadcn Select (click to open, then click option)
      await page.getByRole('combobox', { name: /timezone/i }).click()
      await page.getByRole('option', { name: /Europe\/Brussels/ }).click()

      await page.getByRole('button', { name: /register|sign up|create account/i }).click()

      await expect(page.getByText(/passwords.*match|do not match|must match/i)).toBeVisible()
    })

    test('should show validation error for password too short', async ({ page }) => {
      await page.goto('/register')

      await page.getByLabel(/email/i).fill('test@example.com')
      await page.getByLabel(/^password$/i).fill('short')
      await page.getByLabel(/confirm password/i).fill('short')

      await page.getByRole('button', { name: /register|sign up|create account/i }).click()

      await expect(page.getByText(/8 characters|too short|at least 8/i)).toBeVisible()
    })

    test('should register successfully and auto-login', async ({ page }) => {
      const testEmail = `newuser-${Date.now()}@example.com`

      await page.goto('/register')

      await page.getByLabel(/email/i).fill(testEmail)
      await page.getByLabel(/^password$/i).fill('password123')
      await page.getByLabel(/confirm password/i).fill('password123')

      // Select timezone using shadcn Select (click to open, then click option)
      await page.getByRole('combobox', { name: /timezone/i }).click()
      await page.getByRole('option', { name: /Europe\/Brussels/ }).click()

      await page.getByRole('button', { name: /register|sign up|create account/i }).click()

      // Should be automatically logged in and redirected to dashboard
      await expect(page).toHaveURL(/\/$|\/dashboard/)
    })

    test('should show error for duplicate email registration', async ({ page }) => {
      const testEmail = `duplicate-${Date.now()}@example.com`

      // First registration
      await page.request.post('/api/register', {
        data: {
          email: testEmail,
          password: 'password123',
          timezone: 'Europe/Brussels',
        },
      })

      // Try to register again with same email
      await page.goto('/register')

      await page.getByLabel(/email/i).fill(testEmail)
      await page.getByLabel(/^password$/i).fill('password123')
      await page.getByLabel(/confirm password/i).fill('password123')

      // Select timezone using shadcn Select (click to open, then click option)
      await page.getByRole('combobox', { name: /timezone/i }).click()
      await page.getByRole('option', { name: /Europe\/Brussels/ }).click()

      await page.getByRole('button', { name: /register|sign up|create account/i }).click()

      await expect(page.getByText(/already registered|email.*exists|already in use/i)).toBeVisible()
    })

    test('should have link to login page', async ({ page }) => {
      await page.goto('/register')

      const loginLink = page.getByRole('link', { name: /log in|sign in|already have an account/i })
      await expect(loginLink).toBeVisible()

      await loginLink.click()
      await expect(page).toHaveURL(/\/login/)
    })
  })

  test.describe('Logout Flow', () => {
    test('should logout and redirect to login page', async ({ page }) => {
      // First register and login
      const testEmail = `logout-${Date.now()}@example.com`
      const testPassword = 'password123'

      await page.request.post('/api/register', {
        data: {
          email: testEmail,
          password: testPassword,
          timezone: 'Europe/Brussels',
        },
      })

      await page.goto('/login')
      await page.getByLabel(/email/i).fill(testEmail)
      await page.getByLabel(/password/i).fill(testPassword)
      await page.getByRole('button', { name: /log in|sign in/i }).click()

      // Wait for redirect to dashboard
      await expect(page).toHaveURL(/\/$|\/dashboard/)

      // Find and click logout button
      await page.getByRole('button', { name: /log out|sign out/i }).click()

      // Should be redirected to login
      await expect(page).toHaveURL(/\/login/)
    })
  })

  test.describe('Protected Routes', () => {
    test('should allow access to protected routes when authenticated', async ({ page }) => {
      // First register and login
      const testEmail = `protected-${Date.now()}@example.com`
      const testPassword = 'password123'

      await page.request.post('/api/register', {
        data: {
          email: testEmail,
          password: testPassword,
          timezone: 'Europe/Brussels',
        },
      })

      // Login via the UI
      await page.goto('/login')
      await page.getByLabel(/email/i).fill(testEmail)
      await page.getByLabel(/password/i).fill(testPassword)
      await page.getByRole('button', { name: /log in|sign in/i }).click()

      // Wait for authentication to complete
      await expect(page).toHaveURL(/\/$|\/dashboard/)

      // Now should be able to access protected routes
      await page.goto('/accounts')
      await expect(page).toHaveURL(/\/accounts/)

      await page.goto('/transactions')
      await expect(page).toHaveURL(/\/transactions/)
    })
  })
})
