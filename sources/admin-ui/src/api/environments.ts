import client, { extractData, extractPaginatedData } from './client'
import {
  ApiResponse,
  PaginatedResponse,
  PaginationMeta,
} from './types'

// Environment types (add to types.ts if not already there)
export interface Environment {
  id: string
  name: string
  environment_type: string
  description: string
  config: Record<string, unknown>
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface EnvironmentSummary {
  id: string
  name: string
  environment_type: string
  is_default: boolean
  created_at: string
}

export interface EnvironmentCreate {
  name: string
  environment_type: string
  description?: string
  config?: Record<string, unknown>
  is_default?: boolean
}

export interface EnvironmentUpdate {
  name?: string
  description?: string
  config?: Record<string, unknown>
  is_default?: boolean
}

export interface EnvironmentTestResult {
  success: boolean
  message: string
  latency_ms?: number
  details: Record<string, unknown>
}

export interface ListEnvironmentsParams {
  page?: number
  page_size?: number
  environment_type?: string
}

export const environmentsApi = {
  // List environments
  async list(params: ListEnvironmentsParams = {}): Promise<{
    data: EnvironmentSummary[]
    meta: PaginationMeta
  }> {
    const response = await client.get<PaginatedResponse<EnvironmentSummary>>(
      '/environments',
      { params }
    )
    return extractPaginatedData(response) as { data: EnvironmentSummary[]; meta: PaginationMeta }
  },

  // Get a single environment
  async get(envId: string): Promise<Environment> {
    const response = await client.get<ApiResponse<Environment>>(
      `/environments/${envId}`
    )
    return extractData(response)
  },

  // Create an environment
  async create(data: EnvironmentCreate): Promise<Environment> {
    const response = await client.post<ApiResponse<Environment>>(
      '/environments',
      data
    )
    return extractData(response)
  },

  // Update an environment
  async update(envId: string, data: EnvironmentUpdate): Promise<Environment> {
    const response = await client.put<ApiResponse<Environment>>(
      `/environments/${envId}`,
      data
    )
    return extractData(response)
  },

  // Delete an environment
  async delete(envId: string): Promise<void> {
    await client.delete<ApiResponse<null>>(`/environments/${envId}`)
  },

  // Test environment connection
  async test(envId: string): Promise<EnvironmentTestResult> {
    const response = await client.post<ApiResponse<EnvironmentTestResult>>(
      `/environments/${envId}/test`
    )
    return extractData(response)
  },
}
