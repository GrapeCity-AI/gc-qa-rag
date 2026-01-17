import client, { extractData, extractPaginatedData } from './client'
import {
  ApiResponse,
  FileVersion,
  PaginatedResponse,
  PaginationMeta,
  Task,
  Version,
  VersionBuildRequest,
  VersionCreate,
  VersionPublishRequest,
  VersionSummary,
} from './types'

export interface ListVersionsParams {
  page?: number
  page_size?: number
}

export interface ListFilesParams {
  page?: number
  page_size?: number
  status?: string
}

export const versionsApi = {
  // List versions for a knowledge base
  async list(kbId: string, params: ListVersionsParams = {}): Promise<{
    data: VersionSummary[]
    meta: PaginationMeta
  }> {
    const response = await client.get<PaginatedResponse<VersionSummary>>(
      `/knowledge-bases/${kbId}/versions`,
      { params }
    )
    return extractPaginatedData(response) as { data: VersionSummary[]; meta: PaginationMeta }
  },

  // Get a single version by ID
  async get(versionId: string): Promise<Version> {
    const response = await client.get<ApiResponse<Version>>(
      `/versions/${versionId}`
    )
    return extractData(response)
  },

  // Create a new version
  async create(kbId: string, data: VersionCreate): Promise<Version> {
    const response = await client.post<ApiResponse<Version>>(
      `/knowledge-bases/${kbId}/versions`,
      data
    )
    return extractData(response)
  },

  // Trigger a build for a version
  async build(versionId: string, data: VersionBuildRequest): Promise<Task> {
    const response = await client.post<ApiResponse<Task>>(
      `/versions/${versionId}/build`,
      data
    )
    return extractData(response)
  },

  // Trigger publishing for a version
  async publish(versionId: string, data: VersionPublishRequest): Promise<Task> {
    const response = await client.post<ApiResponse<Task>>(
      `/versions/${versionId}/publish`,
      data
    )
    return extractData(response)
  },

  // List files in a version
  async listFiles(versionId: string, params: ListFilesParams = {}): Promise<{
    data: FileVersion[]
    meta: PaginationMeta
  }> {
    const response = await client.get<PaginatedResponse<FileVersion>>(
      `/versions/${versionId}/files`,
      { params }
    )
    return extractPaginatedData(response) as { data: FileVersion[]; meta: PaginationMeta }
  },
}
