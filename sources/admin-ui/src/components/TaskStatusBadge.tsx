import { Tag } from 'antd'
import {
  ClockCircleOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  MinusCircleOutlined,
} from '@ant-design/icons'

interface TaskStatusBadgeProps {
  status: string
}

const statusConfig: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  pending: {
    color: 'default',
    icon: <ClockCircleOutlined />,
    label: 'Pending',
  },
  running: {
    color: 'processing',
    icon: <SyncOutlined spin />,
    label: 'Running',
  },
  completed: {
    color: 'success',
    icon: <CheckCircleOutlined />,
    label: 'Completed',
  },
  failed: {
    color: 'error',
    icon: <CloseCircleOutlined />,
    label: 'Failed',
  },
  cancelled: {
    color: 'warning',
    icon: <MinusCircleOutlined />,
    label: 'Cancelled',
  },
}

function TaskStatusBadge({ status }: TaskStatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.pending

  return (
    <Tag color={config.color} icon={config.icon}>
      {config.label}
    </Tag>
  )
}

export default TaskStatusBadge
