/**
 * Formatting utilities for currency, dates, and numbers.
 */

/**
 * Format a number or string as currency (USD by default).
 *
 * @param amount - The amount to format (number or string)
 * @param currency - Currency code (default: 'USD')
 * @param locale - Locale for formatting (default: 'en-US')
 * @returns Formatted currency string (e.g., "$1,234.56")
 */
export function formatCurrency(
  amount: number | string,
  currency: string = 'USD',
  locale: string = 'en-US'
): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  if (isNaN(num)) return '$0.00'

  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num)
}

/**
 * Format a number with decimal places.
 *
 * @param value - The value to format
 * @param decimals - Number of decimal places (default: 2)
 * @param locale - Locale for formatting (default: 'en-US')
 * @returns Formatted number string (e.g., "1,234.56")
 */
export function formatDecimal(
  value: number | string,
  decimals: number = 2,
  locale: string = 'en-US'
): string {
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '0.00'

  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num)
}

/**
 * Format a date as month and year (e.g., "January 2024").
 *
 * @param date - Date object, ISO string, or YYYY-MM format string
 * @param locale - Locale for formatting (default: 'en-US')
 * @returns Formatted month-year string
 */
export function formatMonthYear(
  date: Date | string,
  locale: string = 'en-US'
): string {
  let d: Date

  if (typeof date === 'string') {
    // Handle YYYY-MM format (e.g., "2024-01")
    if (/^\d{4}-\d{2}$/.test(date)) {
      const parts = date.split('-').map(Number)
      const year = parts[0] ?? 0
      const month = parts[1] ?? 1
      d = new Date(year, month - 1, 1)
    } else {
      d = new Date(date)
    }
  } else {
    d = date
  }

  if (isNaN(d.getTime())) return ''

  return d.toLocaleDateString(locale, {
    month: 'long',
    year: 'numeric',
  })
}

/**
 * Format a date in short format (e.g., "Jan 15, 2024").
 *
 * @param date - Date object or ISO string
 * @param locale - Locale for formatting (default: 'en-US')
 * @returns Formatted date string
 */
export function formatDate(
  date: Date | string,
  locale: string = 'en-US'
): string {
  const d = typeof date === 'string' ? new Date(date) : date
  if (isNaN(d.getTime())) return ''

  return d.toLocaleDateString(locale, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

/**
 * Format a date in ISO format (YYYY-MM-DD).
 *
 * @param date - Date object
 * @returns ISO date string (e.g., "2024-01-15")
 */
export function formatISODate(date: Date): string {
  const isoStr = date.toISOString()
  return isoStr.split('T')[0] ?? isoStr.substring(0, 10)
}

/**
 * Get the first day of a month as YYYY-MM-DD string.
 *
 * @param year - Year
 * @param month - Month (1-12)
 * @returns ISO date string for first day of month
 */
export function getMonthFirstDay(year: number, month: number): string {
  return `${year}-${month.toString().padStart(2, '0')}-01`
}

/**
 * Parse a YYYY-MM string into year and month numbers.
 *
 * @param monthStr - Month string in YYYY-MM format
 * @returns Object with year and month (1-12), or null if invalid
 */
export function parseMonthString(monthStr: string): { year: number; month: number } | null {
  const match = monthStr.match(/^(\d{4})-(\d{2})$/)
  if (!match || !match[1] || !match[2]) return null

  return {
    year: parseInt(match[1], 10),
    month: parseInt(match[2], 10),
  }
}

/**
 * Get display class for an amount (positive/negative styling).
 *
 * @param amount - The amount (number or string)
 * @returns CSS class name ('positive', 'negative', or 'zero')
 */
export function getAmountClass(amount: number | string): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  if (isNaN(num) || num === 0) return 'zero'
  return num > 0 ? 'positive' : 'negative'
}
