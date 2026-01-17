import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { knowledgeBasesApi, ListKnowledgeBasesParams } from '../api/knowledge-bases'
import { KnowledgeBaseCreate, KnowledgeBaseUpdate } from '../api/types'

// Query keys
export const knowledgeBaseKeys = {
  all: ['knowledge-bases'] as const,
  lists: () => [...knowledgeBaseKeys.all, 'list'] as const,
  list: (params: ListKnowledgeBasesParams) => [...knowledgeBaseKeys.lists(), params] as const,
  details: () => [...knowledgeBaseKeys.all, 'detail'] as const,
  detail: (id: string) => [...knowledgeBaseKeys.details(), id] as const,
}

// List knowledge bases
export function useKnowledgeBases(params: ListKnowledgeBasesParams = {}) {
  return useQuery({
    queryKey: knowledgeBaseKeys.list(params),
    queryFn: () => knowledgeBasesApi.list(params),
  })
}

// Get single knowledge base
export function useKnowledgeBase(id: string) {
  return useQuery({
    queryKey: knowledgeBaseKeys.detail(id),
    queryFn: () => knowledgeBasesApi.get(id),
    enabled: !!id,
  })
}

// Create knowledge base
export function useCreateKnowledgeBase() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: KnowledgeBaseCreate) => knowledgeBasesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: knowledgeBaseKeys.lists() })
    },
  })
}

// Update knowledge base
export function useUpdateKnowledgeBase(id: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: KnowledgeBaseUpdate) => knowledgeBasesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: knowledgeBaseKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: knowledgeBaseKeys.lists() })
    },
  })
}

// Delete knowledge base
export function useDeleteKnowledgeBase() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => knowledgeBasesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: knowledgeBaseKeys.lists() })
    },
  })
}
