import { Card, Typography, Space, Tag } from 'antd'
import { DatabaseOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { KnowledgeBaseSummary } from '../api/types'
import dayjs from 'dayjs'

const { Text, Paragraph } = Typography

interface KbCardProps {
  knowledgeBase: KnowledgeBaseSummary
}

function KbCard({ knowledgeBase }: KbCardProps) {
  const navigate = useNavigate()

  return (
    <Card
      hoverable
      onClick={() => navigate(`/knowledge-bases/${knowledgeBase.id}`)}
      style={{ height: '100%' }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        <Space>
          <DatabaseOutlined style={{ fontSize: 20, color: '#1677ff' }} />
          <Text strong style={{ fontSize: 16 }}>
            {knowledgeBase.name}
          </Text>
        </Space>

        <Paragraph
          type="secondary"
          ellipsis={{ rows: 2 }}
          style={{ marginBottom: 8 }}
        >
          {knowledgeBase.description || 'No description'}
        </Paragraph>

        <Space wrap>
          <Tag>{knowledgeBase.version_count} versions</Tag>
          {knowledgeBase.latest_version && (
            <Tag color="blue">{knowledgeBase.latest_version}</Tag>
          )}
        </Space>

        <Text type="secondary" style={{ fontSize: 12 }}>
          Created {dayjs(knowledgeBase.created_at).format('YYYY-MM-DD')}
        </Text>
      </Space>
    </Card>
  )
}

export default KbCard
