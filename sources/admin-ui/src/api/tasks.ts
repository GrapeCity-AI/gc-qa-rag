import client, { extractData, extractPaginatedData } from './client'
import {
  ApiResponse,
  CountStats,
  HealthStatus,
  PaginatedResponse,
  PaginationMeta,
  Task,
  TaskCancelRequest,
  TaskResult,
  TaskRetryRequest,
  TaskSummary,
} from './types'

export interface ListTasksParams {
  page?: number
  page_size?: number
  status?: string
  task_type?: string
}

export const tasksApi = {
  // List tasks with pagination and filters
  async list(params: ListTasksParams = {}): Promise<{
    data: TaskSummary[]
    meta: PaginationMeta
  }> {
    const response = await client.get<PaginatedResponse<TaskSummary>>(
      '/tasks',
      { params }
    )
    return extractPaginatedData(response) as { data: TaskSummary[]; meta: PaginationMeta }
  },

  // Get a single task by ID
  async get(taskId: string): Promise<Task> {
    const response = await client.get<ApiResponse<Task>>(`/tasks/${taskId}`)
    return extractData(response)
  },

  // Get task result
  async getResult(taskId: string): Promise<TaskResult> {
    const response = await client.get<ApiResponse<TaskResult>>(
      `/tasks/${taskId}/result`
    )
    return extractData(response)
  },

  // Cancel a task
  async cancel(taskId: string, data?: TaskCancelRequest): Promise<Task> {
    const response = await client.post<ApiResponse<Task>>(
      `/tasks/${taskId}/cancel`,
      data || {}
    )
    return extractData(response)
  },

  // Retry a task
  async retry(taskId: string, data?: TaskRetryRequest): Promise<Task> {
    const response = await client.post<ApiResponse<Task>>(
      `/tasks/${taskId}/retry`,
      data || {}
    )
    return extractData(response)
  },
}

export const systemApi = {
  // Health check
  async health(): Promise<HealthStatus> {
    const response = await client.get<ApiResponse<HealthStatus>>('/health')
    return extractData(response)
  },

  // Get system stats
  async stats(): Promise<CountStats> {
    const response = await client.get<ApiResponse<CountStats>>('/stats')
    return extractData(response)
  },
}
