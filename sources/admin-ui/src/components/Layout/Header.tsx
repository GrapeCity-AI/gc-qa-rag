import { Layout, Badge, Space, Typography } from 'antd'
import { CheckCircleOutlined, SyncOutlined } from '@ant-design/icons'
import { useHealth } from '../../hooks/useTasks'

const { Header: AntHeader } = Layout
const { Text } = Typography

function Header() {
  const { data: health, isLoading } = useHealth()

  return (
    <AntHeader
      style={{
        padding: '0 24px',
        background: '#fff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
        borderBottom: '1px solid #f0f0f0',
      }}
    >
      <Space size="middle">
        <Space>
          {isLoading ? (
            <SyncOutlined spin style={{ color: '#1677ff' }} />
          ) : health?.status === 'healthy' ? (
            <Badge status="success" />
          ) : (
            <Badge status="error" />
          )}
          <Text type="secondary">
            {isLoading ? 'Checking...' : health?.status || 'Unknown'}
          </Text>
        </Space>
        {health && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            v{health.version}
          </Text>
        )}
      </Space>
    </AntHeader>
  )
}

export default Header
