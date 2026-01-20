/**
 * Bank connection types for MyBudget.
 *
 * Types for managing bank connections via OpenBanking providers.
 */

/**
 * Health status of a bank connection.
 */
export type ConnectionHealthStatus = 'healthy' | 'warning' | 'error'

/**
 * Status of a bank connection lifecycle.
 */
export type BankConnectionStatus =
  | 'PENDING'
  | 'ACTIVE'
  | 'NEEDS_ATTENTION'
  | 'ERROR'
  | 'DISCONNECTED'
  | 'PENDING_REAUTH'

/**
 * Bank institution available for connection.
 */
export interface Institution {
  id: string
  name: string
  bic: string | null
  logo_url: string | null
  countries: string[]
}

/**
 * A bank connection to a financial institution.
 */
export interface BankConnection {
  id: string
  user_id: string
  provider: string
  institution_id: string
  institution_name: string
  status: BankConnectionStatus
  health_status: ConnectionHealthStatus
  last_sync_at: string | null
  next_sync_at: string | null
  access_valid_until: string | null
  created_at: string
  updated_at: string
}

/**
 * A linked account from a bank connection.
 */
export interface LinkedAccount {
  id: string
  provider_account_id: string
  iban: string | null
  name: string
  account_type: string
  currency: string
  is_active: boolean
}

/**
 * Bank connection with its linked accounts.
 */
export interface BankConnectionWithAccounts extends BankConnection {
  linked_accounts: LinkedAccount[]
}

/**
 * Response from initiating a connection.
 */
export interface InitiateConnectionResponse {
  authorization_url: string
  reference_id: string
}

/**
 * Response from listing institutions.
 */
export interface InstitutionListResponse {
  institutions: Institution[]
  total: number
}

/**
 * Response from listing connections.
 */
export interface ConnectionListResponse {
  connections: BankConnection[]
  total: number
}
