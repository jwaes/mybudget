/**
 * Unit tests for ErrorBoundary component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ErrorBoundary } from '@/components/ErrorBoundary'

// Suppress console.error during tests since ErrorBoundary logs errors
const originalConsoleError = console.error

beforeEach(() => {
  console.error = vi.fn()
})

afterEach(() => {
  console.error = originalConsoleError
})

// Component that throws an error
function ThrowError({ shouldThrow = true }: { shouldThrow?: boolean }) {
  if (shouldThrow) {
    throw new Error('Test error message')
  }
  return <div>No error occurred</div>
}

// Component that can toggle error state
function ToggleableError({
  throwOnRender,
}: {
  throwOnRender: boolean
}) {
  if (throwOnRender) {
    throw new Error('Toggled error')
  }
  return <div>Child rendered successfully</div>
}

describe('ErrorBoundary', () => {
  it('should render children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <div>Child content</div>
      </ErrorBoundary>
    )

    expect(screen.getByText('Child content')).toBeInTheDocument()
  })

  it('should render nested children correctly when no error occurs', () => {
    render(
      <ErrorBoundary>
        <div>
          <h1>Title</h1>
          <p>Paragraph</p>
          <button>Button</button>
        </div>
      </ErrorBoundary>
    )

    expect(screen.getByRole('heading', { name: 'Title' })).toBeInTheDocument()
    expect(screen.getByText('Paragraph')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Button' })).toBeInTheDocument()
  })

  it('should catch errors and show error UI', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    // Should show error UI
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(
      screen.getByText('An unexpected error occurred. Please try again.')
    ).toBeInTheDocument()

    // Should show the error message
    expect(screen.getByText('Test error message')).toBeInTheDocument()
  })

  it('should show Try Again button in error UI', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(screen.getByRole('button', { name: 'Try Again' })).toBeInTheDocument()
  })

  it('should show Reload Page button in error UI', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(
      screen.getByRole('button', { name: 'Reload Page' })
    ).toBeInTheDocument()
  })

  it('should reset state when Try Again button is clicked', async () => {
    const user = userEvent.setup()

    // We need a way to control when the error is thrown
    let shouldThrow = true

    function ConditionalError() {
      if (shouldThrow) {
        throw new Error('Conditional error')
      }
      return <div>Recovered content</div>
    }

    const { rerender } = render(
      <ErrorBoundary>
        <ConditionalError />
      </ErrorBoundary>
    )

    // Should show error UI initially
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()

    // Now set shouldThrow to false before clicking Try Again
    shouldThrow = false

    // Click Try Again
    await user.click(screen.getByRole('button', { name: 'Try Again' }))

    // After reset, the component should attempt to render children again
    // Since shouldThrow is now false, it should show recovered content
    expect(screen.getByText('Recovered content')).toBeInTheDocument()
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
  })

  it('should render custom fallback when provided', () => {
    const customFallback = <div>Custom error fallback</div>

    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError />
      </ErrorBoundary>
    )

    // Should show custom fallback instead of default UI
    expect(screen.getByText('Custom error fallback')).toBeInTheDocument()
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
  })

  it('should log error to console when error is caught', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    // componentDidCatch should log the error
    expect(console.error).toHaveBeenCalledWith(
      'Error caught by boundary:',
      expect.any(Error),
      expect.objectContaining({ componentStack: expect.any(String) })
    )
  })

  it('should call window.location.reload when Reload Page is clicked', async () => {
    const user = userEvent.setup()

    // Mock window.location.reload
    const originalLocation = window.location
    const reloadMock = vi.fn()
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, reload: reloadMock },
      writable: true,
    })

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    await user.click(screen.getByRole('button', { name: 'Reload Page' }))

    expect(reloadMock).toHaveBeenCalled()

    // Restore original location
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
    })
  })

  it('should handle multiple children', () => {
    render(
      <ErrorBoundary>
        <div>First child</div>
        <div>Second child</div>
        <div>Third child</div>
      </ErrorBoundary>
    )

    expect(screen.getByText('First child')).toBeInTheDocument()
    expect(screen.getByText('Second child')).toBeInTheDocument()
    expect(screen.getByText('Third child')).toBeInTheDocument()
  })

  it('should display error message in pre element for debugging', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    const errorPre = screen.getByText('Test error message')
    expect(errorPre.tagName).toBe('PRE')
  })
})
