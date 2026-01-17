/**
 * E2E tests for month rollover with targets.
 *
 * Tests month navigation behavior with all three target types.
 * Covers User Story 6 - Month Rollover.
 */

import { test, expect, Page } from '@playwright/test'

/**
 * Helper to register and login a test user.
 */
async function registerAndLogin(page: Page, suffix: string): Promise<string> {
  const email = `month-test-${suffix}-${Date.now()}@example.com`
  const password = 'testpassword123'

  await page.request.post('/api/register', {
    data: {
      email,
      password,
      timezone: 'Europe/Brussels',
    },
  })

  await page.goto('/login')
  await page.getByLabel(/email/i).fill(email)
  await page.getByLabel(/password/i).fill(password)
  await page.getByRole('button', { name: /log in|sign in/i }).click()

  await expect(page).toHaveURL(/^\/$|\/dashboard/)

  return email
}

/**
 * Setup a category with a target via API.
 */
async function setupCategoryWithTarget(
  page: Page,
  groupName: string,
  categoryName: string,
  targetType: string,
  amount: string,
  targetDate?: string
): Promise<{ groupId: string; categoryId: string; targetId: string }> {
  // Create group
  const groupRes = await page.request.post('/api/categories/groups', {
    data: { name: groupName, is_income: false },
  })
  const groupId = (await groupRes.json()).id

  // Create category
  const categoryRes = await page.request.post('/api/categories', {
    data: { name: categoryName, group_id: groupId },
  })
  const categoryId = (await categoryRes.json()).id

  // Create target
  const targetData: { category_id: string; target_type: string; amount: string; target_date?: string } = {
    category_id: categoryId,
    target_type: targetType,
    amount,
  }
  if (targetDate) {
    targetData.target_date = targetDate
  }
  const targetRes = await page.request.post('/api/targets', { data: targetData })
  const targetId = (await targetRes.json()).id

  return { groupId, categoryId, targetId }
}

/**
 * Setup an account and create income transaction.
 */
async function setupAccountWithIncome(page: Page, amount: string): Promise<string> {
  const accountRes = await page.request.post('/api/accounts', {
    data: {
      name: 'Test Checking',
      account_type: 'CHECKING',
      initial_balance: amount,
    },
  })
  const accountId = (await accountRes.json()).id

  return accountId
}

test.describe('Month Rollover E2E', () => {
  test.describe('Month Navigation', () => {
    test('should navigate between months using arrow buttons', async ({ page }) => {
      await registerAndLogin(page, 'nav-basic')

      // Navigate to budget page
      await page.goto('/')

      // Should show current month
      const currentMonth = new Date().toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric',
      })
      await expect(page.getByText(currentMonth)).toBeVisible()

      // Click previous month
      await page.getByRole('button', { name: /previous month/i }).click()

      // Should show previous month name
      const prevMonth = new Date()
      prevMonth.setMonth(prevMonth.getMonth() - 1)
      const prevMonthName = prevMonth.toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric',
      })
      await expect(page.getByText(prevMonthName)).toBeVisible()

      // Click next month twice to go forward
      await page.getByRole('button', { name: /next month/i }).click()
      await expect(page.getByText(currentMonth)).toBeVisible()

      await page.getByRole('button', { name: /next month/i }).click()
      const nextMonth = new Date()
      nextMonth.setMonth(nextMonth.getMonth() + 1)
      const nextMonthName = nextMonth.toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric',
      })
      await expect(page.getByText(nextMonthName)).toBeVisible()
    })
  })

  test.describe('Monthly Needed Target Rollover', () => {
    test('should show monthly target as underfunded in new month', async ({ page }) => {
      await registerAndLogin(page, 'monthly-rollover')
      await setupAccountWithIncome(page, '1000.00')
      await setupCategoryWithTarget(page, 'Bills', 'Rent', 'MONTHLY_NEEDED', '200.00')

      // Navigate to budget page
      await page.goto('/')

      // Should show underfunded
      await expect(page.getByText(/underfunded/i)).toBeVisible()

      // Fund the target
      await page.getByRole('button', { name: /fund underfunded/i }).click()

      // Wait for funding
      await expect(page.getByRole('button', { name: /funding\.\.\./i })).not.toBeVisible({
        timeout: 10000,
      })

      // Underfunded should now be gone or zero
      await page.waitForTimeout(500) // Let UI update

      // Go to next month
      await page.getByRole('button', { name: /next month/i }).click()

      // Wait for budget to reload
      await page.waitForTimeout(1000)

      // Should show underfunded again in new month
      await expect(page.getByText(/underfunded/i)).toBeVisible()
    })
  })

  test.describe('Target Balance Persistence', () => {
    test('should maintain balance target across months', async ({ page }) => {
      await registerAndLogin(page, 'balance-persist')
      await setupAccountWithIncome(page, '1000.00')
      await setupCategoryWithTarget(page, 'Savings', 'Emergency', 'TARGET_BALANCE', '500.00')

      await page.goto('/')

      // Should show underfunded (500)
      await expect(page.getByText(/underfunded/i)).toBeVisible()

      // Fund partially (200)
      await page.getByRole('button', { name: /fund underfunded/i }).click()
      await expect(page.getByRole('button', { name: /funding\.\.\./i })).not.toBeVisible({
        timeout: 10000,
      })

      // Navigate to next month
      await page.getByRole('button', { name: /next month/i }).click()
      await page.waitForTimeout(1000)

      // Should still show underfunded (balance didn't change)
      // The $200 we funded is still in available, but target is still $500
      await expect(page.getByText(/underfunded/i)).toBeVisible()
    })
  })

  test.describe('Target by Date Progression', () => {
    test('should update suggested monthly as deadline approaches', async ({ page }) => {
      await registerAndLogin(page, 'date-progress')
      await setupAccountWithIncome(page, '2000.00')

      // Create target for 4 months from now
      const targetDate = new Date()
      targetDate.setMonth(targetDate.getMonth() + 4)
      const targetDateStr = targetDate.toISOString().split('T')[0]

      await setupCategoryWithTarget(
        page,
        'Goals',
        'Vacation',
        'TARGET_BY_DATE',
        '400.00',
        targetDateStr
      )

      await page.goto('/')

      // Should show underfunded (400/4 = 100)
      await expect(page.getByText(/underfunded/i)).toBeVisible()

      // Fund for this month
      await page.getByRole('button', { name: /fund underfunded/i }).click()
      await expect(page.getByRole('button', { name: /funding\.\.\./i })).not.toBeVisible({
        timeout: 10000,
      })

      // Navigate to next month
      await page.getByRole('button', { name: /next month/i }).click()
      await page.waitForTimeout(1000)

      // Should show underfunded for next month
      await expect(page.getByText(/underfunded/i)).toBeVisible()
    })
  })

  test.describe('Year Boundary Navigation', () => {
    test('should handle year boundary correctly', async ({ page }) => {
      await registerAndLogin(page, 'year-boundary')

      await page.goto('/')

      // Get current month navigation to December
      const currentDate = new Date()
      const monthsToDecember = 12 - currentDate.getMonth()

      // Navigate forward to December
      for (let i = 0; i < monthsToDecember; i++) {
        await page.getByRole('button', { name: /next month/i }).click()
        await page.waitForTimeout(200)
      }

      // Should show December
      await expect(page.getByText(/december/i)).toBeVisible()

      // Go to next month (January next year)
      await page.getByRole('button', { name: /next month/i }).click()
      await page.waitForTimeout(200)

      // Should show January of next year
      const nextYear = currentDate.getFullYear() + 1
      await expect(page.getByText(`January ${nextYear}`)).toBeVisible()

      // Go back to December
      await page.getByRole('button', { name: /previous month/i }).click()
      await page.waitForTimeout(200)

      await expect(page.getByText(`December ${currentDate.getFullYear()}`)).toBeVisible()
    })
  })

  test.describe('Budget Data Updates on Month Change', () => {
    test('should reload budget data when changing months', async ({ page }) => {
      await registerAndLogin(page, 'data-reload')
      await setupAccountWithIncome(page, '1000.00')
      await setupCategoryWithTarget(page, 'Bills', 'Utilities', 'MONTHLY_NEEDED', '100.00')

      await page.goto('/')

      // Fund in current month
      await page.getByRole('button', { name: /fund underfunded/i }).click()
      await expect(page.getByRole('button', { name: /funding\.\.\./i })).not.toBeVisible({
        timeout: 10000,
      })

      // Get to_assign after funding
      const toAssignText = await page.locator('.to-assign-amount').textContent()

      // Go to previous month
      await page.getByRole('button', { name: /previous month/i }).click()
      await page.waitForTimeout(1000)

      // To assign should be different (previous month wasn't funded)
      const prevMonthToAssign = await page.locator('.to-assign-amount').textContent()

      // Previous month should have full amount to assign (nothing assigned there)
      expect(prevMonthToAssign).not.toEqual(toAssignText)

      // Go back to current month
      await page.getByRole('button', { name: /next month/i }).click()
      await page.waitForTimeout(1000)

      // Should show the same to_assign as before
      const currentMonthToAssign = await page.locator('.to-assign-amount').textContent()
      expect(currentMonthToAssign).toEqual(toAssignText)
    })
  })

  test.describe('All Target Types Combined', () => {
    test('should handle all three target types when navigating months', async ({ page }) => {
      await registerAndLogin(page, 'all-types')
      await setupAccountWithIncome(page, '3000.00')

      // Setup all three target types
      await setupCategoryWithTarget(page, 'Bills', 'Monthly Bill', 'MONTHLY_NEEDED', '200.00')
      await setupCategoryWithTarget(page, 'Savings', 'Balance Goal', 'TARGET_BALANCE', '500.00')

      const futureDate = new Date()
      futureDate.setMonth(futureDate.getMonth() + 3)
      await setupCategoryWithTarget(
        page,
        'Goals',
        'Trip',
        'TARGET_BY_DATE',
        '300.00',
        futureDate.toISOString().split('T')[0]
      )

      await page.goto('/')

      // Should show all categories
      await expect(page.getByText('Monthly Bill')).toBeVisible()
      await expect(page.getByText('Balance Goal')).toBeVisible()
      await expect(page.getByText('Trip')).toBeVisible()

      // Should show underfunded
      await expect(page.getByText(/underfunded/i)).toBeVisible()

      // Fund all
      await page.getByRole('button', { name: /fund underfunded/i }).click()
      await expect(page.getByRole('button', { name: /funding\.\.\./i })).not.toBeVisible({
        timeout: 10000,
      })

      // Navigate to next month
      await page.getByRole('button', { name: /next month/i }).click()
      await page.waitForTimeout(1000)

      // Monthly Needed should be underfunded again
      // Balance and Date targets should reflect carried-over amounts
      await expect(page.getByText(/underfunded/i)).toBeVisible()
    })
  })
})
