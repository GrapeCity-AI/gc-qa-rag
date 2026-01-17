import { Typography, Card, Descriptions, Space, Tag, Switch, Divider } from 'antd'
import { useHealth } from '../../hooks/useTasks'
import { formatDateTime } from '../../utils/format'

const { Title, Text } = Typography

function Settings() {
  const { data: health, isLoading } = useHealth()

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>
        Settings
      </Title>

      {/* System Status */}
      <Card title="System Status" style={{ marginBottom: 24 }}>
        <Descriptions column={2} loading={isLoading}>
          <Descriptions.Item label="Status">
            <Tag color={health?.status === 'healthy' ? 'green' : 'red'}>
              {health?.status || 'Unknown'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Version">
            {health?.version || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Last Check">
            {health?.timestamp ? formatDateTime(health.timestamp) : '-'}
          </Descriptions.Item>
        </Descriptions>

        {health?.components && (
          <>
            <Divider orientation="left" plain>
              Components
            </Divider>
            <Space wrap>
              {Object.entries(health.components).map(([name, status]) => (
                <Tag key={name} color={status === 'healthy' ? 'green' : 'red'}>
                  {name}: {status}
                </Tag>
              ))}
            </Space>
          </>
        )}
      </Card>

      {/* API Information */}
      <Card title="API Configuration" style={{ marginBottom: 24 }}>
        <Descriptions column={1}>
          <Descriptions.Item label="API Base URL">
            <Text copyable>/api/v1</Text>
          </Descriptions.Item>
          <Descriptions.Item label="WebSocket URL">
            <Text copyable>/api/v1/tasks/ws/tasks/:taskId</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Documentation">
            <a href="/api/v1/docs" target="_blank" rel="noopener noreferrer">
              OpenAPI Docs (Swagger)
            </a>
          </Descriptions.Item>
          <Descriptions.Item label="ReDoc">
            <a href="/api/v1/redoc" target="_blank" rel="noopener noreferrer">
              ReDoc Documentation
            </a>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* About */}
      <Card title="About">
        <Descriptions column={1}>
          <Descriptions.Item label="Application">
            AI Knowledge Service - Admin Console
          </Descriptions.Item>
          <Descriptions.Item label="Description">
            Management interface for the AI Knowledge Service ETL system.
            Create and manage knowledge bases, trigger builds, and monitor tasks.
          </Descriptions.Item>
          <Descriptions.Item label="Tech Stack">
            <Space wrap>
              <Tag>React 18</Tag>
              <Tag>TypeScript</Tag>
              <Tag>Ant Design 5</Tag>
              <Tag>TanStack Query</Tag>
              <Tag>Zustand</Tag>
              <Tag>Vite</Tag>
            </Space>
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  )
}

export default Settings
