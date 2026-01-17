import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios'
import { ApiError, ApiResponse } from './types'

// Create axios instance with base configuration
const client: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor to handle errors
client.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<ApiResponse<unknown>>) => {
    if (error.response?.data?.errors) {
      // Return the error response data for handling
      return Promise.reject(error.response.data.errors)
    }

    // Network or other errors
    const apiError: ApiError = {
      code: 'network_error',
      message: error.message || 'Network error occurred',
    }
    return Promise.reject([apiError])
  }
)

export default client

// Helper function to extract data from API response
export function extractData<T>(response: AxiosResponse<ApiResponse<T>>): T {
  if (response.data.errors && response.data.errors.length > 0) {
    throw response.data.errors
  }
  if (response.data.data === null) {
    throw [{ code: 'no_data', message: 'No data returned' }]
  }
  return response.data.data
}

// Helper function to extract paginated data
export function extractPaginatedData<T>(response: AxiosResponse<{ data: T[]; meta: unknown }>): {
  data: T[]
  meta: unknown
} {
  return {
    data: response.data.data,
    meta: response.data.meta,
  }
}
