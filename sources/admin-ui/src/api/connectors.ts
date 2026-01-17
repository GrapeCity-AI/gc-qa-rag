import client, { extractData } from './client'
import {
  ApiResponse,
  ConnectorType,
  ConnectorTestRequest,
  ConnectorTestResponse,
} from './types'

export const connectorsApi = {
  // List available connector types
  async list(): Promise<ConnectorType[]> {
    const response = await client.get<ApiResponse<ConnectorType[]>>('/connectors')
    return extractData(response)
  },

  // Get a specific connector type
  async get(connectorType: string): Promise<ConnectorType> {
    const response = await client.get<ApiResponse<ConnectorType>>(
      `/connectors/${connectorType}`
    )
    return extractData(response)
  },

  // Test a connector configuration
  async test(data: ConnectorTestRequest): Promise<ConnectorTestResponse> {
    const response = await client.post<ApiResponse<ConnectorTestResponse>>(
      '/connectors/test',
      data
    )
    return extractData(response)
  },
}
