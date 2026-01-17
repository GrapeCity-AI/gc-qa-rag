import { Typography, Card, Descriptions, Space, Tag, Row, Col, Divider, Spin } from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  RobotOutlined,
  DatabaseOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useHealth } from '../../hooks/useTasks'
import { useSystemConfig } from '../../hooks/useConfig'
import { formatDateTime } from '../../utils/format'

const { Title, Text } = Typography

function Settings() {
  const { data: health, isLoading: healthLoading } = useHealth()
  const { data: config, isLoading: configLoading } = useSystemConfig()

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>
        Settings
      </Title>

      {/* System Status */}
      <Card title="System Status" style={{ marginBottom: 24 }}>
        <Spin spinning={healthLoading}>
          <Descriptions column={2}>
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
        </Spin>

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

      {/* System Configuration */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={8}>
          <Card
            title={
              <Space>
                <RobotOutlined />
                <span>LLM Configuration</span>
              </Space>
            }
            loading={configLoading}
          >
            {config && (
              <Descriptions column={1} size="small">
                <Descriptions.Item label="Provider">
                  <Tag color="blue">{config.llm_provider}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Model">
                  <Text code>{config.llm_model}</Text>
                </Descriptions.Item>
              </Descriptions>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card
            title={
              <Space>
                <DatabaseOutlined />
                <span>Storage Configuration</span>
              </Space>
            }
            loading={configLoading}
          >
            {config && (
              <Descriptions column={1} size="small">
                <Descriptions.Item label="Storage Type">
                  <Tag color="green">{config.storage_type}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Vector DB">
                  <Tag color="purple">{config.vector_db_type}</Tag>
                </Descriptions.Item>
              </Descriptions>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card
            title={
              <Space>
                <SettingOutlined />
                <span>Pipeline Configuration</span>
              </Space>
            }
            loading={configLoading}
          >
            {config && (
              <Descriptions column={1} size="small">
                <Descriptions.Item label="Max Concurrent Tasks">
                  {config.max_concurrent_tasks}
                </Descriptions.Item>
                <Descriptions.Item label="Default Chunk Size">
                  {config.default_chunk_size}
                </Descriptions.Item>
                <Descriptions.Item label="Chunk Overlap">
                  {config.default_chunk_overlap}
                </Descriptions.Item>
              </Descriptions>
            )}
          </Card>
        </Col>
      </Row>

      {/* Feature Flags */}
      {config?.features && Object.keys(config.features).length > 0 && (
        <Card title="Feature Flags" style={{ marginBottom: 24 }}>
          <Space wrap>
            {Object.entries(config.features).map(([feature, enabled]) => (
              <Tag
                key={feature}
                icon={enabled ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                color={enabled ? 'success' : 'default'}
              >
                {feature.replace(/_/g, ' ')}
              </Tag>
            ))}
          </Space>
        </Card>
      )}

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
