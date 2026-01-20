/**
 * DisconnectConfirmDialog component.
 *
 * Confirmation dialog shown before disconnecting a bank connection.
 */

import { useState } from 'react'
import { AlertTriangle, Loader2 } from 'lucide-react'
import { bankConnectionService } from '@/services/bankConnectionService'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'

interface DisconnectConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  connectionId: string
  bankName: string
  accountCount?: number
  onDisconnected?: () => void
}

export function DisconnectConfirmDialog({
  open,
  onOpenChange,
  connectionId,
  bankName,
  accountCount = 0,
  onDisconnected,
}: DisconnectConfirmDialogProps) {
  const [isDisconnecting, setIsDisconnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleDisconnect() {
    try {
      setIsDisconnecting(true)
      setError(null)

      await bankConnectionService.disconnect(connectionId)

      onOpenChange(false)
      onDisconnected?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect')
      setIsDisconnecting(false)
    }
  }

  function handleCancel() {
    if (!isDisconnecting) {
      setError(null)
      onOpenChange(false)
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-yellow-100 p-2 dark:bg-yellow-900/20">
              <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
            </div>
            <AlertDialogTitle>Disconnect {bankName}?</AlertDialogTitle>
          </div>
          <AlertDialogDescription className="pt-2">
            <p className="mb-3">
              Are you sure you want to disconnect your {bankName} connection?
            </p>
            <ul className="list-disc pl-5 space-y-1 text-sm">
              <li>
                {accountCount > 0
                  ? `${accountCount} linked account${accountCount > 1 ? 's' : ''} will stop syncing automatically`
                  : 'Your linked accounts will stop syncing automatically'}
              </li>
              <li>Transaction history will be preserved</li>
              <li>You can reconnect at any time</li>
            </ul>
            {error && (
              <p className="mt-3 text-sm text-destructive">
                Error: {error}
              </p>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={handleCancel} disabled={isDisconnecting}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDisconnect}
            disabled={isDisconnecting}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isDisconnecting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Disconnecting...
              </>
            ) : (
              'Disconnect'
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

export default DisconnectConfirmDialog
