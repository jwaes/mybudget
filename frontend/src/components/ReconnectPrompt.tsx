/**
 * ReconnectPrompt component.
 *
 * Alert banner shown when a bank connection needs re-authentication.
 */

import { useState } from 'react'
import { AlertCircle, Loader2, RefreshCw } from 'lucide-react'
import { bankConnectionService } from '@/services/bankConnectionService'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

interface ReconnectPromptProps {
  connectionId: string
  bankName: string
  onReconnectInitiated?: () => void
  className?: string
}

export function ReconnectPrompt({
  connectionId,
  bankName,
  onReconnectInitiated,
  className,
}: ReconnectPromptProps) {
  const [isReconnecting, setIsReconnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleReconnect() {
    try {
      setIsReconnecting(true)
      setError(null)

      const redirectUrl = `${window.location.origin}/bank-callback`
      const response = await bankConnectionService.initiateReauth(connectionId, redirectUrl)

      // Notify parent before redirect
      onReconnectInitiated?.()

      // Redirect to bank authorization
      window.location.href = response.authorization_url
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initiate reconnection')
      setIsReconnecting(false)
    }
  }

  return (
    <Alert variant="destructive" className={className} data-testid="reconnect-prompt">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Bank Connection Needs Attention</AlertTitle>
      <AlertDescription className="mt-2">
        <p className="mb-3">
          Your connection to <strong>{bankName}</strong> needs to be re-authenticated.
          Please reconnect to continue syncing your accounts.
        </p>
        {error && (
          <p className="mb-3 text-sm text-destructive">
            {error}
          </p>
        )}
        <Button
          size="sm"
          variant="outline"
          onClick={handleReconnect}
          disabled={isReconnecting}
          className="gap-2"
        >
          {isReconnecting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Reconnecting...
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4" />
              Reconnect {bankName}
            </>
          )}
        </Button>
      </AlertDescription>
    </Alert>
  )
}

export default ReconnectPrompt
