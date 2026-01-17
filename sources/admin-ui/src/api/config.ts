import client, { extractData } from './client'
import { ApiResponse } from './types'

export interface SystemConfig {
  llm_provider: string
  llm_model: string
  storage_type: string
  vector_db_type: string
  max_concurrent_tasks: number
  default_chunk_size: number
  default_chunk_overlap: number
  features: Record<string, boolean>
}

export const configApi = {
  // Get system configuration
  async get(): Promise<SystemConfig> {
    const response = await client.get<ApiResponse<SystemConfig>>('/config')
    return extractData(response)
  },
}
