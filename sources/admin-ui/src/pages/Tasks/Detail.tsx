import { useState } from 'react'
import {
  Typography,
  Button,
  Card,
  Descriptions,
  Progress,
  Table,
  Tag,
  Space,
  Spin,
  App,
  Collapse,
} from 'antd'
import {
  ArrowLeftOutlined,
  StopOutlined,
  ReloadOutlined,
  RetweetOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import { useTask, useTaskResult, useCancelTask, useRetryTask } from '../../hooks/useTasks'
import { useTaskWebSocket } from '../../hooks/useTaskWebSocket'
import TaskStatusBadge from '../../components/TaskStatusBadge'
import { formatDateTime, formatDuration, formatPercent } from '../../utils/format'
import { TaskProgressUpdate } from '../../api/types'

const { Title, Text } = Typography

function TaskDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { message } = App.useApp()

  const { data: task, isLoading, refetch } = useTask(id!)
  const { data: result } = useTaskResult(
    id!,
    task?.status === 'completed' || task?.status === 'failed'
  )
  const cancelTask = useCancelTask()
  const retryTask = useRetryTask()

  const [wsProgress, setWsProgress] = useState<TaskProgressUpdate | null>(null)

  // WebSocket for real-time updates
  useTaskWebSocket({
    taskId: id!,
    onUpdate: (update) => {
      setWsProgress(update)
      if (update.status === 'completed' || update.status === 'failed') {
        refetch()
      }
    },
    autoConnect: task?.status === 'running' || task?.status === 'pending',
  })

  const handleCancel = async () => {
    try {
      await cancelTask.mutateAsync({ taskId: id! })
      message.success('Task cancelled')
      refetch()
    } catch {
      message.error('Failed to cancel task')
    }
  }

  const handleRetry = async () => {
    try {
      const newTask = await retryTask.mutateAsync({ taskId: id! })
      message.success('Task retry created')
      navigate(`/tasks/${newTask.id}`)
    } catch {
      message.error('Failed to retry task')
    }
  }

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!task) {
    return <div>Task not found</div>
  }

  const isRunning = task.status === 'running'
  const isPending = task.status === 'pending'
  const canCancel = isRunning || isPending
  const canRetry = task.status === 'failed' || task.status === 'cancelled'

  // Calculate progress from WebSocket or result
  const progress = wsProgress?.progress ??
    (result ? (result.succeeded_count / result.total_items) * 100 : 0)

  return (
    <div>
      <Space style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/tasks')}>
          Back
        </Button>
        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
          Refresh
        </Button>
        {canCancel && (
          <Button
            danger
            icon={<StopOutlined />}
            onClick={handleCancel}
            loading={cancelTask.isPending}
          >
            Cancel
          </Button>
        )}
        {canRetry && (
          <Button
            type="primary"
            icon={<RetweetOutlined />}
            onClick={handleRetry}
            loading={retryTask.isPending}
          >
            Retry
          </Button>
        )}
      </Space>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Space>
          <Title level={4} style={{ margin: 0 }}>
            Task Details
          </Title>
          <TaskStatusBadge status={task.status} />
        </Space>
      </div>

      {/* Progress Section */}
      {(isRunning || isPending) && (
        <Card style={{ marginBottom: 24 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text strong>Progress</Text>
            <Progress
              percent={Math.round(progress)}
              status={isRunning ? 'active' : 'normal'}
            />
            {wsProgress?.message && (
              <Text type="secondary">{wsProgress.message}</Text>
            )}
            {wsProgress?.current_step && (
              <Text type="secondary">
                Current step: {wsProgress.current_step}
              </Text>
            )}
            {wsProgress?.items_processed !== undefined && wsProgress?.total_items !== undefined && (
              <Text type="secondary">
                Processed {wsProgress.items_processed} of {wsProgress.total_items} items
              </Text>
            )}
          </Space>
        </Card>
      )}

      {/* Task Info */}
      <Card style={{ marginBottom: 24 }}>
        <Descriptions column={2}>
          <Descriptions.Item label="ID">
            <Text copyable style={{ fontFamily: 'monospace' }}>
              {task.id}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="Type">
            <Tag color="blue">{task.task_type}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Knowledge Base">
            {task.knowledge_base_name || task.knowledge_base_id}
          </Descriptions.Item>
          <Descriptions.Item label="Version">
            {task.version_tag || task.knowledge_base_version_id}
          </Descriptions.Item>
          <Descriptions.Item label="Priority">{task.priority}</Descriptions.Item>
          <Descriptions.Item label="Retries">
            {task.retry_count} / {task.max_retries}
          </Descriptions.Item>
          <Descriptions.Item label="Created">
            {formatDateTime(task.created_at)}
          </Descriptions.Item>
          <Descriptions.Item label="Started">
            {task.started_at ? formatDateTime(task.started_at) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Completed">
            {task.completed_at ? formatDateTime(task.completed_at) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Duration">
            {task.duration_seconds ? formatDuration(task.duration_seconds) : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Result Section */}
      {result && (
        <>
          <Card title="Result Statistics" style={{ marginBottom: 24 }}>
            <Descriptions column={3}>
              <Descriptions.Item label="Total Items">
                {result.total_items}
              </Descriptions.Item>
              <Descriptions.Item label="Succeeded">
                <Text type="success">{result.succeeded_count}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Failed">
                <Text type="danger">{result.failed_count}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Skipped">
                {result.skipped_count}
              </Descriptions.Item>
              <Descriptions.Item label="Success Rate">
                {formatPercent(result.success_rate)}
              </Descriptions.Item>
              <Descriptions.Item label="Duration">
                {formatDuration(result.duration_seconds)}
              </Descriptions.Item>
            </Descriptions>

            {/* Type-specific stats */}
            {result.index_records_count > 0 && (
              <Descriptions column={3} style={{ marginTop: 16 }}>
                <Descriptions.Item label="Index Records Created">
                  {result.index_records_count}
                </Descriptions.Item>
              </Descriptions>
            )}
            {(result.new_files_count > 0 || result.updated_files_count > 0) && (
              <Descriptions column={3} style={{ marginTop: 16 }}>
                <Descriptions.Item label="New Files">
                  {result.new_files_count}
                </Descriptions.Item>
                <Descriptions.Item label="Updated Files">
                  {result.updated_files_count}
                </Descriptions.Item>
                <Descriptions.Item label="Unchanged Files">
                  {result.unchanged_files_count}
                </Descriptions.Item>
              </Descriptions>
            )}
            {result.target_collection && (
              <Descriptions column={2} style={{ marginTop: 16 }}>
                <Descriptions.Item label="Target Collection">
                  {result.target_collection}
                </Descriptions.Item>
                <Descriptions.Item label="Alias Applied">
                  {result.alias_applied || '-'}
                </Descriptions.Item>
              </Descriptions>
            )}
          </Card>

          {/* Step Stats */}
          {Object.keys(result.step_stats).length > 0 && (
            <Card title="Step Statistics" style={{ marginBottom: 24 }}>
              <Table
                dataSource={Object.values(result.step_stats)}
                rowKey="step_type"
                pagination={false}
                columns={[
                  { title: 'Step', dataIndex: 'step_type', key: 'step_type' },
                  { title: 'Input', dataIndex: 'input_count', key: 'input_count' },
                  { title: 'Output', dataIndex: 'output_count', key: 'output_count' },
                  {
                    title: 'Duration',
                    dataIndex: 'duration_seconds',
                    key: 'duration_seconds',
                    render: (s: number) => formatDuration(s),
                  },
                  { title: 'Errors', dataIndex: 'errors_count', key: 'errors_count' },
                  {
                    title: 'Success Rate',
                    dataIndex: 'success_rate',
                    key: 'success_rate',
                    render: (r: number) => formatPercent(r),
                  },
                ]}
              />
            </Card>
          )}

          {/* Errors */}
          {result.errors.length > 0 && (
            <Card title={`Errors (${result.errors.length})`}>
              <Collapse>
                {result.errors.map((error, index) => (
                  <Collapse.Panel
                    key={index}
                    header={
                      <Space>
                        <Tag color={error.recoverable ? 'orange' : 'red'}>
                          {error.error_type}
                        </Tag>
                        <Text>{error.item_name}</Text>
                      </Space>
                    }
                  >
                    <Descriptions column={1} size="small">
                      <Descriptions.Item label="Item ID">
                        {error.item_id}
                      </Descriptions.Item>
                      <Descriptions.Item label="Step">
                        {error.step}
                      </Descriptions.Item>
                      <Descriptions.Item label="Message">
                        {error.error_message}
                      </Descriptions.Item>
                      {error.stacktrace && (
                        <Descriptions.Item label="Stacktrace">
                          <pre style={{ fontSize: 12, overflow: 'auto', maxHeight: 200 }}>
                            {error.stacktrace}
                          </pre>
                        </Descriptions.Item>
                      )}
                    </Descriptions>
                  </Collapse.Panel>
                ))}
              </Collapse>
            </Card>
          )}
        </>
      )}
    </div>
  )
}

export default TaskDetail
