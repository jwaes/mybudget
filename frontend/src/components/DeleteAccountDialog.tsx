/**
 * DeleteAccountDialog component.
 *
 * Confirmation dialog shown before deleting an account.
 */

import { useState } from 'react'
import { AlertTriangle, Loader2 } from 'lucide-react'
import { accountService } from '@/services/accountService'
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'

interface DeleteAccountDialogAccount {
  id: string
  name: string
  bank_connection_id?: string | null
}

interface DeleteAccountDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  account: DeleteAccountDialogAccount
  onDeleted?: () => void
}

export function DeleteAccountDialog({
  open,
  onOpenChange,
  account,
  onDeleted,
}: DeleteAccountDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isBankConnected = !!account.bank_connection_id

  async function handleDelete(e: React.MouseEvent) {
    e.preventDefault()
    try {
      setIsDeleting(true)
      setError(null)

      await accountService.delete(account.id)

      onOpenChange(false)
      onDeleted?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete account')
      setIsDeleting(false)
    }
  }

  function handleCancel() {
    if (!isDeleting) {
      setError(null)
      onOpenChange(false)
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-red-100 p-2 dark:bg-red-900/20">
              <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />
            </div>
            <AlertDialogTitle>Delete {account.name}?</AlertDialogTitle>
          </div>
          <AlertDialogDescription className="pt-2" asChild>
            <div>
              <p className="mb-3">
                This action cannot be undone. The account will be permanently deleted.
              </p>
              <ul className="list-disc pl-5 space-y-1 text-sm">
                <li>All transactions in this account will be deleted</li>
                {isBankConnected && (
                  <li>
                    This will unlink the account from your bank connection
                  </li>
                )}
                {isBankConnected && (
                  <li>
                    Your bank connection will be preserved for other accounts
                  </li>
                )}
              </ul>
              {error && (
                <p className="mt-3 text-sm text-destructive">
                  Error: {error}
                </p>
              )}
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={handleCancel} disabled={isDeleting}>
            Cancel
          </AlertDialogCancel>
          <Button
            onClick={handleDelete}
            disabled={isDeleting}
            variant="destructive"
          >
            {isDeleting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete'
            )}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

export default DeleteAccountDialog
