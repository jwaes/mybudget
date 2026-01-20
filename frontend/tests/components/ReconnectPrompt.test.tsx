/**
 * Unit tests for ReconnectPrompt component.
 *
 * Tests the re-authentication prompt for bank connections.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ReconnectPrompt } from '@/components/ReconnectPrompt'

// Mock the bankConnectionService
vi.mock('@/services/bankConnectionService', () => ({
  bankConnectionService: {
    initiateReauth: vi.fn(),
  },
}))

import { bankConnectionService } from '@/services/bankConnectionService'

const mockBankConnectionService = vi.mocked(bankConnectionService)

describe('ReconnectPrompt', () => {
  const defaultProps = {
    connectionId: 'conn-123',
    bankName: 'ING Bank',
    onReconnectInitiated: vi.fn(),
  }

  // Store original window.location
  const originalLocation = window.location

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: {
        ...originalLocation,
        origin: 'http://localhost:3000',
        href: '',
      },
      writable: true,
    })
  })

  afterEach(() => {
    // Restore window.location
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
    })
    vi.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('renders alert with title', () => {
      render(<ReconnectPrompt {...defaultProps} />)

      expect(screen.getByText('Bank Connection Needs Attention')).toBeInTheDocument()
    })

    it('shows the bank name in the description', () => {
      render(<ReconnectPrompt {...defaultProps} />)

      // Bank name appears in description and button - check description specifically
      expect(screen.getByText(/Your connection to/)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reconnect ing bank/i })).toBeInTheDocument()
    })

    it('has a reconnect button', () => {
      render(<ReconnectPrompt {...defaultProps} />)

      expect(screen.getByRole('button', { name: /reconnect/i })).toBeInTheDocument()
    })

    it('has correct test id', () => {
      render(<ReconnectPrompt {...defaultProps} />)

      expect(screen.getByTestId('reconnect-prompt')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(<ReconnectPrompt {...defaultProps} className="custom-class" />)

      const alert = screen.getByTestId('reconnect-prompt')
      expect(alert).toHaveClass('custom-class')
    })
  })

  describe('Reconnect flow', () => {
    it('initiates reauth when reconnect button is clicked', async () => {
      const user = userEvent.setup()
      mockBankConnectionService.initiateReauth.mockResolvedValue({
        authorization_url: 'https://bank.example.com/reauth',
        reference_id: 'ref-456',
      })

      render(<ReconnectPrompt {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: /reconnect/i }))

      expect(mockBankConnectionService.initiateReauth).toHaveBeenCalledWith(
        'conn-123',
        'http://localhost:3000/bank-callback'
      )
    })

    it('calls onReconnectInitiated before redirect', async () => {
      const user = userEvent.setup()
      const onReconnectInitiated = vi.fn()
      mockBankConnectionService.initiateReauth.mockResolvedValue({
        authorization_url: 'https://bank.example.com/reauth',
        reference_id: 'ref-456',
      })

      render(
        <ReconnectPrompt
          {...defaultProps}
          onReconnectInitiated={onReconnectInitiated}
        />
      )

      await user.click(screen.getByRole('button', { name: /reconnect/i }))

      await waitFor(() => {
        expect(onReconnectInitiated).toHaveBeenCalled()
      })
    })

    it('redirects to authorization URL', async () => {
      const user = userEvent.setup()
      mockBankConnectionService.initiateReauth.mockResolvedValue({
        authorization_url: 'https://bank.example.com/reauth',
        reference_id: 'ref-456',
      })

      render(<ReconnectPrompt {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: /reconnect/i }))

      await waitFor(() => {
        expect(window.location.href).toBe('https://bank.example.com/reauth')
      })
    })

    it('shows loading state while reconnecting', async () => {
      const user = userEvent.setup()
      mockBankConnectionService.initiateReauth.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      render(<ReconnectPrompt {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: /reconnect/i }))

      await waitFor(() => {
        expect(screen.getByText(/reconnecting/i)).toBeInTheDocument()
      })

      // Button should be disabled
      expect(screen.getByRole('button', { name: /reconnecting/i })).toBeDisabled()
    })
  })

  describe('Error handling', () => {
    it('shows error message when reauth fails', async () => {
      const user = userEvent.setup()
      mockBankConnectionService.initiateReauth.mockRejectedValue(
        new Error('Reauth failed')
      )

      render(<ReconnectPrompt {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: /reconnect/i }))

      await waitFor(() => {
        expect(screen.getByText('Reauth failed')).toBeInTheDocument()
      })
    })

    it('button is re-enabled after error', async () => {
      const user = userEvent.setup()
      mockBankConnectionService.initiateReauth.mockRejectedValue(
        new Error('Reauth failed')
      )

      render(<ReconnectPrompt {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: /reconnect/i }))

      await waitFor(() => {
        expect(screen.getByText('Reauth failed')).toBeInTheDocument()
      })

      // Button should be enabled again
      expect(screen.getByRole('button', { name: /reconnect/i })).not.toBeDisabled()
    })

    it('allows retry after error', async () => {
      const user = userEvent.setup()
      mockBankConnectionService.initiateReauth
        .mockRejectedValueOnce(new Error('Reauth failed'))
        .mockResolvedValueOnce({
          authorization_url: 'https://bank.example.com/reauth',
          reference_id: 'ref-789',
        })

      render(<ReconnectPrompt {...defaultProps} />)

      // First attempt fails
      await user.click(screen.getByRole('button', { name: /reconnect/i }))

      await waitFor(() => {
        expect(screen.getByText('Reauth failed')).toBeInTheDocument()
      })

      // Second attempt succeeds
      await user.click(screen.getByRole('button', { name: /reconnect/i }))

      await waitFor(() => {
        expect(window.location.href).toBe('https://bank.example.com/reauth')
      })
    })
  })

  describe('Different bank names', () => {
    it('displays the correct bank name', () => {
      render(<ReconnectPrompt {...defaultProps} bankName="ABN AMRO" />)

      // Bank name appears in description and button
      expect(screen.getByText(/Your connection to/)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reconnect abn amro/i })).toBeInTheDocument()
    })
  })
})
