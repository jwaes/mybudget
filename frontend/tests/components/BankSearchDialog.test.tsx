/**
 * Unit tests for BankSearchDialog component.
 *
 * Tests bank search and connection initiation functionality.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BankSearchDialog } from '@/components/BankSearchDialog'
import type { Institution } from '@/types/bankConnection'

// Mock the bankConnectionService
vi.mock('@/services/bankConnectionService', () => ({
  bankConnectionService: {
    listInstitutions: vi.fn(),
    initiateConnection: vi.fn(),
  },
}))

import { bankConnectionService } from '@/services/bankConnectionService'

const mockBankConnectionService = vi.mocked(bankConnectionService)

const mockInstitutions: Institution[] = [
  {
    id: 'inst-1',
    name: 'ING Bank',
    bic: 'INGBNL2A',
    logo_url: 'https://example.com/ing-logo.png',
    countries: ['NL', 'BE'],
  },
  {
    id: 'inst-2',
    name: 'ABN AMRO',
    bic: 'ABNANL2A',
    logo_url: null,
    countries: ['NL'],
  },
  {
    id: 'inst-3',
    name: 'Rabobank',
    bic: 'RABONL2U',
    logo_url: 'https://example.com/rabo-logo.png',
    countries: ['NL'],
  },
]

describe('BankSearchDialog', () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
    onConnectionInitiated: vi.fn(),
  }

  // Store original window.location
  const originalLocation = window.location

  beforeEach(() => {
    vi.clearAllMocks()
    mockBankConnectionService.listInstitutions.mockResolvedValue(mockInstitutions)

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
    it('renders dialog with title and description', async () => {
      render(<BankSearchDialog {...defaultProps} />)

      expect(screen.getByText('Connect Your Bank')).toBeInTheDocument()
      expect(screen.getByText(/search for your bank/i)).toBeInTheDocument()
    })

    it('renders search input', async () => {
      render(<BankSearchDialog {...defaultProps} />)

      expect(screen.getByTestId('bank-search-input')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Search banks...')).toBeInTheDocument()
    })

    it('shows loading state initially', async () => {
      mockBankConnectionService.listInstitutions.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      render(<BankSearchDialog {...defaultProps} />)

      expect(screen.getByText('Loading banks...')).toBeInTheDocument()
    })

    it('loads and displays institutions', async () => {
      render(<BankSearchDialog {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('ING Bank')).toBeInTheDocument()
      })

      expect(screen.getByText('ABN AMRO')).toBeInTheDocument()
      expect(screen.getByText('Rabobank')).toBeInTheDocument()
    })

    it('shows country codes for each institution', async () => {
      render(<BankSearchDialog {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('ING Bank')).toBeInTheDocument()
      })

      expect(screen.getByText('NL, BE - INGBNL2A')).toBeInTheDocument()
      expect(screen.getByText('NL - ABNANL2A')).toBeInTheDocument()
    })
  })

  describe('Search functionality', () => {
    it('filters institutions by name', async () => {
      const user = userEvent.setup()
      render(<BankSearchDialog {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('ING Bank')).toBeInTheDocument()
      })

      const searchInput = screen.getByTestId('bank-search-input')
      await user.type(searchInput, 'ING')

      expect(screen.getByText('ING Bank')).toBeInTheDocument()
      expect(screen.queryByText('ABN AMRO')).not.toBeInTheDocument()
      expect(screen.queryByText('Rabobank')).not.toBeInTheDocument()
    })

    it('filters institutions by BIC code', async () => {
      const user = userEvent.setup()
      render(<BankSearchDialog {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('ING Bank')).toBeInTheDocument()
      })

      const searchInput = screen.getByTestId('bank-search-input')
      await user.type(searchInput, 'ABNANL')

      expect(screen.queryByText('ING Bank')).not.toBeInTheDocument()
      expect(screen.getByText('ABN AMRO')).toBeInTheDocument()
      expect(screen.queryByText('Rabobank')).not.toBeInTheDocument()
    })

    it('shows no results message when no banks match', async () => {
      const user = userEvent.setup()
      render(<BankSearchDialog {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('ING Bank')).toBeInTheDocument()
      })

      const searchInput = screen.getByTestId('bank-search-input')
      await user.type(searchInput, 'NonExistentBank')

      expect(screen.getByText('No banks found matching your search.')).toBeInTheDocument()
    })

    it('search is case insensitive', async () => {
      const user = userEvent.setup()
      render(<BankSearchDialog {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('ING Bank')).toBeInTheDocument()
      })

      const searchInput = screen.getByTestId('bank-search-input')
      await user.type(searchInput, 'ing')

      expect(screen.getByText('ING Bank')).toBeInTheDocument()
    })
  })

  describe('Bank selection', () => {
    it('initiates connection when bank is clicked', async () => {
      const user = userEvent.setup()
      mockBankConnectionService.initiateConnection.mockResolvedValue({
        authorization_url: 'https://bank.example.com/oauth',
        reference_id: 'ref-123',
      })

      render(<BankSearchDialog {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('ING Bank')).toBeInTheDocument()
      })

      const bankButton = screen.getByTestId('bank-item-inst-1')
      await user.click(bankButton)

      expect(mockBankConnectionService.initiateConnection).toHaveBeenCalledWith(
        'inst-1',
        'http://localhost:3000/bank-callback'
      )
    })

    it('calls onConnectionInitiated before redirect', async () => {
      const user = userEvent.setup()
      const onConnectionInitiated = vi.fn()
      mockBankConnectionService.initiateConnection.mockResolvedValue({
        authorization_url: 'https://bank.example.com/oauth',
        reference_id: 'ref-123',
      })

      render(
        <BankSearchDialog
          {...defaultProps}
          onConnectionInitiated={onConnectionInitiated}
        />
      )

      await waitFor(() => {
        expect(screen.getByText('ING Bank')).toBeInTheDocument()
      })

      const bankButton = screen.getByTestId('bank-item-inst-1')
      await user.click(bankButton)

      await waitFor(() => {
        expect(onConnectionInitiated).toHaveBeenCalled()
      })
    })

    it('redirects to authorization URL', async () => {
      const user = userEvent.setup()
      mockBankConnectionService.initiateConnection.mockResolvedValue({
        authorization_url: 'https://bank.example.com/oauth',
        reference_id: 'ref-123',
      })

      render(<BankSearchDialog {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('ING Bank')).toBeInTheDocument()
      })

      const bankButton = screen.getByTestId('bank-item-inst-1')
      await user.click(bankButton)

      await waitFor(() => {
        expect(window.location.href).toBe('https://bank.example.com/oauth')
      })
    })
  })

  describe('Error handling', () => {
    it('shows error message when loading institutions fails', async () => {
      mockBankConnectionService.listInstitutions.mockRejectedValue(
        new Error('Network error')
      )

      render(<BankSearchDialog {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument()
      })

      expect(screen.getByText('Retry')).toBeInTheDocument()
    })

    it('shows error message when connection initiation fails', async () => {
      const user = userEvent.setup()
      mockBankConnectionService.initiateConnection.mockRejectedValue(
        new Error('Connection failed')
      )

      render(<BankSearchDialog {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('ING Bank')).toBeInTheDocument()
      })

      const bankButton = screen.getByTestId('bank-item-inst-1')
      await user.click(bankButton)

      await waitFor(() => {
        expect(screen.getByText('Connection failed')).toBeInTheDocument()
      })
    })

    it('allows retry when loading fails', async () => {
      const user = userEvent.setup()
      mockBankConnectionService.listInstitutions
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockInstitutions)

      render(<BankSearchDialog {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Retry'))

      await waitFor(() => {
        expect(screen.getByText('ING Bank')).toBeInTheDocument()
      })
    })
  })

  describe('Dialog state', () => {
    it('loads institutions when dialog opens', async () => {
      const { rerender } = render(<BankSearchDialog {...defaultProps} open={false} />)

      expect(mockBankConnectionService.listInstitutions).not.toHaveBeenCalled()

      rerender(<BankSearchDialog {...defaultProps} open={true} />)

      await waitFor(() => {
        expect(mockBankConnectionService.listInstitutions).toHaveBeenCalled()
      })
    })

    it('resets state when dialog closes and reopens', async () => {
      const user = userEvent.setup()
      const { rerender } = render(<BankSearchDialog {...defaultProps} open={true} />)

      await waitFor(() => {
        expect(screen.getByText('ING Bank')).toBeInTheDocument()
      })

      // Type in search
      const searchInput = screen.getByTestId('bank-search-input')
      await user.type(searchInput, 'ING')

      // Close dialog
      rerender(<BankSearchDialog {...defaultProps} open={false} />)

      // Reopen dialog
      rerender(<BankSearchDialog {...defaultProps} open={true} />)

      await waitFor(() => {
        // Search should be reset
        expect(screen.getByTestId('bank-search-input')).toHaveValue('')
      })
    })
  })
})
