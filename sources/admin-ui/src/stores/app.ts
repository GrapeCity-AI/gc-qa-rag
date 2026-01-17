import { create } from 'zustand'

interface AppState {
  // Sidebar state
  sidebarCollapsed: boolean
  setSidebarCollapsed: (collapsed: boolean) => void
  toggleSidebar: () => void

  // Current selection
  selectedKnowledgeBaseId: string | null
  setSelectedKnowledgeBaseId: (id: string | null) => void

  // WebSocket connection status
  wsConnected: boolean
  setWsConnected: (connected: boolean) => void
}

export const useAppStore = create<AppState>((set) => ({
  // Sidebar
  sidebarCollapsed: false,
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  // Current selection
  selectedKnowledgeBaseId: null,
  setSelectedKnowledgeBaseId: (id) => set({ selectedKnowledgeBaseId: id }),

  // WebSocket
  wsConnected: false,
  setWsConnected: (connected) => set({ wsConnected: connected }),
}))
