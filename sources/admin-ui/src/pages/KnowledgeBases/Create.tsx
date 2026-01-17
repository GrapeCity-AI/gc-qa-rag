import { Typography, Form, Input, Button, Card, App } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useCreateKnowledgeBase } from '../../hooks/useKnowledgeBases'

const { Title } = Typography
const { TextArea } = Input

function KnowledgeBaseCreate() {
  const navigate = useNavigate()
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const createKb = useCreateKnowledgeBase()

  const handleSubmit = async (values: { name: string; description?: string }) => {
    try {
      const result = await createKb.mutateAsync({
        name: values.name,
        description: values.description || '',
      })
      message.success('Knowledge base created')
      navigate(`/knowledge-bases/${result.id}`)
    } catch {
      message.error('Failed to create knowledge base')
    }
  }

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

      <Card style={{ maxWidth: 600 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="Name"
            rules={[
              { required: true, message: 'Please enter a name' },
              { max: 255, message: 'Name must be less than 255 characters' },
            ]}
          >
            <Input placeholder="Enter knowledge base name" />
          </Form.Item>

          <Form.Item
            name="description"
            label="Description"
            rules={[
              { max: 2000, message: 'Description must be less than 2000 characters' },
            ]}
          >
            <TextArea
              placeholder="Enter description (optional)"
              rows={4}
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={createKb.isPending}
            >
              Create Knowledge Base
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default KnowledgeBaseCreate
