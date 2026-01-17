import { useState } from 'react'
import {
  Typography,
  Descriptions,
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Tabs,
  Tag,
  Spin,
  App,
  Popconfirm,
  Radio,
} from 'antd'
import {
  ArrowLeftOutlined,
  PlusOutlined,
  PlayCircleOutlined,
  CloudUploadOutlined,
  DeleteOutlined,
  FileSearchOutlined,
  UnorderedListOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import { useKnowledgeBase, useDeleteKnowledgeBase } from '../../hooks/useKnowledgeBases'
import { useVersions, useCreateVersion, useBuildVersion, usePublishVersion, useIngestVersion } from '../../hooks/useVersions'
import FileBrowser from './components/FileBrowser'
import { formatDateTime, formatRelativeTime } from '../../utils/format'
import type { ColumnsType } from 'antd/es/table'
import { VersionSummary } from '../../api/types'

const { Title, Text } = Typography

function KnowledgeBaseDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { message } = App.useApp()

  const { data: kb, isLoading } = useKnowledgeBase(id!)
  const { data: versions, isLoading: versionsLoading } = useVersions(id!)
  const deleteKb = useDeleteKnowledgeBase()
  const createVersion = useCreateVersion(id!)
  const buildVersion = useBuildVersion('')
  const publishVersion = usePublishVersion('')
  const ingestVersion = useIngestVersion('')

  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [buildModalOpen, setBuildModalOpen] = useState(false)
  const [publishModalOpen, setPublishModalOpen] = useState(false)
  const [ingestModalOpen, setIngestModalOpen] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null)
  const [fileBrowserVersionId, setFileBrowserVersionId] = useState<string | null>(null)
  const [form] = Form.useForm()

  const handleDelete = async () => {
    try {
      await deleteKb.mutateAsync(id!)
      message.success('Knowledge base deleted')
      navigate('/knowledge-bases')
    } catch {
      message.error('Failed to delete knowledge base')
    }
  }

  const handleCreateVersion = async (values: { version_tag: string }) => {
    try {
      await createVersion.mutateAsync(values)
      message.success('Version created')
      setCreateModalOpen(false)
      form.resetFields()
    } catch {
      message.error('Failed to create version')
    }
  }

  const handleBuild = async (values: { build_type: string }) => {
    if (!selectedVersion) return
    try {
      const result = await buildVersion.mutateAsync({
        build_type: values.build_type as 'full' | 'incremental',
      })
      message.success('Build task created')
      setBuildModalOpen(false)
      navigate(`/tasks/${result.id}`)
    } catch {
      message.error('Failed to trigger build')
    }
  }

  const handlePublish = async (values: { target_environment_id: string; alias_name?: string }) => {
    if (!selectedVersion) return
    try {
      const result = await publishVersion.mutateAsync({
        target_environment_id: values.target_environment_id,
        alias_name: values.alias_name,
      })
      message.success('Publish task created')
      setPublishModalOpen(false)
      navigate(`/tasks/${result.id}`)
    } catch {
      message.error('Failed to trigger publish')
    }
  }

  const handleIngest = async (values: { source_type: string; source_config: string; incremental: boolean }) => {
    if (!selectedVersion) return
    try {
      // Parse source_config as JSON
      let sourceConfig = {}
      try {
        sourceConfig = values.source_config ? JSON.parse(values.source_config) : {}
      } catch {
        message.error('Invalid source config JSON')
        return
      }

      const result = await ingestVersion.mutateAsync({
        source_type: values.source_type,
        source_config: sourceConfig,
        incremental: values.incremental,
      })
      message.success('Ingest task created')
      setIngestModalOpen(false)
      form.resetFields()
      navigate(`/tasks/${result.id}`)
    } catch {
      message.error('Failed to trigger ingest')
    }
  }

  const versionColumns: ColumnsType<VersionSummary> = [
    {
      title: 'Version',
      dataIndex: 'version_tag',
      key: 'version_tag',
      render: (tag: string) => <Tag color="blue">{tag}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors: Record<string, string> = {
          draft: 'default',
          building: 'processing',
          ready: 'success',
          published: 'green',
          archived: 'default',
        }
        return <Tag color={colors[status] || 'default'}>{status}</Tag>
      },
    },
    {
      title: 'Files',
      dataIndex: 'file_count',
      key: 'file_count',
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => formatRelativeTime(date),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => {
              setSelectedVersion(record.id)
              setIngestModalOpen(true)
            }}
            disabled={record.status === 'building' || record.status === 'published'}
          >
            Ingest
          </Button>
          <Button
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => {
              setSelectedVersion(record.id)
              setBuildModalOpen(true)
            }}
            disabled={record.status === 'building'}
          >
            Build
          </Button>
          <Button
            size="small"
            icon={<CloudUploadOutlined />}
            onClick={() => {
              setSelectedVersion(record.id)
              setPublishModalOpen(true)
            }}
            disabled={record.status !== 'ready'}
          >
            Publish
          </Button>
        </Space>
      ),
    },
  ]

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!kb) {
    return <div>Knowledge base not found</div>
  }

  return (
    <div>
      <Space style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/knowledge-bases')}>
          Back
        </Button>
      </Space>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0 }}>
          {kb.name}
        </Title>
        <Popconfirm
          title="Delete knowledge base"
          description="Are you sure? This action cannot be undone."
          onConfirm={handleDelete}
          okText="Delete"
          okType="danger"
        >
          <Button danger icon={<DeleteOutlined />}>
            Delete
          </Button>
        </Popconfirm>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <Descriptions column={2}>
          <Descriptions.Item label="ID">{kb.id}</Descriptions.Item>
          <Descriptions.Item label="Versions">{kb.version_count}</Descriptions.Item>
          <Descriptions.Item label="Description" span={2}>
            {kb.description || 'No description'}
          </Descriptions.Item>
          <Descriptions.Item label="Created">{formatDateTime(kb.created_at)}</Descriptions.Item>
          <Descriptions.Item label="Updated">{formatDateTime(kb.updated_at)}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Tabs
        defaultActiveKey="versions"
        items={[
          {
            key: 'versions',
            label: (
              <span>
                <UnorderedListOutlined />
                Versions
              </span>
            ),
            children: (
              <Card
                extra={
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setCreateModalOpen(true)}
                  >
                    Create Version
                  </Button>
                }
              >
                <Table
                  columns={versionColumns}
                  dataSource={versions?.data || []}
                  rowKey="id"
                  loading={versionsLoading}
                  pagination={false}
                />
              </Card>
            ),
          },
          {
            key: 'files',
            label: (
              <span>
                <FileSearchOutlined />
                Files
              </span>
            ),
            children: (
              <Card>
                <div style={{ marginBottom: 16 }}>
                  <Space align="center">
                    <Text>Select version:</Text>
                    <Radio.Group
                      value={fileBrowserVersionId}
                      onChange={(e) => setFileBrowserVersionId(e.target.value)}
                      optionType="button"
                      buttonStyle="solid"
                    >
                      {versions?.data.map((v) => (
                        <Radio.Button key={v.id} value={v.id}>
                          {v.version_tag} ({v.file_count} files)
                        </Radio.Button>
                      ))}
                    </Radio.Group>
                  </Space>
                </div>
                {fileBrowserVersionId ? (
                  <FileBrowser versionId={fileBrowserVersionId} />
                ) : (
                  <div style={{ textAlign: 'center', padding: 48, color: '#999' }}>
                    <FileSearchOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                    <div>Select a version above to browse files</div>
                  </div>
                )}
              </Card>
            ),
          },
        ]}
      />

      {/* Create Version Modal */}
      <Modal
        title="Create Version"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createVersion.isPending}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateVersion}>
          <Form.Item
            name="version_tag"
            label="Version Tag"
            rules={[{ required: true, message: 'Please enter a version tag' }]}
          >
            <Input placeholder="e.g., v1.0.0" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Build Modal */}
      <Modal
        title="Trigger Build"
        open={buildModalOpen}
        onCancel={() => setBuildModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={buildVersion.isPending}
      >
        <Form form={form} layout="vertical" onFinish={handleBuild} initialValues={{ build_type: 'full' }}>
          <Form.Item
            name="build_type"
            label="Build Type"
            rules={[{ required: true }]}
          >
            <Select>
              <Select.Option value="full">Full Build</Select.Option>
              <Select.Option value="incremental">Incremental Build</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Publish Modal */}
      <Modal
        title="Publish Version"
        open={publishModalOpen}
        onCancel={() => setPublishModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={publishVersion.isPending}
      >
        <Form form={form} layout="vertical" onFinish={handlePublish}>
          <Form.Item
            name="target_environment_id"
            label="Target Environment"
            rules={[{ required: true, message: 'Please select an environment' }]}
          >
            <Select placeholder="Select environment">
              <Select.Option value="production">Production</Select.Option>
              <Select.Option value="staging">Staging</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="alias_name" label="Alias Name">
            <Input placeholder="e.g., latest" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Ingest Modal */}
      <Modal
        title="Ingest Data"
        open={ingestModalOpen}
        onCancel={() => {
          setIngestModalOpen(false)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        confirmLoading={ingestVersion.isPending}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleIngest}
          initialValues={{ source_type: 'filesystem', incremental: false }}
        >
          <Form.Item
            name="source_type"
            label="Source Type"
            rules={[{ required: true, message: 'Please select a source type' }]}
          >
            <Select>
              <Select.Option value="filesystem">Filesystem</Select.Option>
              <Select.Option value="sitemap">Sitemap</Select.Option>
              <Select.Option value="forum_api">Forum API</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="source_config"
            label="Source Configuration (JSON)"
            rules={[{ required: true, message: 'Please provide source configuration' }]}
            extra={'Example: {"root_path": "/path/to/docs", "patterns": "**/*.md"}'}
          >
            <Input.TextArea
              rows={4}
              placeholder={'{"root_path": "/path/to/documents", "patterns": "**/*.md,**/*.txt"}'}
            />
          </Form.Item>
          <Form.Item
            name="incremental"
            label="Incremental Ingestion"
            valuePropName="checked"
          >
            <Select>
              <Select.Option value={false}>Full (fetch all files)</Select.Option>
              <Select.Option value={true}>Incremental (only new/changed files)</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default KnowledgeBaseDetail
