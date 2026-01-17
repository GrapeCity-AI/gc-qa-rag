import { useQuery, useMutation } from '@tanstack/react-query'
import { connectorsApi } from '../api/connectors'
import { ConnectorTestRequest } from '../api/types'

// Query keys
export const connectorKeys = {
  all: ['connectors'] as const,
  list: () => [...connectorKeys.all, 'list'] as const,
  detail: (type: string) => [...connectorKeys.all, 'detail', type] as const,
}

// List connectors
export function useConnectors() {
  return useQuery({
    queryKey: connectorKeys.list(),
    queryFn: () => connectorsApi.list(),
    staleTime: 5 * 60 * 1000, // Connector types rarely change
  })
}

// Get single connector
export function useConnector(connectorType: string) {
  return useQuery({
    queryKey: connectorKeys.detail(connectorType),
    queryFn: () => connectorsApi.get(connectorType),
    enabled: !!connectorType,
  })
}

// Test connector
export function useTestConnector() {
  return useMutation({
    mutationFn: (data: ConnectorTestRequest) => connectorsApi.test(data),
  })
}
