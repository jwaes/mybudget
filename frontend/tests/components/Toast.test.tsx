/**
 * Unit tests for Toast component.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ToastProvider, useToast } from '@/components/Toast'

// Test component that uses the toast hook
function ToastTester() {
  const { showToast, showSuccess, showError, showInfo, showWarning } = useToast()

  return (
    <div>
      <button onClick={() => showToast('Default toast')}>Show Default</button>
      <button onClick={() => showSuccess('Success message')}>Show Success</button>
      <button onClick={() => showError('Error message')}>Show Error</button>
      <button onClick={() => showInfo('Info message')}>Show Info</button>
      <button onClick={() => showWarning('Warning message')}>Show Warning</button>
    </div>
  )
}

describe('Toast', () => {
  it('should render children', () => {
    render(
      <ToastProvider>
        <div>Test Content</div>
      </ToastProvider>
    )

    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('should throw error when useToast is used outside provider', () => {
    // Suppress console.error for this test
    const originalError = console.error
    console.error = vi.fn()

    expect(() => {
      render(<ToastTester />)
    }).toThrow('useToast must be used within a ToastProvider')

    console.error = originalError
  })

  it('should show toast message when showToast is called', async () => {
    const user = userEvent.setup()

    render(
      <ToastProvider>
        <ToastTester />
      </ToastProvider>
    )

    await user.click(screen.getByText('Show Default'))

    await waitFor(() => {
      expect(screen.getByText('Default toast')).toBeInTheDocument()
    })
  })

  it('should show success toast with correct styling', async () => {
    const user = userEvent.setup()

    render(
      <ToastProvider>
        <ToastTester />
      </ToastProvider>
    )

    await user.click(screen.getByText('Show Success'))

    await waitFor(() => {
      const toastElement = screen.getByText('Success message').closest('div')
      expect(toastElement).toHaveClass('bg-green-600')
    })
  })

  it('should show error toast with correct styling', async () => {
    const user = userEvent.setup()

    render(
      <ToastProvider>
        <ToastTester />
      </ToastProvider>
    )

    await user.click(screen.getByText('Show Error'))

    await waitFor(() => {
      const toastElement = screen.getByText('Error message').closest('div')
      expect(toastElement).toHaveClass('bg-destructive')
    })
  })

  it('should show info toast with correct styling', async () => {
    const user = userEvent.setup()

    render(
      <ToastProvider>
        <ToastTester />
      </ToastProvider>
    )

    await user.click(screen.getByText('Show Info'))

    await waitFor(() => {
      const toastElement = screen.getByText('Info message').closest('div')
      expect(toastElement).toHaveClass('bg-primary')
    })
  })

  it('should show warning toast with correct styling', async () => {
    const user = userEvent.setup()

    render(
      <ToastProvider>
        <ToastTester />
      </ToastProvider>
    )

    await user.click(screen.getByText('Show Warning'))

    await waitFor(() => {
      const toastElement = screen.getByText('Warning message').closest('div')
      expect(toastElement).toHaveClass('bg-amber-500')
    })
  })

  it('should show multiple toasts', async () => {
    const user = userEvent.setup()

    render(
      <ToastProvider>
        <ToastTester />
      </ToastProvider>
    )

    await user.click(screen.getByText('Show Success'))
    await user.click(screen.getByText('Show Error'))

    await waitFor(() => {
      expect(screen.getByText('Success message')).toBeInTheDocument()
      expect(screen.getByText('Error message')).toBeInTheDocument()
    })
  })

  it('should have close button for toast', async () => {
    const user = userEvent.setup()

    render(
      <ToastProvider>
        <ToastTester />
      </ToastProvider>
    )

    await user.click(screen.getByText('Show Success'))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument()
    })
  })
})
