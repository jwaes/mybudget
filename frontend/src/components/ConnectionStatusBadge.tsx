/**
 * ConnectionStatusBadge component.
 *
 * Displays the health status of a bank connection with appropriate color and icon.
 */

import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import type { ConnectionHealthStatus } from '@/types/bankConnection'
import { cn } from '@/lib/utils'

interface ConnectionStatusBadgeProps {
  status: ConnectionHealthStatus
  lastSyncAt?: string | null
  className?: string
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

const statusConfig: Record<
  ConnectionHealthStatus,
  {
    icon: typeof CheckCircle
    label: string
    tooltip: string
    badgeClass: string
    iconClass: string
  }
> = {
  healthy: {
    icon: CheckCircle,
    label: 'Connected',
    tooltip: 'Bank connection is healthy and syncing normally',
    badgeClass: 'bg-green-100 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800',
    iconClass: 'text-green-600 dark:text-green-400',
  },
  warning: {
    icon: AlertTriangle,
    label: 'Attention',
    tooltip: 'Bank connection needs attention - access may expire soon',
    badgeClass: 'bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-400 dark:border-yellow-800',
    iconClass: 'text-yellow-600 dark:text-yellow-400',
  },
  error: {
    icon: XCircle,
    label: 'Error',
    tooltip: 'Bank connection has an error and needs to be reconnected',
    badgeClass: 'bg-red-100 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800',
    iconClass: 'text-red-600 dark:text-red-400',
  },
}

export function ConnectionStatusBadge({
  status,
  lastSyncAt,
  className,
}: ConnectionStatusBadgeProps) {
  const config = statusConfig[status]
  const Icon = config.icon

  const tooltipContent = lastSyncAt
    ? `${config.tooltip}. Last synced ${formatRelativeTime(lastSyncAt)}`
    : config.tooltip

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge
            variant="outline"
            className={cn(config.badgeClass, 'cursor-help gap-1', className)}
            data-testid={`connection-status-${status}`}
          >
            <Icon className={cn('h-3.5 w-3.5', config.iconClass)} />
            <span>{config.label}</span>
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <p>{tooltipContent}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

export default ConnectionStatusBadge
