import client, { extractData, extractPaginatedData } from './client'
import {
  ApiResponse,
  KnowledgeBase,
  KnowledgeBaseCreate,
  KnowledgeBaseSummary,
  KnowledgeBaseUpdate,
  PaginatedResponse,
  PaginationMeta,
} from './types'

export interface ListKnowledgeBasesParams {
  page?: number
  page_size?: number
  search?: string
}

export const knowledgeBasesApi = {
  // List knowledge bases with pagination
  async list(params: ListKnowledgeBasesParams = {}): Promise<{
    data: KnowledgeBaseSummary[]
    meta: PaginationMeta
  }> {
    const response = await client.get<PaginatedResponse<KnowledgeBaseSummary>>(
      '/knowledge-bases',
      { params }
    )
    return extractPaginatedData(response) as { data: KnowledgeBaseSummary[]; meta: PaginationMeta }
  },

  // Get a single knowledge base by ID
  async get(id: string): Promise<KnowledgeBase> {
    const response = await client.get<ApiResponse<KnowledgeBase>>(
      `/knowledge-bases/${id}`
    )
    return extractData(response)
  },

  // Create a new knowledge base
  async create(data: KnowledgeBaseCreate): Promise<KnowledgeBase> {
    const response = await client.post<ApiResponse<KnowledgeBase>>(
      '/knowledge-bases',
      data
    )
    return extractData(response)
  },

  // Update a knowledge base
  async update(id: string, data: KnowledgeBaseUpdate): Promise<KnowledgeBase> {
    const response = await client.put<ApiResponse<KnowledgeBase>>(
      `/knowledge-bases/${id}`,
      data
    )
    return extractData(response)
  },

  // Delete a knowledge base
  async delete(id: string): Promise<void> {
    await client.delete(`/knowledge-bases/${id}`)
  },
}
