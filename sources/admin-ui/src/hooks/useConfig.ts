import { useQuery } from '@tanstack/react-query'
import { configApi } from '../api/config'

// Query keys
export const configKeys = {
  config: ['system', 'config'] as const,
}

// Get system configuration
export function useSystemConfig() {
  return useQuery({
    queryKey: configKeys.config,
    queryFn: () => configApi.get(),
    staleTime: 5 * 60 * 1000, // Config rarely changes
  })
}
