import { useState } from 'react'
import { Typography, Table, Select, Space, Tag } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useTasks } from '../../hooks/useTasks'
import TaskStatusBadge from '../../components/TaskStatusBadge'
import { formatRelativeTime } from '../../utils/format'
import type { ColumnsType } from 'antd/es/table'
import { TaskSummary } from '../../api/types'

const { Title } = Typography

function TaskList() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState<string | undefined>(undefined)
  const [taskType, setTaskType] = useState<string | undefined>(undefined)
  const pageSize = 20

  const { data, isLoading } = useTasks({
    page,
    page_size: pageSize,
    status,
    task_type: taskType,
  })

  const columns: ColumnsType<TaskSummary> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      render: (id: string) => (
        <span style={{ fontFamily: 'monospace', fontSize: 12 }}>
          {id.slice(0, 8)}...
        </span>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 120,
      render: (type: string) => {
        const colors: Record<string, string> = {
          ingestion: 'blue',
          indexing: 'purple',
          publishing: 'green',
        }
        return (
          <Tag color={colors[type] || 'default'}>
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </Tag>
        )
      },
    },
    {
      title: 'Knowledge Base',
      dataIndex: 'knowledge_base_name',
      key: 'knowledge_base_name',
      ellipsis: true,
      render: (name: string | null) => name || '-',
    },
    {
      title: 'Version',
      dataIndex: 'version_tag',
      key: 'version_tag',
      width: 100,
      render: (tag: string | null) => tag ? <Tag>{tag}</Tag> : '-',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 130,
      render: (status: string) => <TaskStatusBadge status={status} />,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => formatRelativeTime(date),
    },
    {
      title: 'Completed',
      dataIndex: 'completed_at',
      key: 'completed_at',
      width: 150,
      render: (date: string | null) => date ? formatRelativeTime(date) : '-',
    },
  ]

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>
        Tasks
      </Title>

      <Space style={{ marginBottom: 16 }}>
        <Select
          style={{ width: 150 }}
          placeholder="Filter by status"
          allowClear
          value={status}
          onChange={setStatus}
        >
          <Select.Option value="pending">Pending</Select.Option>
          <Select.Option value="running">Running</Select.Option>
          <Select.Option value="completed">Completed</Select.Option>
          <Select.Option value="failed">Failed</Select.Option>
          <Select.Option value="cancelled">Cancelled</Select.Option>
        </Select>
        <Select
          style={{ width: 150 }}
          placeholder="Filter by type"
          allowClear
          value={taskType}
          onChange={setTaskType}
        >
          <Select.Option value="ingestion">Ingestion</Select.Option>
          <Select.Option value="indexing">Indexing</Select.Option>
          <Select.Option value="publishing">Publishing</Select.Option>
        </Select>
      </Space>

      <Table
        columns={columns}
        dataSource={data?.data || []}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: page,
          pageSize,
          total: data?.meta?.total_items || 0,
          onChange: setPage,
          showSizeChanger: false,
          showQuickJumper: true,
        }}
        onRow={(record) => ({
          onClick: () => navigate(`/tasks/${record.id}`),
          style: { cursor: 'pointer' },
        })}
      />
    </div>
  )
}

export default TaskList
