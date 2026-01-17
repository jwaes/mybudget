/**
 * Account types for MyBudget.
 */

export type AccountType = 'CHECKING' | 'SAVINGS'

export interface Account {
  id: string
  user_id: string
  name: string
  account_type: AccountType
  balance: string
  initial_balance: string
  created_at: string
  updated_at: string
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
