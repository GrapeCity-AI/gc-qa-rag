import { useState } from 'react'
import { Table, Tag, Space, Select, Input, Empty, Typography } from 'antd'
import {
  FileOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileImageOutlined,
  FileExcelOutlined,
  FileWordOutlined,
  FileUnknownOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import { useVersionFiles } from '../../../hooks/useVersions'
import { formatRelativeTime, formatBytes } from '../../../utils/format'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import { FileVersion } from '../../../api/types'

const { Text } = Typography

interface FileBrowserProps {
  versionId: string
}

function getFileIcon(mimeType: string | null) {
  if (!mimeType) return <FileUnknownOutlined />

  if (mimeType.startsWith('text/')) return <FileTextOutlined />
  if (mimeType === 'application/pdf') return <FilePdfOutlined />
  if (mimeType.startsWith('image/')) return <FileImageOutlined />
  if (mimeType.includes('spreadsheet') || mimeType.includes('excel')) return <FileExcelOutlined />
  if (mimeType.includes('word') || mimeType.includes('document')) return <FileWordOutlined />

  return <FileOutlined />
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'default',
    indexing: 'processing',
    indexed: 'success',
    failed: 'error',
    skipped: 'warning',
  }
  return colors[status] || 'default'
}

function FileBrowser({ versionId }: FileBrowserProps) {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)
  const [searchText, setSearchText] = useState('')

  const { data: filesData, isLoading } = useVersionFiles(versionId, {
    page,
    page_size: pageSize,
    status: statusFilter,
  })

  // Client-side filtering by name (API may not support this)
  const filteredFiles = filesData?.data.filter(file => {
    if (!searchText) return true
    const name = file.original_name || file.source_uri || ''
    return name.toLowerCase().includes(searchText.toLowerCase())
  }) || []

  const columns: ColumnsType<FileVersion> = [
    {
      title: 'Name',
      key: 'name',
      ellipsis: true,
      render: (_, record) => {
        const name = record.original_name || record.source_uri || record.id
        const icon = getFileIcon(record.mime_type)
        return (
          <Space>
            <span style={{ color: '#1890ff' }}>{icon}</span>
            <Text ellipsis style={{ maxWidth: 300 }} title={name}>
              {name}
            </Text>
          </Space>
        )
      },
    },
    {
      title: 'Source',
      dataIndex: 'source_type',
      key: 'source_type',
      width: 100,
      render: (sourceType: string | null) => (
        sourceType ? <Tag>{sourceType}</Tag> : '-'
      ),
    },
    {
      title: 'Size',
      dataIndex: 'size_bytes',
      key: 'size_bytes',
      width: 100,
      render: (size: number | null) => (
        size ? formatBytes(size) : '-'
      ),
    },
    {
      title: 'Type',
      dataIndex: 'mime_type',
      key: 'mime_type',
      width: 150,
      ellipsis: true,
      render: (mimeType: string | null) => (
        <Text type="secondary" style={{ fontSize: 12 }}>
          {mimeType || '-'}
        </Text>
      ),
    },
    {
      title: 'Index Status',
      dataIndex: 'index_status',
      key: 'index_status',
      width: 120,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{status}</Tag>
      ),
    },
    {
      title: 'Indexed At',
      dataIndex: 'indexed_at',
      key: 'indexed_at',
      width: 150,
      render: (date: string | null) => (
        date ? formatRelativeTime(date) : '-'
      ),
    },
  ]

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setPage(pagination.current || 1)
    setPageSize(pagination.pageSize || 10)
  }

  if (!versionId) {
    return (
      <Empty
        description="Select a version to browse files"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    )
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        <Input
          placeholder="Search files..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ width: 250 }}
          allowClear
        />
        <Select
          placeholder="Filter by status"
          value={statusFilter}
          onChange={setStatusFilter}
          style={{ width: 150 }}
          allowClear
        >
          <Select.Option value="pending">Pending</Select.Option>
          <Select.Option value="indexing">Indexing</Select.Option>
          <Select.Option value="indexed">Indexed</Select.Option>
          <Select.Option value="failed">Failed</Select.Option>
          <Select.Option value="skipped">Skipped</Select.Option>
        </Select>
        <Text type="secondary">
          {filesData?.meta?.total_items || 0} files
        </Text>
      </Space>

      <Table
        columns={columns}
        dataSource={filteredFiles}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: page,
          pageSize: pageSize,
          total: filesData?.meta?.total_items || 0,
          showSizeChanger: true,
          showQuickJumper: true,
          pageSizeOptions: ['10', '20', '50', '100'],
        }}
        onChange={handleTableChange}
        size="small"
      />
    </div>
  )
}

export default FileBrowser
