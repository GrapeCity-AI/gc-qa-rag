import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { versionsApi, ListVersionsParams, ListFilesParams } from '../api/versions'
import { VersionCreate, VersionBuildRequest, VersionPublishRequest, VersionIngestRequest } from '../api/types'
import { knowledgeBaseKeys } from './useKnowledgeBases'
import { taskKeys } from './useTasks'

// Query keys
export const versionKeys = {
  all: ['versions'] as const,
  lists: () => [...versionKeys.all, 'list'] as const,
  list: (kbId: string, params: ListVersionsParams) => [...versionKeys.lists(), kbId, params] as const,
  details: () => [...versionKeys.all, 'detail'] as const,
  detail: (id: string) => [...versionKeys.details(), id] as const,
  files: (versionId: string) => [...versionKeys.all, 'files', versionId] as const,
  fileList: (versionId: string, params: ListFilesParams) => [...versionKeys.files(versionId), params] as const,
}

// List versions for a knowledge base
export function useVersions(kbId: string, params: ListVersionsParams = {}) {
  return useQuery({
    queryKey: versionKeys.list(kbId, params),
    queryFn: () => versionsApi.list(kbId, params),
    enabled: !!kbId,
    refetchInterval: 5000, // Refresh every 5 seconds
  })
}

// Get single version
export function useVersion(versionId: string) {
  return useQuery({
    queryKey: versionKeys.detail(versionId),
    queryFn: () => versionsApi.get(versionId),
    enabled: !!versionId,
    refetchInterval: (query) => {
      // Refetch every 3 seconds while version is building
      const status = query.state.data?.status
      return status === 'building' ? 3000 : false
    },
  })
}

// Create version
export function useCreateVersion(kbId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: VersionCreate) => versionsApi.create(kbId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: versionKeys.lists() })
      queryClient.invalidateQueries({ queryKey: knowledgeBaseKeys.detail(kbId) })
    },
  })
}

// Build version
export function useBuildVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ versionId, data }: { versionId: string; data: VersionBuildRequest }) =>
      versionsApi.build(versionId, data),
    onSuccess: (_, { versionId }) => {
      queryClient.invalidateQueries({ queryKey: versionKeys.detail(versionId) })
      queryClient.invalidateQueries({ queryKey: versionKeys.lists() })
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() })
    },
  })
}

// Publish version
export function usePublishVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ versionId, data }: { versionId: string; data: VersionPublishRequest }) =>
      versionsApi.publish(versionId, data),
    onSuccess: (_, { versionId }) => {
      queryClient.invalidateQueries({ queryKey: versionKeys.detail(versionId) })
      queryClient.invalidateQueries({ queryKey: versionKeys.lists() })
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() })
    },
  })
}

// Ingest version (fetch data from source)
export function useIngestVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ versionId, data }: { versionId: string; data: VersionIngestRequest }) =>
      versionsApi.ingest(versionId, data),
    onSuccess: (_, { versionId }) => {
      queryClient.invalidateQueries({ queryKey: versionKeys.detail(versionId) })
      queryClient.invalidateQueries({ queryKey: versionKeys.lists() })
      queryClient.invalidateQueries({ queryKey: versionKeys.files(versionId) })
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() })
    },
  })
}

// List files in a version
export function useVersionFiles(versionId: string, params: ListFilesParams = {}) {
  return useQuery({
    queryKey: versionKeys.fileList(versionId, params),
    queryFn: () => versionsApi.listFiles(versionId, params),
    enabled: !!versionId,
  })
}
