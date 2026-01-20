/**
 * Unit tests for ConnectionStatusBadge component.
 *
 * Tests the display of bank connection health status.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ConnectionStatusBadge } from '@/components/ConnectionStatusBadge'
import type { ConnectionHealthStatus } from '@/types/bankConnection'

describe('ConnectionStatusBadge', () => {
  describe('Healthy status', () => {
    it('renders healthy status with correct label', () => {
      render(<ConnectionStatusBadge status="healthy" />)

      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    it('has correct test id', () => {
      render(<ConnectionStatusBadge status="healthy" />)

      expect(screen.getByTestId('connection-status-healthy')).toBeInTheDocument()
    })

    it('renders checkmark icon', () => {
      render(<ConnectionStatusBadge status="healthy" />)

      const badge = screen.getByTestId('connection-status-healthy')
      expect(badge.querySelector('svg')).toBeInTheDocument()
    })
  })

  describe('Warning status', () => {
    it('renders warning status with correct label', () => {
      render(<ConnectionStatusBadge status="warning" />)

      expect(screen.getByText('Attention')).toBeInTheDocument()
    })

    it('has correct test id', () => {
      render(<ConnectionStatusBadge status="warning" />)

      expect(screen.getByTestId('connection-status-warning')).toBeInTheDocument()
    })
  })

  describe('Error status', () => {
    it('renders error status with correct label', () => {
      render(<ConnectionStatusBadge status="error" />)

      expect(screen.getByText('Error')).toBeInTheDocument()
    })

    it('has correct test id', () => {
      render(<ConnectionStatusBadge status="error" />)

      expect(screen.getByTestId('connection-status-error')).toBeInTheDocument()
    })
  })

  describe('Styling', () => {
    it('applies custom className', () => {
      render(<ConnectionStatusBadge status="healthy" className="custom-class" />)

      const badge = screen.getByTestId('connection-status-healthy')
      expect(badge).toHaveClass('custom-class')
    })

    it('healthy status has green styling', () => {
      render(<ConnectionStatusBadge status="healthy" />)

      const badge = screen.getByTestId('connection-status-healthy')
      // Check for green-related classes
      expect(badge.className).toMatch(/green/)
    })

    it('warning status has yellow styling', () => {
      render(<ConnectionStatusBadge status="warning" />)

      const badge = screen.getByTestId('connection-status-warning')
      // Check for yellow-related classes
      expect(badge.className).toMatch(/yellow/)
    })

    it('error status has red styling', () => {
      render(<ConnectionStatusBadge status="error" />)

      const badge = screen.getByTestId('connection-status-error')
      // Check for red-related classes
      expect(badge.className).toMatch(/red/)
    })
  })

  describe('All status types', () => {
    const statuses: ConnectionHealthStatus[] = ['healthy', 'warning', 'error']

    it.each(statuses)('renders %s status correctly', (status) => {
      render(<ConnectionStatusBadge status={status} />)

      expect(screen.getByTestId(`connection-status-${status}`)).toBeInTheDocument()
    })
  })

  describe('Last sync time', () => {
    it('does not break when lastSyncAt is undefined', () => {
      render(<ConnectionStatusBadge status="healthy" />)

      expect(screen.getByTestId('connection-status-healthy')).toBeInTheDocument()
    })

    it('does not break when lastSyncAt is null', () => {
      render(<ConnectionStatusBadge status="healthy" lastSyncAt={null} />)

      expect(screen.getByTestId('connection-status-healthy')).toBeInTheDocument()
    })

    it('accepts a valid lastSyncAt date', () => {
      render(
        <ConnectionStatusBadge
          status="healthy"
          lastSyncAt="2026-01-18T10:00:00Z"
        />
      )

      expect(screen.getByTestId('connection-status-healthy')).toBeInTheDocument()
    })
  })
})
