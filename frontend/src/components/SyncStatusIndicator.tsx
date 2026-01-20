/**
 * SyncStatusIndicator component.
 *
 * Displays the status of a sync job with appropriate styling and icons.
 */

import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import type { SyncJobStatus, SyncJob } from '@/services/syncService'

interface SyncStatusIndicatorProps {
  /** Current status of the sync job */
  status: SyncJobStatus
  /** Number of transactions imported (shown for COMPLETED status) */
  transactionsImported?: number
  /** Number of duplicate transactions skipped (shown for COMPLETED status) */
  transactionsDuplicates?: number
  /** Error message (shown for FAILED status) */
  errorMessage?: string | null
  /** Show compact version without text */
  compact?: boolean
  /** Full sync job for detailed display */
  syncJob?: SyncJob
}

/**
 * Displays sync job status with appropriate icon, color, and details.
 */
export function SyncStatusIndicator({
  status,
  transactionsImported,
  transactionsDuplicates,
  errorMessage,
  compact = false,
  syncJob,
}: SyncStatusIndicatorProps) {
  // Use syncJob values if provided
  const imported = transactionsImported ?? syncJob?.transactions_imported ?? 0
  const duplicates = transactionsDuplicates ?? syncJob?.transactions_duplicates ?? 0
  const error = errorMessage ?? syncJob?.error_message

  switch (status) {
    case 'PENDING':
    case 'RUNNING':
      return (
        <div className="flex items-center gap-2" data-testid="sync-status-running">
          <Loader2 className="h-4 w-4 animate-spin text-primary" />
          {!compact && (
            <span className="text-sm text-muted-foreground">
              {status === 'PENDING' ? 'Waiting...' : 'Syncing...'}
            </span>
          )}
        </div>
      )

    case 'COMPLETED': {
      const hasResults = imported > 0 || duplicates > 0
      return (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2" data-testid="sync-status-completed">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                {!compact && (
                  <span className="text-sm text-green-600">
                    Completed
                    {hasResults && (
                      <span className="text-muted-foreground ml-1">
                        ({imported} imported{duplicates > 0 ? `, ${duplicates} skipped` : ''})
                      </span>
                    )}
                  </span>
                )}
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <div className="text-sm">
                <p className="font-medium">Sync completed successfully</p>
                {hasResults && (
                  <div className="mt-1">
                    <p>Transactions imported: {imported}</p>
                    <p>Duplicates skipped: {duplicates}</p>
                  </div>
                )}
              </div>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )
    }

    case 'FAILED':
      return (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2" data-testid="sync-status-failed">
                <XCircle className="h-4 w-4 text-destructive" />
                {!compact && (
                  <Badge variant="destructive" className="text-xs">
                    Failed
                  </Badge>
                )}
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <div className="text-sm max-w-xs">
                <p className="font-medium text-destructive">Sync failed</p>
                {error && <p className="mt-1 text-muted-foreground">{error}</p>}
              </div>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )

    default:
      return (
        <div className="flex items-center gap-2" data-testid="sync-status-unknown">
          <Clock className="h-4 w-4 text-muted-foreground" />
          {!compact && <span className="text-sm text-muted-foreground">Unknown</span>}
        </div>
      )
  }
}

export default SyncStatusIndicator
