import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  environmentsApi,
  ListEnvironmentsParams,
  EnvironmentCreate,
  EnvironmentUpdate,
} from '../api/environments'

// Query keys
export const environmentKeys = {
  all: ['environments'] as const,
  lists: () => [...environmentKeys.all, 'list'] as const,
  list: (params: ListEnvironmentsParams) => [...environmentKeys.lists(), params] as const,
  details: () => [...environmentKeys.all, 'detail'] as const,
  detail: (id: string) => [...environmentKeys.details(), id] as const,
}

// List environments
export function useEnvironments(params: ListEnvironmentsParams = {}) {
  return useQuery({
    queryKey: environmentKeys.list(params),
    queryFn: () => environmentsApi.list(params),
  })
}

// Get single environment
export function useEnvironment(envId: string) {
  return useQuery({
    queryKey: environmentKeys.detail(envId),
    queryFn: () => environmentsApi.get(envId),
    enabled: !!envId,
  })
}

// Create environment
export function useCreateEnvironment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: EnvironmentCreate) => environmentsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: environmentKeys.lists() })
    },
  })
}

// Update environment
export function useUpdateEnvironment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ envId, data }: { envId: string; data: EnvironmentUpdate }) =>
      environmentsApi.update(envId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: environmentKeys.detail(variables.envId) })
      queryClient.invalidateQueries({ queryKey: environmentKeys.lists() })
    },
  })
}

// Delete environment
export function useDeleteEnvironment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (envId: string) => environmentsApi.delete(envId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: environmentKeys.lists() })
    },
  })
}

// Test environment connection
export function useTestEnvironment() {
  return useMutation({
    mutationFn: (envId: string) => environmentsApi.test(envId),
  })
}
