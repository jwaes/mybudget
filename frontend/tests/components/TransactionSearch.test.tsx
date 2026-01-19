/**
 * Unit tests for TransactionSearch component.
 *
 * Tests search input rendering, debounced onChange callback, and value syncing.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { TransactionSearch } from '@/components/TransactionSearch'

describe('TransactionSearch', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Rendering', () => {
    it('should render with default placeholder text', () => {
      render(<TransactionSearch value="" onChange={() => {}} />)

      expect(screen.getByPlaceholderText('Search payee or memo...')).toBeInTheDocument()
    })

    it('should render with custom placeholder text', () => {
      render(<TransactionSearch value="" onChange={() => {}} placeholder="Custom search..." />)

      expect(screen.getByPlaceholderText('Custom search...')).toBeInTheDocument()
    })

    it('should show search icon', () => {
      const { container } = render(<TransactionSearch value="" onChange={() => {}} />)

      // Search icon from lucide-react has the lucide-search class
      const searchIcon = container.querySelector('.lucide-search')
      expect(searchIcon).toBeInTheDocument()
    })

    it('should render with initial value', () => {
      render(<TransactionSearch value="initial search" onChange={() => {}} />)

      expect(screen.getByDisplayValue('initial search')).toBeInTheDocument()
    })
  })

  describe('Debounced onChange', () => {
    it('should not call onChange immediately when typing', () => {
      const onChange = vi.fn()
      render(<TransactionSearch value="" onChange={onChange} />)

      const input = screen.getByPlaceholderText('Search payee or memo...')
      fireEvent.change(input, { target: { value: 'test' } })

      // onChange should not be called immediately
      expect(onChange).not.toHaveBeenCalled()
    })

    it('should call onChange after 300ms debounce delay', () => {
      const onChange = vi.fn()
      render(<TransactionSearch value="" onChange={onChange} />)

      const input = screen.getByPlaceholderText('Search payee or memo...')
      fireEvent.change(input, { target: { value: 'test search' } })

      // Should not be called before 300ms
      act(() => {
        vi.advanceTimersByTime(299)
      })
      expect(onChange).not.toHaveBeenCalled()

      // Should be called after 300ms
      act(() => {
        vi.advanceTimersByTime(1)
      })
      expect(onChange).toHaveBeenCalledTimes(1)
      expect(onChange).toHaveBeenCalledWith('test search')
    })

    it('should debounce multiple rapid keystrokes', () => {
      const onChange = vi.fn()
      render(<TransactionSearch value="" onChange={onChange} />)

      const input = screen.getByPlaceholderText('Search payee or memo...')

      // Type multiple characters rapidly
      fireEvent.change(input, { target: { value: 't' } })
      act(() => {
        vi.advanceTimersByTime(100)
      })

      fireEvent.change(input, { target: { value: 'te' } })
      act(() => {
        vi.advanceTimersByTime(100)
      })

      fireEvent.change(input, { target: { value: 'tes' } })
      act(() => {
        vi.advanceTimersByTime(100)
      })

      fireEvent.change(input, { target: { value: 'test' } })

      // Should still not be called
      expect(onChange).not.toHaveBeenCalled()

      // Wait for full debounce delay after last keystroke
      act(() => {
        vi.advanceTimersByTime(300)
      })

      // Should only be called once with final value
      expect(onChange).toHaveBeenCalledTimes(1)
      expect(onChange).toHaveBeenCalledWith('test')
    })
  })

  describe('Local Value Updates', () => {
    it('should update local value immediately when typing', () => {
      render(<TransactionSearch value="" onChange={() => {}} />)

      const input = screen.getByPlaceholderText('Search payee or memo...')
      fireEvent.change(input, { target: { value: 'new value' } })

      // Input should show new value immediately (before debounce)
      expect(screen.getByDisplayValue('new value')).toBeInTheDocument()
    })

    it('should maintain local value during debounce period', () => {
      render(<TransactionSearch value="" onChange={() => {}} />)

      const input = screen.getByPlaceholderText('Search payee or memo...')
      fireEvent.change(input, { target: { value: 'typing...' } })

      act(() => {
        vi.advanceTimersByTime(150)
      })

      // Input should still show the typed value
      expect(screen.getByDisplayValue('typing...')).toBeInTheDocument()
    })
  })

  describe('External Value Sync', () => {
    it('should sync with external value prop changes', () => {
      const { rerender } = render(<TransactionSearch value="" onChange={() => {}} />)

      expect(screen.getByDisplayValue('')).toBeInTheDocument()

      // Simulate external value change (e.g., from parent component)
      rerender(<TransactionSearch value="external value" onChange={() => {}} />)

      expect(screen.getByDisplayValue('external value')).toBeInTheDocument()
    })

    it('should update when external value is cleared', () => {
      const { rerender } = render(<TransactionSearch value="initial" onChange={() => {}} />)

      expect(screen.getByDisplayValue('initial')).toBeInTheDocument()

      // Clear from parent
      rerender(<TransactionSearch value="" onChange={() => {}} />)

      expect(screen.getByDisplayValue('')).toBeInTheDocument()
    })

    it('should sync external value even after user has typed', () => {
      const { rerender } = render(<TransactionSearch value="" onChange={() => {}} />)

      const input = screen.getByPlaceholderText('Search payee or memo...')
      fireEvent.change(input, { target: { value: 'user typed' } })

      expect(screen.getByDisplayValue('user typed')).toBeInTheDocument()

      // External value change should override local value
      rerender(<TransactionSearch value="external override" onChange={() => {}} />)

      expect(screen.getByDisplayValue('external override')).toBeInTheDocument()
    })
  })
})
