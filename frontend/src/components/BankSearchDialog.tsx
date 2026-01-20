/**
 * BankSearchDialog component.
 *
 * Dialog for searching and selecting a bank to connect via OpenBanking.
 */

import { useState, useEffect, useMemo } from 'react'
import { Search, Building2, Loader2 } from 'lucide-react'
import { bankConnectionService } from '@/services/bankConnectionService'
import type { Institution } from '@/types/bankConnection'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'

interface BankSearchDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConnectionInitiated?: () => void
}

export function BankSearchDialog({
  open,
  onOpenChange,
  onConnectionInitiated,
}: BankSearchDialogProps) {
  const [institutions, setInstitutions] = useState<Institution[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [connectingId, setConnectingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Load institutions when dialog opens
  useEffect(() => {
    if (open) {
      loadInstitutions()
    } else {
      // Reset state when dialog closes
      setSearchTerm('')
      setError(null)
      setConnectingId(null)
      setIsConnecting(false)
    }
  }, [open])

  async function loadInstitutions() {
    try {
      setIsLoading(true)
      setError(null)
      const data = await bankConnectionService.listInstitutions()
      setInstitutions(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load banks')
    } finally {
      setIsLoading(false)
    }
  }

  // Filter institutions by search term
  const filteredInstitutions = useMemo(() => {
    if (!searchTerm.trim()) {
      return institutions
    }
    const term = searchTerm.toLowerCase()
    return institutions.filter(
      (inst) =>
        inst.name.toLowerCase().includes(term) ||
        (inst.bic && inst.bic.toLowerCase().includes(term))
    )
  }, [institutions, searchTerm])

  async function handleSelectBank(institution: Institution) {
    try {
      setIsConnecting(true)
      setConnectingId(institution.id)
      setError(null)

      // Get the callback URL
      const redirectUrl = `${window.location.origin}/bank-callback`

      const response = await bankConnectionService.initiateConnection(
        institution.id,
        redirectUrl
      )

      // Notify parent before redirect
      onConnectionInitiated?.()

      // Redirect to bank authorization
      window.location.href = response.authorization_url
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initiate connection')
      setIsConnecting(false)
      setConnectingId(null)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Connect Your Bank</DialogTitle>
          <DialogDescription>
            Search for your bank to connect it securely via OpenBanking.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search input */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search banks..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
              disabled={isConnecting}
              data-testid="bank-search-input"
            />
          </div>

          {/* Error message */}
          {error && (
            <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
              {error}
              <Button
                variant="link"
                size="sm"
                className="ml-2 h-auto p-0 text-destructive"
                onClick={loadInstitutions}
              >
                Retry
              </Button>
            </div>
          )}

          {/* Loading state */}
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-muted-foreground">Loading banks...</span>
            </div>
          )}

          {/* Institution list */}
          {!isLoading && !error && (
            <ScrollArea className="h-[300px]">
              <div className="space-y-1 pr-4">
                {filteredInstitutions.length === 0 ? (
                  <div className="py-8 text-center text-muted-foreground">
                    {searchTerm
                      ? 'No banks found matching your search.'
                      : 'No banks available.'}
                  </div>
                ) : (
                  filteredInstitutions.map((institution) => (
                    <button
                      key={institution.id}
                      onClick={() => handleSelectBank(institution)}
                      disabled={isConnecting}
                      className="flex w-full items-center gap-3 rounded-lg border p-3 text-left transition-colors hover:bg-muted/50 focus:bg-muted/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
                      data-testid={`bank-item-${institution.id}`}
                    >
                      {/* Bank logo or placeholder */}
                      {institution.logo_url ? (
                        <img
                          src={institution.logo_url}
                          alt={`${institution.name} logo`}
                          className="h-10 w-10 rounded object-contain"
                        />
                      ) : (
                        <div className="flex h-10 w-10 items-center justify-center rounded bg-muted">
                          <Building2 className="h-5 w-5 text-muted-foreground" />
                        </div>
                      )}

                      {/* Bank info */}
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{institution.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {institution.countries.join(', ')}
                          {institution.bic && ` - ${institution.bic}`}
                        </div>
                      </div>

                      {/* Loading indicator for connecting bank */}
                      {connectingId === institution.id && (
                        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                      )}
                    </button>
                  ))
                )}
              </div>
            </ScrollArea>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default BankSearchDialog
