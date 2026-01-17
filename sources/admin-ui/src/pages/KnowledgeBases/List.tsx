import { useState } from 'react'
import {
  Typography,
  Button,
  Input,
  Row,
  Col,
  Empty,
  Spin,
  Pagination,
  Space,
} from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useKnowledgeBases } from '../../hooks/useKnowledgeBases'
import KbCard from '../../components/KbCard'

const { Title } = Typography
const { Search } = Input

function KnowledgeBaseList() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const pageSize = 12

  const { data, isLoading } = useKnowledgeBases({
    page,
    page_size: pageSize,
    search: search || undefined,
  })

  const handleSearch = (value: string) => {
    setSearch(value)
    setPage(1)
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0 }}>
          Knowledge Bases
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/knowledge-bases/create')}
        >
          Create
        </Button>
      </div>

      <div style={{ marginBottom: 24 }}>
        <Search
          placeholder="Search knowledge bases..."
          allowClear
          enterButton={<SearchOutlined />}
          size="large"
          onSearch={handleSearch}
          style={{ maxWidth: 400 }}
        />
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: 48 }}>
          <Spin size="large" />
        </div>
      ) : data?.data.length === 0 ? (
        <Empty
          description={search ? 'No matching knowledge bases found' : 'No knowledge bases yet'}
        >
          {!search && (
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate('/knowledge-bases/create')}
            >
              Create your first knowledge base
            </Button>
          )}
        </Empty>
      ) : (
        <>
          <Row gutter={[16, 16]}>
            {data?.data.map((kb) => (
              <Col key={kb.id} xs={24} sm={12} lg={8} xl={6}>
                <KbCard knowledgeBase={kb} />
              </Col>
            ))}
          </Row>

          {data?.meta && data.meta.total_pages > 1 && (
            <div style={{ textAlign: 'center', marginTop: 24 }}>
              <Pagination
                current={page}
                pageSize={pageSize}
                total={data.meta.total_items}
                onChange={setPage}
                showSizeChanger={false}
                showQuickJumper
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default KnowledgeBaseList
