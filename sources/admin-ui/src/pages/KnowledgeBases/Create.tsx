import { useState } from 'react'
import {
  Typography,
  Form,
  Input,
  Button,
  Card,
  App,
  Steps,
  Space,
  Select,
  InputNumber,
  Switch,
  Descriptions,
  Tag,
  Divider,
  Alert,
  Row,
  Col,
} from 'antd'
import {
  ArrowLeftOutlined,
  InfoCircleOutlined,
  DatabaseOutlined,
  SettingOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useCreateKnowledgeBase } from '../../hooks/useKnowledgeBases'

const { Title, Text } = Typography
const { TextArea } = Input

interface WizardData {
  // Basic info
  name: string
  description: string
  // Data source
  source_type: string
  source_config: Record<string, unknown>
  // Pipeline
  chunk_size: number
  chunk_overlap: number
  enable_embedding: boolean
  embedding_model: string
  // Publishing target
  target_environment: string
  auto_publish: boolean
}

const defaultWizardData: WizardData = {
  name: '',
  description: '',
  source_type: 'sitemap',
  source_config: {},
  chunk_size: 512,
  chunk_overlap: 50,
  enable_embedding: true,
  embedding_model: 'text-embedding-v3',
  target_environment: 'development',
  auto_publish: false,
}

function KnowledgeBaseCreate() {
  const navigate = useNavigate()
  const { message } = App.useApp()
  const [currentStep, setCurrentStep] = useState(0)
  const [wizardData, setWizardData] = useState<WizardData>(defaultWizardData)
  const [basicForm] = Form.useForm()
  const [sourceForm] = Form.useForm()
  const [pipelineForm] = Form.useForm()
  const createKb = useCreateKnowledgeBase()

  const updateWizardData = (updates: Partial<WizardData>) => {
    setWizardData(prev => ({ ...prev, ...updates }))
  }

  const handleNext = async () => {
    try {
      if (currentStep === 0) {
        const values = await basicForm.validateFields()
        updateWizardData(values)
      } else if (currentStep === 1) {
        const values = await sourceForm.validateFields()
        updateWizardData(values)
      } else if (currentStep === 2) {
        const values = await pipelineForm.validateFields()
        updateWizardData(values)
      }
      setCurrentStep(prev => prev + 1)
    } catch {
      // Form validation failed
    }
  }

  const handlePrev = () => {
    setCurrentStep(prev => prev - 1)
  }

  const handleSubmit = async () => {
    try {
      const result = await createKb.mutateAsync({
        name: wizardData.name,
        description: wizardData.description,
        metadata: {
          source_type: wizardData.source_type,
          source_config: wizardData.source_config,
          pipeline_config: {
            chunk_size: wizardData.chunk_size,
            chunk_overlap: wizardData.chunk_overlap,
            enable_embedding: wizardData.enable_embedding,
            embedding_model: wizardData.embedding_model,
          },
          publish_config: {
            target_environment: wizardData.target_environment,
            auto_publish: wizardData.auto_publish,
          },
        },
      })
      message.success('Knowledge base created successfully')
      navigate(`/knowledge-bases/${result.id}`)
    } catch {
      message.error('Failed to create knowledge base')
    }
  }

  const steps = [
    {
      title: 'Basic Info',
      icon: <InfoCircleOutlined />,
    },
    {
      title: 'Data Source',
      icon: <DatabaseOutlined />,
    },
    {
      title: 'Pipeline',
      icon: <SettingOutlined />,
    },
    {
      title: 'Review',
      icon: <CheckCircleOutlined />,
    },
  ]

  // Step 1: Basic Info
  const BasicInfoStep = (
    <Form
      form={basicForm}
      layout="vertical"
      initialValues={{
        name: wizardData.name,
        description: wizardData.description,
      }}
    >
      <Form.Item
        name="name"
        label="Knowledge Base Name"
        rules={[
          { required: true, message: 'Please enter a name' },
          { max: 255, message: 'Name must be less than 255 characters' },
        ]}
      >
        <Input placeholder="e.g., Product Documentation, FAQ Base" size="large" />
      </Form.Item>

      <Form.Item
        name="description"
        label="Description"
        rules={[
          { max: 2000, message: 'Description must be less than 2000 characters' },
        ]}
      >
        <TextArea
          placeholder="Describe the purpose and content of this knowledge base..."
          rows={4}
        />
      </Form.Item>

      <Alert
        message="Tip"
        description="Choose a descriptive name that helps identify the content source and purpose of this knowledge base."
        type="info"
        showIcon
      />
    </Form>
  )

  // Step 2: Data Source
  const DataSourceStep = (
    <Form
      form={sourceForm}
      layout="vertical"
      initialValues={{
        source_type: wizardData.source_type,
        source_config: wizardData.source_config,
      }}
    >
      <Form.Item
        name="source_type"
        label="Data Source Type"
        rules={[{ required: true }]}
      >
        <Select size="large">
          <Select.Option value="sitemap">
            <Space>
              <Tag color="blue">Web</Tag>
              Sitemap Crawler
            </Space>
          </Select.Option>
          <Select.Option value="filesystem">
            <Space>
              <Tag color="green">Local</Tag>
              File System
            </Space>
          </Select.Option>
          <Select.Option value="forum_api">
            <Space>
              <Tag color="purple">API</Tag>
              Forum API
            </Space>
          </Select.Option>
        </Select>
      </Form.Item>

      <Form.Item
        noStyle
        shouldUpdate={(prevValues, currentValues) =>
          prevValues.source_type !== currentValues.source_type
        }
      >
        {({ getFieldValue }) => {
          const sourceType = getFieldValue('source_type')

          if (sourceType === 'sitemap') {
            return (
              <>
                <Form.Item
                  name={['source_config', 'sitemap_url']}
                  label="Sitemap URL"
                  rules={[{ required: true, type: 'url', message: 'Please enter a valid URL' }]}
                >
                  <Input placeholder="https://example.com/sitemap.xml" />
                </Form.Item>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name={['source_config', 'max_pages']}
                      label="Max Pages"
                      initialValue={100}
                    >
                      <InputNumber min={1} max={10000} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name={['source_config', 'crawl_delay']}
                      label="Crawl Delay (ms)"
                      initialValue={1000}
                    >
                      <InputNumber min={100} max={10000} step={100} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                </Row>
              </>
            )
          }

          if (sourceType === 'filesystem') {
            return (
              <>
                <Form.Item
                  name={['source_config', 'root_path']}
                  label="Root Path"
                  rules={[{ required: true, message: 'Please enter a path' }]}
                >
                  <Input placeholder="/path/to/documents" />
                </Form.Item>
                <Form.Item
                  name={['source_config', 'patterns']}
                  label="File Patterns"
                  initialValue="**/*.md,**/*.txt,**/*.pdf"
                >
                  <Input placeholder="**/*.md,**/*.txt,**/*.pdf" />
                </Form.Item>
              </>
            )
          }

          if (sourceType === 'forum_api') {
            return (
              <>
                <Form.Item
                  name={['source_config', 'api_base_url']}
                  label="API Base URL"
                  rules={[{ required: true, type: 'url', message: 'Please enter a valid URL' }]}
                >
                  <Input placeholder="https://forum.example.com/api" />
                </Form.Item>
                <Form.Item
                  name={['source_config', 'api_key']}
                  label="API Key"
                >
                  <Input.Password placeholder="Optional API key for authentication" />
                </Form.Item>
              </>
            )
          }

          return null
        }}
      </Form.Item>
    </Form>
  )

  // Step 3: Pipeline Configuration
  const PipelineStep = (
    <Form
      form={pipelineForm}
      layout="vertical"
      initialValues={{
        chunk_size: wizardData.chunk_size,
        chunk_overlap: wizardData.chunk_overlap,
        enable_embedding: wizardData.enable_embedding,
        embedding_model: wizardData.embedding_model,
        target_environment: wizardData.target_environment,
        auto_publish: wizardData.auto_publish,
      }}
    >
      <Divider orientation="left">Text Processing</Divider>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="chunk_size"
            label="Chunk Size"
            tooltip="Number of characters per text chunk"
          >
            <InputNumber min={100} max={4000} step={50} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="chunk_overlap"
            label="Chunk Overlap"
            tooltip="Number of overlapping characters between chunks"
          >
            <InputNumber min={0} max={500} step={10} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Divider orientation="left">Embedding</Divider>

      <Form.Item
        name="enable_embedding"
        label="Enable Embedding"
        valuePropName="checked"
      >
        <Switch />
      </Form.Item>

      <Form.Item
        noStyle
        shouldUpdate={(prevValues, currentValues) =>
          prevValues.enable_embedding !== currentValues.enable_embedding
        }
      >
        {({ getFieldValue }) =>
          getFieldValue('enable_embedding') ? (
            <Form.Item
              name="embedding_model"
              label="Embedding Model"
            >
              <Select>
                <Select.Option value="text-embedding-v3">
                  text-embedding-v3 (Recommended)
                </Select.Option>
                <Select.Option value="text-embedding-v2">
                  text-embedding-v2
                </Select.Option>
                <Select.Option value="bge-large-zh">
                  bge-large-zh (Chinese optimized)
                </Select.Option>
              </Select>
            </Form.Item>
          ) : null
        }
      </Form.Item>

      <Divider orientation="left">Publishing</Divider>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="target_environment"
            label="Default Target Environment"
          >
            <Select>
              <Select.Option value="development">Development</Select.Option>
              <Select.Option value="staging">Staging</Select.Option>
              <Select.Option value="production">Production</Select.Option>
            </Select>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="auto_publish"
            label="Auto Publish After Build"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Col>
      </Row>
    </Form>
  )

  // Step 4: Review
  const ReviewStep = (
    <div>
      <Alert
        message="Review your configuration"
        description="Please review the settings below before creating the knowledge base. You can go back to modify any settings."
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Card title="Basic Information" size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={1} size="small">
          <Descriptions.Item label="Name">
            <Text strong>{wizardData.name || '-'}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Description">
            {wizardData.description || <Text type="secondary">No description</Text>}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="Data Source" size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={1} size="small">
          <Descriptions.Item label="Source Type">
            <Tag color="blue">{wizardData.source_type}</Tag>
          </Descriptions.Item>
          {wizardData.source_config && Object.entries(wizardData.source_config).map(([key, value]) => (
            <Descriptions.Item key={key} label={key.replace(/_/g, ' ')}>
              {key.includes('key') || key.includes('password')
                ? '••••••••'
                : String(value) || '-'}
            </Descriptions.Item>
          ))}
        </Descriptions>
      </Card>

      <Card title="Pipeline Configuration" size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="Chunk Size">{wizardData.chunk_size}</Descriptions.Item>
          <Descriptions.Item label="Chunk Overlap">{wizardData.chunk_overlap}</Descriptions.Item>
          <Descriptions.Item label="Embedding">
            {wizardData.enable_embedding ? (
              <Tag color="green">Enabled</Tag>
            ) : (
              <Tag>Disabled</Tag>
            )}
          </Descriptions.Item>
          {wizardData.enable_embedding && (
            <Descriptions.Item label="Model">{wizardData.embedding_model}</Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      <Card title="Publishing" size="small">
        <Descriptions column={2} size="small">
          <Descriptions.Item label="Target Environment">
            <Tag>{wizardData.target_environment}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Auto Publish">
            {wizardData.auto_publish ? (
              <Tag color="green">Yes</Tag>
            ) : (
              <Tag>No</Tag>
            )}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  )

  const stepContents = [BasicInfoStep, DataSourceStep, PipelineStep, ReviewStep]

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/knowledge-bases')}
        style={{ marginBottom: 24 }}
      >
        Back
      </Button>

      <Title level={4}>Create Knowledge Base</Title>

      <Card style={{ maxWidth: 800 }}>
        <Steps
          current={currentStep}
          items={steps}
          style={{ marginBottom: 32 }}
        />

        <div style={{ minHeight: 300, marginBottom: 24 }}>
          {stepContents[currentStep]}
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button
            onClick={handlePrev}
            disabled={currentStep === 0}
          >
            Previous
          </Button>
          <Space>
            <Button onClick={() => navigate('/knowledge-bases')}>
              Cancel
            </Button>
            {currentStep < steps.length - 1 ? (
              <Button type="primary" onClick={handleNext}>
                Next
              </Button>
            ) : (
              <Button
                type="primary"
                onClick={handleSubmit}
                loading={createKb.isPending}
              >
                Create Knowledge Base
              </Button>
            )}
          </Space>
        </div>
      </Card>
    </div>
  )
}

export default KnowledgeBaseCreate
