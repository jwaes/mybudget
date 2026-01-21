/**
 * Accounts page.
 *
 * Displays the list of accounts and allows creating new accounts.
 */

import { useState } from 'react'
import { Building2 } from 'lucide-react'
import { AccountList } from '@/components/AccountList'
import { BankSearchDialog } from '@/components/BankSearchDialog'
import { accountService } from '@/services/accountService'
import type { AccountType } from '@/types/account'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export function AccountsPage() {
  const [isCreating, setIsCreating] = useState(false)
  const [isBankSearchOpen, setIsBankSearchOpen] = useState(false)
  const [name, setName] = useState('')
  const [accountType, setAccountType] = useState<AccountType>('CHECKING')
  const [initialBalance, setInitialBalance] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  async function handleCreateAccount(e: React.FormEvent) {
    e.preventDefault()

    if (!name.trim()) {
      setError('Account name is required')
      return
    }

    if (!initialBalance.trim()) {
      setError('Initial balance is required')
      return
    }

    try {
      setError(null)
      await accountService.create({
        name: name.trim(),
        account_type: accountType,
        initial_balance: initialBalance,
      })

      // Reset form and refresh list
      setName('')
      setAccountType('CHECKING')
      setInitialBalance('')
      setIsCreating(false)
      setRefreshKey((prev) => prev + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create account')
    }
  }

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-foreground">Accounts</h1>
        {!isCreating && (
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setIsBankSearchOpen(true)}>
              <Building2 className="h-4 w-4 mr-2" />
              Connect Bank
            </Button>
            <Button onClick={() => setIsCreating(true)}>
              + New Account
            </Button>
          </div>
        )}
      </div>

      {isCreating && (
        <Card className="mb-6 max-w-md">
          <CardHeader>
            <CardTitle>Create Account</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateAccount} className="space-y-4">
              {error && (
                <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="name">Account Name</Label>
                <Input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Main Checking"
                  autoFocus
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="accountType">Account Type</Label>
                <Select value={accountType} onValueChange={(v) => setAccountType(v as AccountType)}>
                  <SelectTrigger id="accountType">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CHECKING">Checking</SelectItem>
                    <SelectItem value="SAVINGS">Savings</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="initialBalance">Initial Balance</Label>
                <Input
                  id="initialBalance"
                  type="number"
                  step="0.01"
                  value={initialBalance}
                  onChange={(e) => setInitialBalance(e.target.value)}
                  placeholder="0.00"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <Button type="submit">Create Account</Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsCreating(false)
                    setError(null)
                  }}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <AccountList key={refreshKey} />

      <BankSearchDialog
        open={isBankSearchOpen}
        onOpenChange={setIsBankSearchOpen}
        onConnectionInitiated={() => {
          setIsBankSearchOpen(false)
          setRefreshKey((prev) => prev + 1)
        }}
      />
    </div>
  )
}

export default AccountsPage
