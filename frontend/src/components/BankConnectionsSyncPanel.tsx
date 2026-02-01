/**
 * BankConnectionsSyncPanel component.
 *
 * Displays bank connections with sync controls and status indicators.
 */

import { useEffect, useState, useCallback } from 'react'
import { RefreshCw, Building2, AlertCircle } from 'lucide-react'
import { bankConnectionService } from '@/services/bankConnectionService'
import { syncService, type SyncJob } from '@/services/syncService'
import { SyncStatusIndicator } from './SyncStatusIndicator'
import { useToast } from '@/components/Toast'
import type { BankConnection } from '@/types/bankConnection'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

interface SyncState {
  isLoading: boolean
  currentJob: SyncJob | null
  error: string | null
}

interface BankConnectionsSyncPanelProps {
  /** Callback when sync completes (e.g., to refresh transactions) */
  onSyncComplete?: () => void
}

/**
 * Displays bank connections with sync controls.
 */
export function BankConnectionsSyncPanel({ onSyncComplete }: BankConnectionsSyncPanelProps) {
  const [connections, setConnections] = useState<BankConnection[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [syncStates, setSyncStates] = useState<Record<string, SyncState>>({})
  const { showSuccess, showError } = useToast()

  useEffect(() => {
    loadConnections()
  }, [])

  async function loadConnections() {
    try {
      setIsLoading(true)
      setError(null)
      const connectionsList = await bankConnectionService.listConnections()
      setConnections(connectionsList)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bank connections')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSync = useCallback(
    async (connectionId: string, institutionName: string) => {
      // Update sync state to loading
      setSyncStates((prev) => ({
        ...prev,
        [connectionId]: { isLoading: true, currentJob: null, error: null },
      }))

      try {
        // Trigger sync
        const job = await syncService.triggerSync(connectionId)

        // Update state with current job
        setSyncStates((prev) => ({
          ...prev,
          [connectionId]: { isLoading: true, currentJob: job, error: null },
        }))

        // Poll until complete
        const finalJob = await syncService.pollUntilComplete(job.id)

        // Update state with final result
        setSyncStates((prev) => ({
          ...prev,
          [connectionId]: { isLoading: false, currentJob: finalJob, error: null },
        }))

        if (finalJob.status === 'COMPLETED') {
          const message =
            finalJob.transactions_imported > 0
              ? `Synced ${institutionName}: ${finalJob.transactions_imported} transactions imported`
              : `Synced ${institutionName}: No new transactions`
          showSuccess(message)
          onSyncComplete?.()
        } else if (finalJob.status === 'FAILED') {
          showError(`Sync failed: ${finalJob.error_message || 'Unknown error'}`)
        }

        // Refresh connections to update last_sync_at
        await loadConnections()
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Sync failed'
        setSyncStates((prev) => ({
          ...prev,
          [connectionId]: { isLoading: false, currentJob: null, error: errorMessage },
        }))
        showError(errorMessage)
      }
    },
    [onSyncComplete, showSuccess, showError]
  )

  function formatRelativeTime(dateString: string | null): string {
    if (!dateString) return 'Never'
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

  function getHealthBadgeVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
    switch (status) {
      case 'healthy':
        return 'default'
      case 'warning':
        return 'secondary'
      case 'error':
        return 'destructive'
      default:
        return 'outline'
    }
  }

  function formatExpiryDate(dateString: string | null): string {
    if (!dateString) return 'Unknown'
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = date.getTime() - now.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays < 0) return 'Expired'
    if (diffDays === 0) return 'Expires today'
    if (diffDays === 1) return 'Expires tomorrow'
    if (diffDays < 7) return `Expires in ${diffDays} days`
    if (diffDays < 30) return `Expires in ${Math.floor(diffDays / 7)} weeks`
    return `Expires ${date.toLocaleDateString()}`
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Bank Connections
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Bank Connections
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center">
          <p className="text-destructive mb-4">Error: {error}</p>
          <Button onClick={loadConnections}>Retry</Button>
        </CardContent>
      </Card>
    )
  }

  if (connections.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Bank Connections
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center text-muted-foreground">
          <p>No bank connections yet.</p>
          <p className="text-sm mt-1">Connect a bank to sync transactions automatically.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Building2 className="h-5 w-5" />
          Bank Connections
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {connections.map((connection) => {
            const syncState = syncStates[connection.id]
            const isActive = connection.status === 'ACTIVE'

            return (
              <div
                key={connection.id}
                className="flex items-center justify-between p-3 border rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{connection.institution_name}</span>
                      <Badge variant={getHealthBadgeVariant(connection.health_status)}>
                        {connection.health_status}
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground space-y-0.5">
                      <div>Last synced: {formatRelativeTime(connection.last_sync_at)}</div>
                      <div>{formatExpiryDate(connection.access_valid_until)}</div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {/* Show sync status only after sync completes (not during loading - button handles that) */}
                  {syncState?.currentJob && !syncState.isLoading && (
                    <SyncStatusIndicator
                      status={syncState.currentJob.status}
                      transactionsImported={syncState.currentJob.transactions_imported}
                      transactionsDuplicates={syncState.currentJob.transactions_duplicates}
                      errorMessage={syncState.currentJob.error_message}
                    />
                  )}

                  {/* Sync button */}
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSync(connection.id, connection.institution_name)}
                          disabled={!isActive || syncState?.isLoading}
                          aria-label={`Sync ${connection.institution_name}`}
                        >
                          <RefreshCw
                            className={`h-4 w-4 mr-1.5 ${syncState?.isLoading ? 'animate-spin' : ''}`}
                          />
                          {syncState?.isLoading ? 'Syncing...' : 'Sync Now'}
                        </Button>
                      </TooltipTrigger>
                      {!isActive && (
                        <TooltipContent>
                          <div className="flex items-center gap-2">
                            <AlertCircle className="h-4 w-4" />
                            <span>Connection is not active. Re-authenticate to sync.</span>
                          </div>
                        </TooltipContent>
                      )}
                    </Tooltip>
                  </TooltipProvider>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

export default BankConnectionsSyncPanel
