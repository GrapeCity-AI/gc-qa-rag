import { ConfigProvider, theme, App as AntApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './components/Layout/MainLayout'
import Dashboard from './pages/Dashboard'
import KnowledgeBaseList from './pages/KnowledgeBases/List'
import KnowledgeBaseDetail from './pages/KnowledgeBases/Detail'
import KnowledgeBaseCreate from './pages/KnowledgeBases/Create'
import TaskList from './pages/Tasks/List'
import TaskDetail from './pages/Tasks/Detail'
import Settings from './pages/Settings'

function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 6,
        },
      }}
    >
      <AntApp>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="knowledge-bases">
              <Route index element={<KnowledgeBaseList />} />
              <Route path="create" element={<KnowledgeBaseCreate />} />
              <Route path=":id" element={<KnowledgeBaseDetail />} />
            </Route>
            <Route path="tasks">
              <Route index element={<TaskList />} />
              <Route path=":id" element={<TaskDetail />} />
            </Route>
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </AntApp>
    </ConfigProvider>
  )
}

export default App
