/**
 * Target Badge component.
 *
 * Displays a small badge indicating the target type and status.
 * Shows different icons/colors for each target type and funding status.
 */

import type { TargetType } from '@/types/target'

interface TargetBadgeProps {
  targetType: TargetType
  underfunded?: string
  onClick?: () => void
}

/**
 * Get icon for target type.
 */
function getTargetIcon(targetType: TargetType): string {
  switch (targetType) {
    case 'MONTHLY_NEEDED':
      return '↻' // Recurring
    case 'TARGET_BALANCE':
      return '◎' // Balance
    case 'TARGET_BY_DATE':
      return '📅' // Calendar
    default:
      return '◉'
  }
}

/**
 * Get short label for target type.
 */
function getTargetLabel(targetType: TargetType): string {
  switch (targetType) {
    case 'MONTHLY_NEEDED':
      return 'Monthly'
    case 'TARGET_BALANCE':
      return 'Balance'
    case 'TARGET_BY_DATE':
      return 'By Date'
    default:
      return 'Target'
  }
}

/**
 * Determine status based on underfunded amount.
 */
function getStatus(underfunded?: string): 'underfunded' | 'funded' | 'none' {
  if (!underfunded) return 'none'
  const amount = parseFloat(underfunded)
  if (isNaN(amount)) return 'none'
  return amount > 0 ? 'underfunded' : 'funded'
}

export function TargetBadge({ targetType, underfunded, onClick }: TargetBadgeProps) {
  const status = getStatus(underfunded)
  const icon = getTargetIcon(targetType)
  const label = getTargetLabel(targetType)

  return (
    <span
      className={`target-badge ${status} ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
      title={`${label}${underfunded ? ` - €${underfunded} underfunded` : ''}`}
    >
      <span className="badge-icon">{icon}</span>
      <span className="badge-label">{label}</span>

      <style>{`
        .target-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.125rem 0.5rem;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 500;
          background: #f0f0f0;
          color: #666;
          white-space: nowrap;
        }

        .target-badge.clickable {
          cursor: pointer;
        }

        .target-badge.clickable:hover {
          background: #e0e0e0;
        }

        .target-badge.underfunded {
          background: #fff3e0;
          color: #f57c00;
        }

        .target-badge.underfunded.clickable:hover {
          background: #ffe0b2;
        }

        .target-badge.funded {
          background: #e8f5e9;
          color: #388e3c;
        }

        .target-badge.funded.clickable:hover {
          background: #c8e6c9;
        }

        .badge-icon {
          font-size: 0.75rem;
        }

        .badge-label {
          font-size: 0.6875rem;
          text-transform: uppercase;
          letter-spacing: 0.02em;
        }
      `}</style>
    </span>
  )
}

export default TargetBadge
