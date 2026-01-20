/**
 * Account types for MyBudget.
 */

import type { ConnectionHealthStatus } from './bankConnection'

export type AccountType = 'CHECKING' | 'SAVINGS'

export type SyncStatus = 'SUCCESS' | 'FAILED' | 'PENDING' | 'NEVER_SYNCED'

export interface Account {
  id: string
  user_id: string
  name: string
  account_type: AccountType
  balance: string
  initial_balance: string
  sync_status: SyncStatus
  last_sync_at: string | null
  sync_error: string | null
  created_at: string
  updated_at: string
  // Bank connection fields (present for linked accounts)
  bank_connection_id?: string | null
  bank_connection_name?: string | null
  bank_connection_health?: ConnectionHealthStatus | null
}

export interface AccountCreate {
  name: string
  account_type: AccountType
  initial_balance: string
}

export interface AccountUpdate {
  name?: string
}

export interface AccountListResponse {
  accounts: Account[]
  total: number
}
