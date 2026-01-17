import { useEffect, useRef, useCallback } from 'react'
import { useAppStore } from '../stores/app'
import { TaskProgressUpdate } from '../api/types'

interface UseTaskWebSocketOptions {
  taskId: string
  onUpdate?: (update: TaskProgressUpdate) => void
  onError?: (error: Event) => void
  autoConnect?: boolean
}

export function useTaskWebSocket({
  taskId,
  onUpdate,
  onError,
  autoConnect = true,
}: UseTaskWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const setWsConnected = useAppStore((state) => state.setWsConnected)

  const connect = useCallback(() => {
    if (!taskId || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    // Determine WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/v1/tasks/ws/tasks/${taskId}`

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setWsConnected(true)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as TaskProgressUpdate
        onUpdate?.(data)
      } catch {
        // Ignore parse errors
      }
    }

    ws.onerror = (event) => {
      onError?.(event)
    }

    ws.onclose = () => {
      setWsConnected(false)
    }

    wsRef.current = ws
  }, [taskId, onUpdate, onError, setWsConnected])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
      setWsConnected(false)
    }
  }, [setWsConnected])

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send('ping')
    }
  }, [])

  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    // Set up ping interval
    const pingInterval = setInterval(sendPing, 30000)

    return () => {
      clearInterval(pingInterval)
      disconnect()
    }
  }, [autoConnect, connect, disconnect, sendPing])

  return {
    connect,
    disconnect,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  }
}
