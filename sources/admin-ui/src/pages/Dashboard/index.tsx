import { Row, Col, Card, Statistic, Table, Typography, Space, Spin } from 'antd'
import {
  DatabaseOutlined,
  BranchesOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useStats, useTasks } from '../../hooks/useTasks'
import { useKnowledgeBases } from '../../hooks/useKnowledgeBases'
import TaskStatusBadge from '../../components/TaskStatusBadge'
import { formatRelativeTime } from '../../utils/format'
import type { ColumnsType } from 'antd/es/table'
import { TaskSummary } from '../../api/types'

const { Title } = Typography

function Dashboard() {
  const navigate = useNavigate()
  const { data: stats, isLoading: statsLoading } = useStats()
  const { data: recentTasks, isLoading: tasksLoading } = useTasks({ page_size: 5 })
  const { data: knowledgeBases, isLoading: kbLoading } = useKnowledgeBases({ page_size: 5 })

  const taskColumns: ColumnsType<TaskSummary> = [
    {
      title: 'Type',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 100,
      render: (type: string) => type.charAt(0).toUpperCase() + type.slice(1),
    },
    {
      title: 'Knowledge Base',
      dataIndex: 'knowledge_base_name',
      key: 'knowledge_base_name',
      ellipsis: true,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => <TaskStatusBadge status={status} />,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => formatRelativeTime(date),
    },
  ]

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>
        Dashboard
      </Title>

      {/* Stats Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Knowledge Bases"
              value={stats?.knowledge_bases || 0}
              prefix={<DatabaseOutlined />}
              loading={statsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Versions"
              value={stats?.versions || 0}
              prefix={<BranchesOutlined />}
              loading={statsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Pending Tasks"
              value={stats?.pending_tasks || 0}
              prefix={<ClockCircleOutlined />}
              loading={statsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Running Tasks"
              value={stats?.running_tasks || 0}
              prefix={<SyncOutlined spin={!!stats?.running_tasks} />}
              loading={statsLoading}
            />
          </Card>
        </Col>
      </Row>

      {/* Task Status */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12}>
          <Card>
            <Statistic
              title="Completed Tasks (24h)"
              value={stats?.completed_tasks || 0}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
              loading={statsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card>
            <Statistic
              title="Failed Tasks (24h)"
              value={stats?.failed_tasks || 0}
              valueStyle={{ color: stats?.failed_tasks ? '#ff4d4f' : undefined }}
              prefix={<CloseCircleOutlined />}
              loading={statsLoading}
            />
          </Card>
        </Col>
      </Row>

      {/* Recent Tasks */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card
            title="Recent Tasks"
            extra={
              <a onClick={() => navigate('/tasks')}>View all</a>
            }
          >
            <Table
              columns={taskColumns}
              dataSource={recentTasks?.data || []}
              rowKey="id"
              pagination={false}
              loading={tasksLoading}
              size="small"
              onRow={(record) => ({
                onClick: () => navigate(`/tasks/${record.id}`),
                style: { cursor: 'pointer' },
              })}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
