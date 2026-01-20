/**
 * Sync service for MyBudget.
 *
 * Handles bank connection sync operations.
 */

import { api } from './api'

/**
 * Sync job status types.
 */
export type SyncJobStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'

/**
 * Sync job response from the API.
 */
export interface SyncJob {
  id: string
  connection_id: string
  status: SyncJobStatus
  started_at: string | null
  completed_at: string | null
  transactions_imported: number
  transactions_duplicates: number
  error_message: string | null
  created_at: string
  updated_at: string
}

/**
 * Sync jobs list response.
 */
export interface SyncJobListResponse {
  jobs: SyncJob[]
  total: number
}

/**
 * Sync job list query parameters.
 */
export interface SyncJobListParams {
  connection_id?: string
  status?: SyncJobStatus
  limit?: number
  offset?: number
}

/**
 * Sync service with methods for managing bank sync operations.
 */
export const syncService = {
  /**
   * Trigger a manual sync for a bank connection.
   *
   * @param connectionId - The bank connection ID
   * @returns The created sync job
   */
  async triggerSync(connectionId: string): Promise<SyncJob> {
    return api.post<SyncJob>(`/connections/${connectionId}/sync`)
  },

  /**
   * Get a list of sync jobs.
   *
   * @param params - Query parameters for filtering
   * @returns List of sync jobs
   */
  async listJobs(params?: SyncJobListParams): Promise<SyncJobListResponse> {
    const searchParams = new URLSearchParams()
    if (params?.connection_id) {
      searchParams.set('connection_id', params.connection_id)
    }
    if (params?.status) {
      searchParams.set('status', params.status)
    }
    if (params?.limit !== undefined) {
      searchParams.set('limit', params.limit.toString())
    }
    if (params?.offset !== undefined) {
      searchParams.set('offset', params.offset.toString())
    }

    const query = searchParams.toString()
    const endpoint = query ? `/sync-jobs?${query}` : '/sync-jobs'
    return api.get<SyncJobListResponse>(endpoint)
  },

  /**
   * Get a sync job by ID.
   *
   * @param jobId - The sync job ID
   * @returns The sync job details
   */
  async getJob(jobId: string): Promise<SyncJob> {
    return api.get<SyncJob>(`/sync-jobs/${jobId}`)
  },

  /**
   * Poll a sync job until it completes or fails.
   *
   * @param jobId - The sync job ID
   * @param intervalMs - Polling interval in milliseconds (default: 2000)
   * @param maxAttempts - Maximum polling attempts (default: 60)
   * @returns The final sync job state
   */
  async pollUntilComplete(
    jobId: string,
    intervalMs: number = 2000,
    maxAttempts: number = 60
  ): Promise<SyncJob> {
    let attempts = 0

    const poll = async (): Promise<SyncJob> => {
      attempts++
      const job = await this.getJob(jobId)

      if (job.status === 'COMPLETED' || job.status === 'FAILED') {
        return job
      }

      if (attempts >= maxAttempts) {
        throw new Error('Sync job polling timed out')
      }

      await new Promise((resolve) => setTimeout(resolve, intervalMs))
      return poll()
    }

    return poll()
  },
}

export default syncService
