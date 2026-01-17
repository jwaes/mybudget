/**
 * Unit tests for MonthNavigator component.
 *
 * Tests month navigation and boundary handling.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MonthNavigator } from '@/components/MonthNavigator'

describe('MonthNavigator', () => {
  describe('Display', () => {
    it('should display the current month name', () => {
      render(<MonthNavigator month="2026-01" onMonthChange={() => {}} />)

      expect(screen.getByText('January 2026')).toBeInTheDocument()
    })

    it('should display different months correctly', () => {
      const { rerender } = render(
        <MonthNavigator month="2026-06" onMonthChange={() => {}} />
      )
      expect(screen.getByText('June 2026')).toBeInTheDocument()

      rerender(<MonthNavigator month="2025-12" onMonthChange={() => {}} />)
      expect(screen.getByText('December 2025')).toBeInTheDocument()
    })

    it('should have previous and next month buttons', () => {
      render(<MonthNavigator month="2026-01" onMonthChange={() => {}} />)

      expect(screen.getByRole('button', { name: /previous month/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /next month/i })).toBeInTheDocument()
    })
  })

  describe('Navigation', () => {
    it('should call onMonthChange with previous month when clicking previous', async () => {
      const user = userEvent.setup()
      const onMonthChange = vi.fn()

      render(<MonthNavigator month="2026-03" onMonthChange={onMonthChange} />)

      await user.click(screen.getByRole('button', { name: /previous month/i }))

      expect(onMonthChange).toHaveBeenCalledWith('2026-02')
    })

    it('should call onMonthChange with next month when clicking next', async () => {
      const user = userEvent.setup()
      const onMonthChange = vi.fn()

      render(<MonthNavigator month="2026-03" onMonthChange={onMonthChange} />)

      await user.click(screen.getByRole('button', { name: /next month/i }))

      expect(onMonthChange).toHaveBeenCalledWith('2026-04')
    })
  })

  describe('Year Boundary Handling', () => {
    it('should go to December of previous year when going before January', async () => {
      const user = userEvent.setup()
      const onMonthChange = vi.fn()

      render(<MonthNavigator month="2026-01" onMonthChange={onMonthChange} />)

      await user.click(screen.getByRole('button', { name: /previous month/i }))

      expect(onMonthChange).toHaveBeenCalledWith('2025-12')
    })

    it('should go to January of next year when going after December', async () => {
      const user = userEvent.setup()
      const onMonthChange = vi.fn()

      render(<MonthNavigator month="2026-12" onMonthChange={onMonthChange} />)

      await user.click(screen.getByRole('button', { name: /next month/i }))

      expect(onMonthChange).toHaveBeenCalledWith('2027-01')
    })

    it('should display correct month when crossing year boundary', () => {
      const { rerender } = render(
        <MonthNavigator month="2025-12" onMonthChange={() => {}} />
      )
      expect(screen.getByText('December 2025')).toBeInTheDocument()

      rerender(<MonthNavigator month="2026-01" onMonthChange={() => {}} />)
      expect(screen.getByText('January 2026')).toBeInTheDocument()
    })
  })

  describe('Month Padding', () => {
    it('should format single-digit months with leading zero', async () => {
      const user = userEvent.setup()
      const onMonthChange = vi.fn()

      render(<MonthNavigator month="2026-10" onMonthChange={onMonthChange} />)

      await user.click(screen.getByRole('button', { name: /previous month/i }))

      // September should be '09' not '9'
      expect(onMonthChange).toHaveBeenCalledWith('2026-09')
    })

    it('should handle January (month 01) correctly', async () => {
      const user = userEvent.setup()
      const onMonthChange = vi.fn()

      render(<MonthNavigator month="2026-02" onMonthChange={onMonthChange} />)

      await user.click(screen.getByRole('button', { name: /previous month/i }))

      expect(onMonthChange).toHaveBeenCalledWith('2026-01')
    })
  })
})
