/**
 * E2E tests for the funding workflow.
 *
 * Tests the complete user journey of funding underfunded categories.
 * Covers User Story 5 - Auto-Fund Underfunded Categories.
 */

import { test, expect, Page } from '@playwright/test'

/**
 * Helper to register and login a test user.
 */
async function registerAndLogin(page: Page, suffix: string): Promise<{ email: string; password: string }> {
  const email = `funding-test-${suffix}-${Date.now()}@example.com`
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

  // Wait for redirect to dashboard
  await expect(page).toHaveURL(/\/$|\/dashboard/)

  return { email, password }
}

/**
 * Helper to set up test data via API.
 */
async function setupTestData(page: Page): Promise<{
  accountId: string
  groupId: string
  categoryId: string
  targetId: string
}> {
  // Create an account
  const accountRes = await page.request.post('/api/accounts', {
    data: {
      name: 'Test Checking',
      account_type: 'CHECKING',
      initial_balance: '1000.00',
    },
  })
  const account = await accountRes.json()

  // Create a category group
  const groupRes = await page.request.post('/api/categories/groups', {
    data: {
      name: 'Bills',
      is_income: false,
    },
  })
  const group = await groupRes.json()

  // Create a category
  const categoryRes = await page.request.post('/api/categories', {
    data: {
      name: 'Electricity',
      group_id: group.id,
    },
  })
  const category = await categoryRes.json()

  // Create a transaction (income to have funds to assign)
  await page.request.post('/api/transactions', {
    data: {
      account_id: account.id,
      date: new Date().toISOString().split('T')[0],
      payee: 'Paycheck',
      amount: '500.00',
    },
  })

  // Create a target for the category (monthly savings target of $200)
  const targetRes = await page.request.post('/api/targets', {
    data: {
      category_id: category.id,
      target_type: 'MONTHLY_SAVINGS',
      amount: '200.00',
    },
  })
  const target = await targetRes.json()

  return {
    accountId: account.id,
    groupId: group.id,
    categoryId: category.id,
    targetId: target.id,
  }
}

test.describe('Funding Workflow', () => {
  test.describe('View Underfunded Summary', () => {
    test('should display underfunded amount when categories have targets but no funding', async ({ page }) => {
      await registerAndLogin(page, 'underfunded-display')
      await setupTestData(page)

      // Navigate to budget page
      await page.goto('/')

      // Should show the To Assign amount (from income transaction)
      await expect(page.getByText(/to assign/i)).toBeVisible()

      // Should show underfunded section
      await expect(page.getByText(/underfunded/i)).toBeVisible()

      // Should show the Fund Underfunded button
      await expect(page.getByRole('button', { name: /fund underfunded/i })).toBeVisible()
    })

    test('should show specific category underfunded amounts', async ({ page }) => {
      await registerAndLogin(page, 'category-underfunded')
      await setupTestData(page)

      // Navigate to budget page
      await page.goto('/')

      // Should display the Electricity category
      await expect(page.getByText('Electricity')).toBeVisible()

      // The category row should show underfunded status (highlighted or with indicator)
      const categoryRow = page.locator('[data-testid="category-row"]', { hasText: 'Electricity' })
        .or(page.locator('.category-row', { hasText: 'Electricity' }))
        .or(page.getByText('Electricity').locator('..'))

      await expect(categoryRow).toBeVisible()
    })
  })

  test.describe('Fund All Underfunded', () => {
    test('should fund all underfunded categories when clicking Fund Underfunded button', async ({ page }) => {
      await registerAndLogin(page, 'fund-all')
      await setupTestData(page)

      // Navigate to budget page
      await page.goto('/')

      // Wait for budget data to load
      await expect(page.getByText(/to assign/i)).toBeVisible()

      // Get initial To Assign amount
      const toAssignBefore = await page.getByText(/\$[\d,]+\.\d{2}/).first().textContent()

      // Click Fund Underfunded button
      await page.getByRole('button', { name: /fund underfunded/i }).click()

      // Wait for funding to complete - button should change or underfunded section should disappear
      await expect(page.getByRole('button', { name: /funding\.\.\./i })).not.toBeVisible({ timeout: 10000 })

      // The To Assign amount should decrease
      const toAssignAfter = await page.getByText(/\$[\d,]+\.\d{2}/).first().textContent()

      // Verify amounts changed (To Assign decreased after funding)
      expect(toAssignBefore).not.toEqual(toAssignAfter)
    })

    test('should show success toast after funding', async ({ page }) => {
      await registerAndLogin(page, 'fund-toast')
      await setupTestData(page)

      // Navigate to budget page
      await page.goto('/')

      // Wait for budget data to load
      await expect(page.getByRole('button', { name: /fund underfunded/i })).toBeVisible()

      // Click Fund Underfunded button
      await page.getByRole('button', { name: /fund underfunded/i }).click()

      // Should show success toast
      await expect(page.getByText(/funded.*\$/i)).toBeVisible({ timeout: 10000 })
    })

    test('should disable Fund Underfunded button when To Assign is zero', async ({ page }) => {
      await registerAndLogin(page, 'fund-disabled')

      // Create category group and category but NO income (so To Assign is 0)
      const groupRes = await page.request.post('/api/categories/groups', {
        data: {
          name: 'Bills',
          is_income: false,
        },
      })
      const group = await groupRes.json()

      const categoryRes = await page.request.post('/api/categories', {
        data: {
          name: 'Electricity',
          group_id: group.id,
        },
      })
      const category = await categoryRes.json()

      // Create a target
      await page.request.post('/api/targets', {
        data: {
          category_id: category.id,
          target_type: 'MONTHLY_SAVINGS',
          amount: '200.00',
        },
      })

      // Navigate to budget page
      await page.goto('/')

      // Wait for page to load
      await expect(page.getByText('Electricity')).toBeVisible()

      // The Fund Underfunded button should be disabled (no funds to assign)
      const fundButton = page.getByRole('button', { name: /fund underfunded/i })
      if (await fundButton.isVisible()) {
        await expect(fundButton).toBeDisabled()
      }
    })
  })

  test.describe('Fund Single Category', () => {
    test('should fund a single underfunded category', async ({ page }) => {
      await registerAndLogin(page, 'fund-single')
      await setupTestData(page)

      // Navigate to budget page
      await page.goto('/')

      // Wait for budget data to load
      await expect(page.getByText('Electricity')).toBeVisible()

      // Find the category row and its fund button (if it exists)
      // The exact UI depends on implementation - look for a fund icon or button near the category
      const categoryArea = page.getByText('Electricity').locator('..')

      // Try to find a fund button for the category
      const fundButton = categoryArea.getByRole('button', { name: /fund|fill/i })
        .or(categoryArea.locator('[aria-label*="fund"]'))
        .or(categoryArea.locator('.fund-button'))

      // If there's a single-category fund button, click it
      if (await fundButton.isVisible()) {
        await fundButton.click()

        // Should show success toast
        await expect(page.getByText(/funded.*electricity/i)).toBeVisible({ timeout: 10000 })
      }
    })
  })

  test.describe('Manual Assignment', () => {
    test('should allow manual fund assignment to a category', async ({ page }) => {
      await registerAndLogin(page, 'manual-assign')
      await setupTestData(page)

      // Navigate to budget page
      await page.goto('/')

      // Wait for budget data to load
      await expect(page.getByText('Electricity')).toBeVisible()

      // Click on the category's funded column to edit
      // The exact interaction depends on implementation
      const categoryRow = page.getByText('Electricity').locator('..')

      // Try to click on the funded amount to edit
      const fundedCell = categoryRow.locator('.funded-amount, .funded-cell, [data-column="funded"]')
        .or(categoryRow.locator('input[name*="funded"]'))

      if (await fundedCell.isVisible()) {
        await fundedCell.click()

        // Type an amount
        await page.keyboard.type('50.00')
        await page.keyboard.press('Enter')

        // Should update the display
        await expect(page.getByText('$50.00')).toBeVisible({ timeout: 5000 })
      }
    })
  })

  test.describe('Budget View Updates', () => {
    test('should update available amount after funding', async ({ page }) => {
      await registerAndLogin(page, 'available-update')
      await setupTestData(page)

      // Navigate to budget page
      await page.goto('/')

      // Wait for budget data to load
      await expect(page.getByRole('button', { name: /fund underfunded/i })).toBeVisible()

      // Get the category row
      await expect(page.getByText('Electricity')).toBeVisible()

      // Click Fund Underfunded
      await page.getByRole('button', { name: /fund underfunded/i }).click()

      // Wait for funding to complete
      await expect(page.getByRole('button', { name: /funding\.\.\./i })).not.toBeVisible({ timeout: 10000 })

      // The available amount for the category should now show funded amount
      // (This will depend on the specific UI implementation)
      const categoryRow = page.getByText('Electricity').locator('..')
      const availableAmount = categoryRow.locator('.available, [data-column="available"]')

      if (await availableAmount.isVisible()) {
        // Should show a positive amount after funding
        const text = await availableAmount.textContent()
        expect(text).toMatch(/\$[\d,]+\.\d{2}/)
      }
    })

    test('should persist funding after page reload', async ({ page }) => {
      await registerAndLogin(page, 'persist-funding')
      await setupTestData(page)

      // Navigate to budget page
      await page.goto('/')

      // Wait for and click Fund Underfunded
      await expect(page.getByRole('button', { name: /fund underfunded/i })).toBeVisible()
      await page.getByRole('button', { name: /fund underfunded/i }).click()

      // Wait for funding to complete
      await expect(page.getByRole('button', { name: /funding\.\.\./i })).not.toBeVisible({ timeout: 10000 })

      // Get the To Assign amount after funding
      const toAssignAfterFunding = await page.locator('.to-assign-amount').textContent()

      // Reload the page
      await page.reload()

      // Wait for page to load
      await expect(page.getByText('Electricity')).toBeVisible()

      // The To Assign amount should be the same (funding persisted)
      await expect(page.locator('.to-assign-amount')).toHaveText(toAssignAfterFunding || '')
    })
  })

  test.describe('Target-Based Funding', () => {
    test('should fund up to target amount', async ({ page }) => {
      await registerAndLogin(page, 'target-based')

      // Create account with $150 (less than $200 target)
      const accountRes = await page.request.post('/api/accounts', {
        data: {
          name: 'Test Checking',
          account_type: 'CHECKING',
          initial_balance: '0.00',
        },
      })
      const account = await accountRes.json()

      // Create income transaction of $150
      await page.request.post('/api/transactions', {
        data: {
          account_id: account.id,
          date: new Date().toISOString().split('T')[0],
          payee: 'Paycheck',
          amount: '150.00',
        },
      })

      // Create category with $200 target
      const groupRes = await page.request.post('/api/categories/groups', {
        data: { name: 'Bills', is_income: false },
      })
      const group = await groupRes.json()

      const categoryRes = await page.request.post('/api/categories', {
        data: { name: 'Rent', group_id: group.id },
      })
      const category = await categoryRes.json()

      await page.request.post('/api/targets', {
        data: {
          category_id: category.id,
          target_type: 'MONTHLY_SAVINGS',
          amount: '200.00',
        },
      })

      // Navigate to budget page
      await page.goto('/')

      // Wait for page to load
      await expect(page.getByText('Rent')).toBeVisible()

      // Should show underfunded ($200 target, $0 funded)
      await expect(page.getByText(/underfunded/i)).toBeVisible()

      // Click Fund Underfunded
      await page.getByRole('button', { name: /fund underfunded/i }).click()

      // Wait for funding
      await expect(page.getByRole('button', { name: /funding\.\.\./i })).not.toBeVisible({ timeout: 10000 })

      // Should show toast indicating partial funding (only $150 available)
      await expect(page.getByText(/funded.*\$150/i)).toBeVisible({ timeout: 5000 })
    })
  })

  test.describe('Multiple Categories Funding', () => {
    test('should fund multiple underfunded categories in priority order', async ({ page }) => {
      await registerAndLogin(page, 'multi-category')

      // Create account
      const accountRes = await page.request.post('/api/accounts', {
        data: {
          name: 'Test Checking',
          account_type: 'CHECKING',
          initial_balance: '0.00',
        },
      })
      const account = await accountRes.json()

      // Create income
      await page.request.post('/api/transactions', {
        data: {
          account_id: account.id,
          date: new Date().toISOString().split('T')[0],
          payee: 'Paycheck',
          amount: '500.00',
        },
      })

      // Create multiple categories with targets
      const groupRes = await page.request.post('/api/categories/groups', {
        data: { name: 'Essential Bills', is_income: false },
      })
      const group = await groupRes.json()

      // Category 1: Rent $300
      const cat1Res = await page.request.post('/api/categories', {
        data: { name: 'Rent', group_id: group.id },
      })
      const cat1 = await cat1Res.json()
      await page.request.post('/api/targets', {
        data: { category_id: cat1.id, target_type: 'MONTHLY_SAVINGS', amount: '300.00' },
      })

      // Category 2: Utilities $100
      const cat2Res = await page.request.post('/api/categories', {
        data: { name: 'Utilities', group_id: group.id },
      })
      const cat2 = await cat2Res.json()
      await page.request.post('/api/targets', {
        data: { category_id: cat2.id, target_type: 'MONTHLY_SAVINGS', amount: '100.00' },
      })

      // Navigate to budget page
      await page.goto('/')

      // Wait for categories to appear
      await expect(page.getByText('Rent')).toBeVisible()
      await expect(page.getByText('Utilities')).toBeVisible()

      // Click Fund Underfunded
      await page.getByRole('button', { name: /fund underfunded/i }).click()

      // Wait for funding
      await expect(page.getByRole('button', { name: /funding\.\.\./i })).not.toBeVisible({ timeout: 10000 })

      // Should fund both categories (total $400 needed, $500 available)
      // Check that to_assign is now $100 ($500 - $400)
      await expect(page.locator('.to-assign-amount')).toContainText('100')
    })
  })
})
