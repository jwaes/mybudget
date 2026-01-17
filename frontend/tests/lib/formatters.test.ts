/**
 * Tests for formatting utilities.
 */

import { describe, it, expect } from 'vitest'
import {
  formatCurrency,
  formatDecimal,
  formatMonthYear,
  formatDate,
  formatISODate,
  getMonthFirstDay,
  parseMonthString,
  getAmountClass,
} from '@/lib/formatters'

describe('formatCurrency', () => {
  it('should format positive numbers as USD', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56')
  })

  it('should format negative numbers', () => {
    expect(formatCurrency(-1234.56)).toBe('-$1,234.56')
  })

  it('should format string amounts', () => {
    expect(formatCurrency('99.99')).toBe('$99.99')
  })

  it('should format zero', () => {
    expect(formatCurrency(0)).toBe('$0.00')
  })

  it('should handle NaN gracefully', () => {
    expect(formatCurrency('invalid')).toBe('$0.00')
  })

  it('should round to 2 decimal places', () => {
    expect(formatCurrency(1.999)).toBe('$2.00')
    expect(formatCurrency(1.001)).toBe('$1.00')
  })

  it('should add thousands separators', () => {
    expect(formatCurrency(1000000)).toBe('$1,000,000.00')
  })
})

describe('formatDecimal', () => {
  it('should format with default 2 decimals', () => {
    expect(formatDecimal(1234.5)).toBe('1,234.50')
  })

  it('should format with custom decimals', () => {
    expect(formatDecimal(1234.5678, 4)).toBe('1,234.5678')
    expect(formatDecimal(1234.5678, 0)).toBe('1,235')
  })

  it('should format string values', () => {
    expect(formatDecimal('99.9')).toBe('99.90')
  })

  it('should handle NaN gracefully', () => {
    expect(formatDecimal('invalid')).toBe('0.00')
  })
})

describe('formatMonthYear', () => {
  it('should format Date object', () => {
    const date = new Date(2024, 0, 15) // January 15, 2024
    expect(formatMonthYear(date)).toBe('January 2024')
  })

  it('should format ISO date string', () => {
    expect(formatMonthYear('2024-06-15')).toBe('June 2024')
  })

  it('should format YYYY-MM string', () => {
    expect(formatMonthYear('2024-12')).toBe('December 2024')
  })

  it('should handle invalid date gracefully', () => {
    expect(formatMonthYear('invalid')).toBe('')
  })
})

describe('formatDate', () => {
  it('should format Date object', () => {
    const date = new Date(2024, 0, 15)
    expect(formatDate(date)).toBe('Jan 15, 2024')
  })

  it('should format ISO string', () => {
    expect(formatDate('2024-06-01')).toBe('Jun 1, 2024')
  })

  it('should handle invalid date gracefully', () => {
    expect(formatDate('invalid')).toBe('')
  })
})

describe('formatISODate', () => {
  it('should format Date to YYYY-MM-DD', () => {
    const date = new Date(2024, 5, 15) // June 15, 2024
    expect(formatISODate(date)).toBe('2024-06-15')
  })

  it('should pad single digit months and days', () => {
    const date = new Date(2024, 0, 5) // January 5, 2024
    expect(formatISODate(date)).toBe('2024-01-05')
  })
})

describe('getMonthFirstDay', () => {
  it('should return first day of month in YYYY-MM-DD format', () => {
    expect(getMonthFirstDay(2024, 1)).toBe('2024-01-01')
    expect(getMonthFirstDay(2024, 12)).toBe('2024-12-01')
  })

  it('should pad single digit months', () => {
    expect(getMonthFirstDay(2024, 6)).toBe('2024-06-01')
  })
})

describe('parseMonthString', () => {
  it('should parse valid YYYY-MM string', () => {
    expect(parseMonthString('2024-06')).toEqual({ year: 2024, month: 6 })
    expect(parseMonthString('2024-12')).toEqual({ year: 2024, month: 12 })
  })

  it('should return null for invalid format', () => {
    expect(parseMonthString('2024')).toBeNull()
    expect(parseMonthString('2024-6')).toBeNull()
    expect(parseMonthString('invalid')).toBeNull()
    expect(parseMonthString('2024-06-01')).toBeNull()
  })
})

describe('getAmountClass', () => {
  it('should return "positive" for positive amounts', () => {
    expect(getAmountClass(100)).toBe('positive')
    expect(getAmountClass('50.00')).toBe('positive')
  })

  it('should return "negative" for negative amounts', () => {
    expect(getAmountClass(-100)).toBe('negative')
    expect(getAmountClass('-50.00')).toBe('negative')
  })

  it('should return "zero" for zero', () => {
    expect(getAmountClass(0)).toBe('zero')
    expect(getAmountClass('0.00')).toBe('zero')
  })

  it('should return "zero" for invalid values', () => {
    expect(getAmountClass('invalid')).toBe('zero')
  })
})
