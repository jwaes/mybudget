/**
 * Bank connection service for MyBudget.
 *
 * Handles bank connection operations via OpenBanking providers.
 */

import { api } from './api'
import type {
  BankConnection,
  BankConnectionWithAccounts,
  Institution,
  InitiateConnectionResponse,
  InstitutionListResponse,
  ConnectionListResponse,
} from '@/types/bankConnection'

/**
 * Bank connection service with methods for managing bank connections.
 */
export const bankConnectionService = {
  /**
   * Initiate a new bank connection.
   *
   * @param institutionId - The ID of the institution to connect to
   * @param redirectUrl - The URL to redirect to after authorization
   * @returns The authorization URL and reference ID
   */
  async initiateConnection(
    institutionId: string,
    redirectUrl: string
  ): Promise<InitiateConnectionResponse> {
    return api.post<InitiateConnectionResponse>('/connections/initiate', {
      institution_id: institutionId,
      redirect_url: redirectUrl,
    })
  },

  /**
   * Complete the OAuth flow after bank authorization.
   *
   * @param reference - The reference ID from the callback
   * @returns The created bank connection
   */
  async completeOAuth(reference: string): Promise<BankConnection> {
    return api.get<BankConnection>(`/connections/callback?ref=${encodeURIComponent(reference)}`)
  },

  /**
   * Get all bank connections for the current user.
   *
   * @returns List of bank connections
   */
  async listConnections(): Promise<BankConnection[]> {
    const response = await api.get<ConnectionListResponse>('/connections/')
    return response.connections
  },

  /**
   * Get a single bank connection by ID with linked accounts.
   *
   * @param id - Connection ID
   * @returns The bank connection with linked accounts
   */
  async getConnection(id: string): Promise<BankConnectionWithAccounts> {
    return api.get<BankConnectionWithAccounts>(`/connections/${id}`)
  },

  /**
   * Disconnect a bank connection.
   *
   * @param id - Connection ID
   */
  async disconnect(id: string): Promise<void> {
    return api.delete(`/connections/${id}`)
  },

  /**
   * Initiate re-authentication for a connection.
   *
   * @param id - Connection ID
   * @param redirectUrl - The URL to redirect to after authorization
   * @returns The authorization URL and reference ID
   */
  async initiateReauth(
    id: string,
    redirectUrl: string
  ): Promise<InitiateConnectionResponse> {
    return api.post<InitiateConnectionResponse>(`/connections/${id}/reauth`, {
      redirect_url: redirectUrl,
    })
  },

  /**
   * Get available institutions for connection.
   *
   * @param country - Optional country code to filter by
   * @returns List of institutions
   */
  async listInstitutions(country?: string): Promise<Institution[]> {
    const params = country ? `?country=${encodeURIComponent(country)}` : ''
    const response = await api.get<InstitutionListResponse>(`/institutions/${params}`)
    return response.institutions
  },
}

export default bankConnectionService
