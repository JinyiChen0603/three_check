import { Button, Modal, Space, Table, Tag, Typography, Progress } from 'antd';
import {
  ClockCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  StarOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import utc from 'dayjs/plugin/utc';
import 'dayjs/locale/zh-cn';

import type { Task } from '../../../types';
import { TaskStatus, TaskType } from '../../../config/constants';

dayjs.extend(relativeTime);
dayjs.extend(utc);
dayjs.locale('zh-cn');

const { Text } = Typography;

export function TaskList({
  tasks,
  loading,
  onAbandon,
}: {
  tasks: Task[];
  loading: boolean;
  onAbandon: (taskId: number) => Promise<void>;
}) {
  const navigate = useNavigate();
  const getTimeRemaining = (expiresAt?: string) => {
    if (!expiresAt) return null;

    // 后端返回的是 UTC 时间，需要正确解析
    const expires = dayjs.utc(expiresAt);
    const now = dayjs.utc();

    const diff = expires.diff(now, 'minute');

    if (diff < 0) return <Text type="danger">已超时</Text>;

    const hours = Math.floor(diff / 60);
    const minutes = diff % 60;

    if (hours === 0) {
      return <Text type="warning">{minutes} 分钟后超时</Text>;
    }

    return (
      <Text>
        {hours} 小时 {minutes} 分钟后超时
      </Text>
    );
  };

  const getStatusTag = (status: TaskStatus) => {
    const statusConfig: Record<TaskStatus, { color: string; text: string }> = {
      [TaskStatus.AVAILABLE]: { color: 'default', text: '可领取' },
      [TaskStatus.CLAIMED]: { color: 'processing', text: '已领取' },
      [TaskStatus.IN_PROGRESS]: { color: 'blue', text: '进行中' },
      [TaskStatus.SUBMITTED]: { color: 'orange', text: '已提交' },
      [TaskStatus.COMPLETED]: { color: 'success', text: '已完成' },
      [TaskStatus.REJECTED]: { color: 'error', text: '已拒绝' },
    };

    const config = statusConfig[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const handleAbandonTask = (taskId: number) => {
    Modal.confirm({
      title: '确认放弃任务',
      content: '放弃后此任务将返回任务池，您确定要放弃吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        await onAbandon(taskId);
      },
    });
  };

  const handleEnterTask = (task: Task) => {
    if (task.task_type === TaskType.PROBLEM_CREATION) {
      navigate('/problem');
    } else {
      navigate('/review');
    }
  };

  const columns = [
    { title: '批次ID', dataIndex: 'batch_id', key: 'batch_id', width: 120, ellipsis: true,
      render: (batchId?: string) => batchId ? <Text code>{batchId.replace('batch_', '')}</Text> : '-'
    },
    {
      title: '任务类型',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 120,
      render: (type: TaskType) => (
        <Tag 
          icon={type === TaskType.PROBLEM_CREATION ? <EditOutlined /> : <StarOutlined />}
          color={type === TaskType.PROBLEM_CREATION ? 'blue' : 'purple'}
        >
          {type === TaskType.PROBLEM_CREATION ? '出题' : '评分'}
        </Tag>
      ),
    },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status', 
      width: 100,
      render: (status: TaskStatus) => getStatusTag(status) 
    },
    {
      title: '进度',
      key: 'progress',
      width: 160,
      render: (_: any, record: Task) => {
        const total = record.total_count || 0;
        const completed = record.completed_count || 0;
        const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
        return (
          <div>
            <Progress 
              percent={percent} 
              size="small" 
              status={completed >= total ? 'success' : 'active'}
              format={() => `${completed}/${total}`}
            />
          </div>
        );
      },
    },
    {
      title: '领取时间',
      dataIndex: 'claimed_at',
      key: 'claimed_at',
      width: 150,
      render: (time?: string) => (time ? dayjs(time).format('MM-DD HH:mm') : '-'),
    },
    {
      title: '剩余时间',
      dataIndex: 'expires_at',
      key: 'expires_at',
      width: 160,
      render: (_: any, record: Task) => (
        <Space>
          <ClockCircleOutlined />
          {getTimeRemaining(record.expires_at)}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: any, record: Task) => (
        <Space>
          {(record.status === TaskStatus.CLAIMED || record.status === TaskStatus.IN_PROGRESS) && (
            <>
              <Button 
                type="primary" 
                size="small"
                icon={record.task_type === TaskType.PROBLEM_CREATION ? <EditOutlined /> : <StarOutlined />}
                onClick={() => handleEnterTask(record)}
              >
                {record.task_type === TaskType.PROBLEM_CREATION ? '去出题' : '去评分'}
              </Button>
              <Button 
                type="link" 
                danger 
                size="small"
                icon={<DeleteOutlined />} 
                onClick={() => handleAbandonTask(record.id)}
              >
                放弃
              </Button>
            </>
          )}
          {record.status === TaskStatus.SUBMITTED && (
            <Tag color="green">已提交</Tag>
          )}
          {record.status === TaskStatus.COMPLETED && (
            <Tag color="success">已完成</Tag>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Table columns={columns} dataSource={tasks} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
  );
}


