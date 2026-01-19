import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tasksApi, systemApi, ListTasksParams } from '../api/tasks'
import { TaskCancelRequest, TaskRetryRequest } from '../api/types'

// Query keys
export const taskKeys = {
  all: ['tasks'] as const,
  lists: () => [...taskKeys.all, 'list'] as const,
  list: (params: ListTasksParams) => [...taskKeys.lists(), params] as const,
  details: () => [...taskKeys.all, 'detail'] as const,
  detail: (id: string) => [...taskKeys.details(), id] as const,
  results: () => [...taskKeys.all, 'result'] as const,
  result: (id: string) => [...taskKeys.results(), id] as const,
}

export const systemKeys = {
  health: ['system', 'health'] as const,
  stats: ['system', 'stats'] as const,
}

// List tasks
export function useTasks(params: ListTasksParams = {}) {
  return useQuery({
    queryKey: taskKeys.list(params),
    queryFn: () => tasksApi.list(params),
    refetchInterval: 5000, // Refresh every 5 seconds
  })
}

// Get single task
export function useTask(taskId: string) {
  return useQuery({
    queryKey: taskKeys.detail(taskId),
    queryFn: () => tasksApi.get(taskId),
    enabled: !!taskId,
    refetchInterval: (query) => {
      // Refetch every 2 seconds while task is running
      const status = query.state.data?.status
      return status === 'pending' || status === 'running' ? 2000 : false
    },
  })
}

// Get task result
export function useTaskResult(taskId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: taskKeys.result(taskId),
    queryFn: () => tasksApi.getResult(taskId),
    enabled: enabled && !!taskId,
  })
}

// Cancel task
export function useCancelTask() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: string; data?: TaskCancelRequest }) =>
      tasksApi.cancel(taskId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: taskKeys.detail(variables.taskId) })
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() })
    },
  })
}

// Retry task
export function useRetryTask() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: string; data?: TaskRetryRequest }) =>
      tasksApi.retry(taskId, data),
    onSuccess: (newTask, variables) => {
      queryClient.invalidateQueries({ queryKey: taskKeys.detail(variables.taskId) })
      queryClient.invalidateQueries({ queryKey: taskKeys.detail(newTask.id) })
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() })
    },
  })
}

// Health check
export function useHealth() {
  return useQuery({
    queryKey: systemKeys.health,
    queryFn: () => systemApi.health(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })
}

// System stats
export function useStats() {
  return useQuery({
    queryKey: systemKeys.stats,
    queryFn: () => systemApi.stats(),
    refetchInterval: 10000, // Refresh every 10 seconds
  })
}
