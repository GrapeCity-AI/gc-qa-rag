import { useState, useEffect } from 'react'
import {
  Modal,
  Form,
  Input,
  Button,
  Alert,
  Space,
  Descriptions,
} from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { useTestConnector } from '../../hooks/useConnectors'
import { ConnectorType } from '../../api/types'

const { TextArea } = Input

interface TestDialogProps {
  open: boolean
  connector: ConnectorType | null
  onClose: () => void
}

function TestDialog({ open, connector, onClose }: TestDialogProps) {
  const [form] = Form.useForm()
  const testConnector = useTestConnector()
  const [testResult, setTestResult] = useState<{
    success: boolean
    message: string
  } | null>(null)

  useEffect(() => {
    if (open) {
      form.resetFields()
      setTestResult(null)
    }
  }, [open, form])

  const handleTest = async (values: Record<string, unknown>) => {
    if (!connector) return

    try {
      const result = await testConnector.mutateAsync({
        connector_type: connector.type,
        config: values,
      })
      setTestResult({
        success: result.success,
        message: result.message,
      })
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Failed to test connection',
      })
    }
  }

  const getFormFields = () => {
    if (!connector?.config_schema?.properties) return null

    const properties = connector.config_schema.properties as Record<
      string,
      { type: string; description?: string; default?: unknown }
    >
    const required = (connector.config_schema.required || []) as string[]

    return Object.entries(properties).map(([key, schema]) => {
      const isRequired = required.includes(key)

      if (schema.type === 'array') {
        return (
          <Form.Item
            key={key}
            name={key}
            label={key}
            tooltip={schema.description}
            rules={isRequired ? [{ required: true }] : []}
          >
            <TextArea
              placeholder={`Enter ${key} (one per line)`}
              rows={3}
            />
          </Form.Item>
        )
      }

      if (schema.type === 'boolean') {
        return null // Skip boolean fields for simplicity
      }

      return (
        <Form.Item
          key={key}
          name={key}
          label={key}
          tooltip={schema.description}
          rules={isRequired ? [{ required: true }] : []}
          initialValue={schema.default}
        >
          <Input placeholder={schema.description || key} />
        </Form.Item>
      )
    })
  }

  return (
    <Modal
      title={`Test ${connector?.name || 'Connector'} Connection`}
      open={open}
      onCancel={onClose}
      footer={null}
      width={600}
    >
      {connector && (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Descriptions size="small" column={1}>
            <Descriptions.Item label="Type">{connector.type}</Descriptions.Item>
            <Descriptions.Item label="Description">
              {connector.description}
            </Descriptions.Item>
          </Descriptions>

          <Form form={form} layout="vertical" onFinish={handleTest}>
            {getFormFields()}

            <Form.Item>
              <Space>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={testConnector.isPending}
                >
                  Test Connection
                </Button>
                <Button onClick={onClose}>Cancel</Button>
              </Space>
            </Form.Item>
          </Form>

          {testResult && (
            <Alert
              type={testResult.success ? 'success' : 'error'}
              icon={
                testResult.success ? (
                  <CheckCircleOutlined />
                ) : (
                  <CloseCircleOutlined />
                )
              }
              message={testResult.success ? 'Connection Successful' : 'Connection Failed'}
              description={testResult.message}
              showIcon
            />
          )}
        </Space>
      )}
    </Modal>
  )
}

export default TestDialog
