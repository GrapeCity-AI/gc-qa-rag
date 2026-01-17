import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  DatabaseOutlined,
  ThunderboltOutlined,
  SettingOutlined,
  CloudDownloadOutlined,
  RocketOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAppStore } from '../../stores/app'

const { Sider } = Layout

const menuItems = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: 'Dashboard',
  },
  {
    key: '/knowledge-bases',
    icon: <DatabaseOutlined />,
    label: 'Knowledge Bases',
  },
  {
    key: '/sources',
    icon: <CloudDownloadOutlined />,
    label: 'Data Sources',
  },
  {
    key: '/tasks',
    icon: <ThunderboltOutlined />,
    label: 'Tasks',
  },
  {
    key: '/publishing',
    icon: <RocketOutlined />,
    label: 'Publishing',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: 'Settings',
  },
]

function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { sidebarCollapsed, setSidebarCollapsed } = useAppStore()

  const selectedKey = '/' + location.pathname.split('/')[1]

  return (
    <Sider
      collapsible
      collapsed={sidebarCollapsed}
      onCollapse={setSidebarCollapsed}
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
      }}
    >
      <div
        style={{
          height: 32,
          margin: 16,
          background: 'rgba(255, 255, 255, 0.2)',
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontWeight: 600,
        }}
      >
        {sidebarCollapsed ? 'AKS' : 'AI Knowledge Service'}
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[selectedKey]}
        items={menuItems}
        onClick={({ key }) => navigate(key)}
      />
    </Sider>
  )
}

export default Sidebar
