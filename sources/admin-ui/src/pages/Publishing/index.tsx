import { useState } from 'react'
import {
  Typography,
  Tabs,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Tag,
  App,
  Alert,
  Popconfirm,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ExperimentOutlined,
  StarFilled,
} from '@ant-design/icons'
import {
  useEnvironments,
  useCreateEnvironment,
  useUpdateEnvironment,
  useDeleteEnvironment,
  useTestEnvironment,
} from '../../hooks/useEnvironments'
import { useTasks } from '../../hooks/useTasks'
import TaskStatusBadge from '../../components/TaskStatusBadge'
import { formatRelativeTime } from '../../utils/format'
import type { ColumnsType } from 'antd/es/table'
import { EnvironmentSummary, Environment, EnvironmentCreate, EnvironmentUpdate } from '../../api/environments'
import { TaskSummary } from '../../api/types'

const { Title, Text } = Typography
const { TextArea } = Input

function Publishing() {
  const { message } = App.useApp()
  const [activeTab, setActiveTab] = useState('environments')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingEnv, setEditingEnv] = useState<Environment | null>(null)
  const [testResult, setTestResult] = useState<{ envId: string; success: boolean; message: string } | null>(null)
  const [form] = Form.useForm()

  const { data: environments, isLoading: envLoading } = useEnvironments()
  const { data: publishTasks, isLoading: tasksLoading } = useTasks({
    task_type: 'publishing',
    page_size: 10,
  })

  const createEnv = useCreateEnvironment()
  const updateEnv = useUpdateEnvironment()
  const deleteEnv = useDeleteEnvironment()
  const testEnv = useTestEnvironment()

  const handleOpenCreate = () => {
    setEditingEnv(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleOpenEdit = (env: EnvironmentSummary) => {
    // Would need to fetch full environment details
    form.setFieldsValue({
      name: env.name,
      environment_type: env.environment_type,
      is_default: env.is_default,
    })
    setEditingEnv(env as unknown as Environment)
    setModalOpen(true)
  }

  const handleSubmit = async (values: EnvironmentCreate | EnvironmentUpdate) => {
    try {
      if (editingEnv) {
        await updateEnv.mutateAsync({ envId: editingEnv.id, data: values as EnvironmentUpdate })
        message.success('Environment updated')
      } else {
        await createEnv.mutateAsync(values as EnvironmentCreate)
        message.success('Environment created')
      }
      setModalOpen(false)
      form.resetFields()
    } catch {
      message.error('Failed to save environment')
    }
  }

  const handleDelete = async (envId: string) => {
    try {
      await deleteEnv.mutateAsync(envId)
      message.success('Environment deleted')
    } catch {
      message.error('Failed to delete environment')
    }
  }

  const handleTest = async (envId: string) => {
    setTestResult(null)
    try {
      const result = await testEnv.mutateAsync(envId)
      setTestResult({ envId, success: result.success, message: result.message })
      if (result.success) {
        message.success('Connection test successful')
      } else {
        message.error(result.message)
      }
    } catch {
      setTestResult({ envId, success: false, message: 'Test failed' })
      message.error('Connection test failed')
    }
  }

  const envColumns: ColumnsType<EnvironmentSummary> = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record) => (
        <Space>
          {record.is_default && <StarFilled style={{ color: '#faad14' }} />}
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'environment_type',
      key: 'environment_type',
      width: 120,
      render: (type: string) => {
        const colors: Record<string, string> = {
          development: 'blue',
          staging: 'orange',
          production: 'green',
        }
        return <Tag color={colors[type] || 'default'}>{type}</Tag>
      },
    },
    {
      title: 'Default',
      dataIndex: 'is_default',
      key: 'is_default',
      width: 80,
      render: (isDefault: boolean) => isDefault ? <Tag color="gold">Default</Tag> : null,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => formatRelativeTime(date),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<ExperimentOutlined />}
            onClick={() => handleTest(record.id)}
            loading={testEnv.isPending && testResult?.envId === record.id}
          >
            Test
          </Button>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleOpenEdit(record)}
          >
            Edit
          </Button>
          <Popconfirm
            title="Delete environment?"
            description="This action cannot be undone."
            onConfirm={() => handleDelete(record.id)}
            okText="Delete"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              disabled={record.is_default}
            >
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const taskColumns: ColumnsType<TaskSummary> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      render: (id: string) => (
        <Text copyable style={{ fontFamily: 'monospace', fontSize: 12 }}>
          {id.slice(0, 8)}...
        </Text>
      ),
    },
    {
      title: 'Knowledge Base',
      dataIndex: 'knowledge_base_name',
      key: 'knowledge_base_name',
    },
    {
      title: 'Version',
      dataIndex: 'version_tag',
      key: 'version_tag',
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
  ]

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>
        Publishing
      </Title>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'environments',
            label: 'Environments',
            children: (
              <div>
                <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">
                    Manage publishing environments for deploying knowledge bases
                  </Text>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={handleOpenCreate}
                  >
                    Create Environment
                  </Button>
                </div>

                {testResult && (
                  <Alert
                    type={testResult.success ? 'success' : 'error'}
                    message={testResult.success ? 'Connection Test Passed' : 'Connection Test Failed'}
                    description={testResult.message}
                    showIcon
                    closable
                    onClose={() => setTestResult(null)}
                    style={{ marginBottom: 16 }}
                  />
                )}

                <Table
                  columns={envColumns}
                  dataSource={environments?.data || []}
                  rowKey="id"
                  loading={envLoading}
                  pagination={{
                    total: environments?.meta?.total_items || 0,
                    showSizeChanger: false,
                  }}
                />
              </div>
            ),
          },
          {
            key: 'history',
            label: 'Publish History',
            children: (
              <div>
                <Text type="secondary" style={{ marginBottom: 16, display: 'block' }}>
                  Recent publishing tasks
                </Text>
                <Table
                  columns={taskColumns}
                  dataSource={publishTasks?.data || []}
                  rowKey="id"
                  loading={tasksLoading}
                  pagination={false}
                  onRow={(record) => ({
                    onClick: () => window.location.href = `/tasks/${record.id}`,
                    style: { cursor: 'pointer' },
                  })}
                />
                <div style={{ marginTop: 16, textAlign: 'center' }}>
                  <a href="/tasks?task_type=publishing">View all publishing tasks</a>
                </div>
              </div>
            ),
          },
        ]}
      />

      <Modal
        title={editingEnv ? 'Edit Environment' : 'Create Environment'}
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false)
          form.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            environment_type: 'development',
            is_default: false,
          }}
        >
          <Form.Item
            name="name"
            label="Name"
            rules={[{ required: true, message: 'Please enter environment name' }]}
          >
            <Input placeholder="e.g., Production Qdrant" />
          </Form.Item>

          <Form.Item
            name="environment_type"
            label="Environment Type"
            rules={[{ required: true }]}
          >
            <Select>
              <Select.Option value="development">Development</Select.Option>
              <Select.Option value="staging">Staging</Select.Option>
              <Select.Option value="production">Production</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="Description"
          >
            <TextArea rows={3} placeholder="Environment description" />
          </Form.Item>

          <Form.Item
            name="is_default"
            label="Default Environment"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={createEnv.isPending || updateEnv.isPending}
              >
                {editingEnv ? 'Update' : 'Create'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Publishing
