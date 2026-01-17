import { useState } from 'react'
import { Typography, Card, Row, Col, Space, Tag, Button, Spin } from 'antd'
import {
  GlobalOutlined,
  FolderOutlined,
  ApiOutlined,
  ExperimentOutlined,
} from '@ant-design/icons'
import { useConnectors } from '../../hooks/useConnectors'
import TestDialog from './TestDialog'
import { ConnectorType } from '../../api/types'

const { Title, Text, Paragraph } = Typography

const connectorIcons: Record<string, React.ReactNode> = {
  sitemap: <GlobalOutlined style={{ fontSize: 32 }} />,
  filesystem: <FolderOutlined style={{ fontSize: 32 }} />,
  forum_api: <ApiOutlined style={{ fontSize: 32 }} />,
}

const connectorColors: Record<string, string> = {
  sitemap: '#1890ff',
  filesystem: '#52c41a',
  forum_api: '#722ed1',
}

function SourceList() {
  const { data: connectors, isLoading } = useConnectors()
  const [testDialogOpen, setTestDialogOpen] = useState(false)
  const [selectedConnector, setSelectedConnector] = useState<ConnectorType | null>(null)

  const handleTest = (connector: ConnectorType) => {
    setSelectedConnector(connector)
    setTestDialogOpen(true)
  }

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={4} style={{ marginBottom: 8 }}>
          Data Sources
        </Title>
        <Text type="secondary">
          Available connectors for ingesting data into knowledge bases
        </Text>
      </div>

      <Row gutter={[16, 16]}>
        {connectors?.map((connector) => (
          <Col xs={24} sm={12} lg={8} key={connector.type}>
            <Card
              hoverable
              style={{ height: '100%' }}
              actions={[
                <Button
                  key="test"
                  type="link"
                  icon={<ExperimentOutlined />}
                  onClick={() => handleTest(connector)}
                >
                  Test Connection
                </Button>,
              ]}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space>
                  <div
                    style={{
                      width: 48,
                      height: 48,
                      borderRadius: 8,
                      backgroundColor: `${connectorColors[connector.type]}15`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: connectorColors[connector.type],
                    }}
                  >
                    {connectorIcons[connector.type] || <ApiOutlined style={{ fontSize: 32 }} />}
                  </div>
                  <div>
                    <Text strong style={{ fontSize: 16 }}>{connector.name}</Text>
                    <br />
                    <Tag color={connectorColors[connector.type]}>{connector.type}</Tag>
                  </div>
                </Space>
                <Paragraph
                  type="secondary"
                  ellipsis={{ rows: 2 }}
                  style={{ marginBottom: 0, marginTop: 12 }}
                >
                  {connector.description}
                </Paragraph>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>

      <Card title="Ingestion History" style={{ marginTop: 24 }}>
        <Text type="secondary">
          View ingestion task history in the{' '}
          <a href="/tasks?task_type=ingestion">Tasks</a> page with type filter set to "Ingestion"
        </Text>
      </Card>

      <TestDialog
        open={testDialogOpen}
        connector={selectedConnector}
        onClose={() => {
          setTestDialogOpen(false)
          setSelectedConnector(null)
        }}
      />
    </div>
  )
}

export default SourceList
