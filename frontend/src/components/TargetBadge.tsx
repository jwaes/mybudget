/**
 * Target Badge component.
 *
 * Displays a small badge indicating the target type and status.
 * Shows different icons/colors for each target type and funding status.
 */

import type { TargetType } from '@/types/target'
import { cn } from '@/lib/utils'

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

const statusStyles = {
  none: 'bg-muted text-muted-foreground hover:bg-muted/80',
  underfunded: 'bg-orange-100 text-orange-600 hover:bg-orange-200',
  funded: 'bg-green-100 text-green-600 hover:bg-green-200',
}

export function TargetBadge({ targetType, underfunded, onClick }: TargetBadgeProps) {
  const status = getStatus(underfunded)
  const icon = getTargetIcon(targetType)
  const label = getTargetLabel(targetType)

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 py-0.5 px-2 rounded-full text-xs font-medium whitespace-nowrap',
        statusStyles[status],
        onClick && 'cursor-pointer'
      )}
      onClick={onClick}
      title={`${label}${underfunded ? ` - $${underfunded} underfunded` : ''}`}
    >
      <span className="text-xs">{icon}</span>
      <span className="text-[11px] uppercase tracking-wide">{label}</span>
    </span>
  )
}

export default TargetBadge
