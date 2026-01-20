/**
 * BankCallback page.
 *
 * Handles the OAuth callback from bank authorization.
 */

import { useEffect, useState, useCallback } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { bankConnectionService } from '@/services/bankConnectionService'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

type CallbackStatus = 'loading' | 'success' | 'error'

export function BankCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState<CallbackStatus>('loading')
  const [error, setError] = useState<string | null>(null)
  const [bankName, setBankName] = useState<string | null>(null)

  const completeOAuth = useCallback(async (reference: string) => {
    try {
      setStatus('loading')
      setError(null)

      const connection = await bankConnectionService.completeOAuth(reference)

      setBankName(connection.institution_name)
      setStatus('success')

      // Auto-redirect to accounts after 3 seconds
      setTimeout(() => {
        navigate('/accounts')
      }, 3000)
    } catch (err) {
      setStatus('error')
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to complete bank connection. Please try again.'
      )
    }
  }, [navigate])

  useEffect(() => {
    const ref = searchParams.get('ref')

    if (!ref) {
      setStatus('error')
      setError('Missing reference parameter. Please try connecting again.')
      return
    }

    completeOAuth(ref)
  }, [searchParams, completeOAuth])

  function handleGoToAccounts() {
    navigate('/accounts')
  }

  function handleTryAgain() {
    navigate('/accounts')
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle>
            {status === 'loading' && 'Connecting Your Bank'}
            {status === 'success' && 'Bank Connected!'}
            {status === 'error' && 'Connection Failed'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Loading state */}
          {status === 'loading' && (
            <div className="flex flex-col items-center space-y-4 py-8">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <p className="text-muted-foreground">
                Please wait while we complete your bank connection...
              </p>
            </div>
          )}

          {/* Success state */}
          {status === 'success' && (
            <div className="flex flex-col items-center space-y-4 py-8">
              <div className="rounded-full bg-green-100 p-3 dark:bg-green-900/20">
                <CheckCircle className="h-12 w-12 text-green-600 dark:text-green-400" />
              </div>
              <div className="text-center">
                <p className="font-medium">
                  {bankName ? `${bankName} has been connected successfully!` : 'Your bank has been connected successfully!'}
                </p>
                <p className="mt-2 text-sm text-muted-foreground">
                  You will be redirected to your accounts shortly...
                </p>
              </div>
              <Button onClick={handleGoToAccounts} className="mt-4">
                Go to Accounts
              </Button>
            </div>
          )}

          {/* Error state */}
          {status === 'error' && (
            <div className="flex flex-col items-center space-y-4 py-8">
              <div className="rounded-full bg-red-100 p-3 dark:bg-red-900/20">
                <XCircle className="h-12 w-12 text-red-600 dark:text-red-400" />
              </div>
              <div className="text-center">
                <p className="font-medium text-destructive">
                  {error || 'An unexpected error occurred.'}
                </p>
                <p className="mt-2 text-sm text-muted-foreground">
                  Please try connecting your bank again.
                </p>
              </div>
              <Button onClick={handleTryAgain} variant="outline" className="mt-4">
                Try Again
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default BankCallbackPage
