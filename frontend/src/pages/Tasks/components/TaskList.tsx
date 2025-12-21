import { Button, Modal, Space, Table, Tag, Typography } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, DeleteOutlined, FileTextOutlined } from '@ant-design/icons';
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

  const columns = [
    { title: '任务ID', dataIndex: 'id', key: 'id', width: 80 },
    {
      title: '任务类型',
      dataIndex: 'task_type',
      key: 'task_type',
      render: (type: TaskType) => (
        <Tag icon={type === TaskType.PROBLEM_CREATION ? <FileTextOutlined /> : <CheckCircleOutlined />}>
          {type === TaskType.PROBLEM_CREATION ? '出题任务' : '评分任务'}
        </Tag>
      ),
    },
    { title: '状态', dataIndex: 'status', key: 'status', render: (status: TaskStatus) => getStatusTag(status) },
    {
      title: '任务数量',
      dataIndex: 'total_count',
      key: 'total_count',
      width: 100,
      render: (count?: number) => (count !== undefined ? count : '-'),
    },
    {
      title: '领取时间',
      dataIndex: 'claimed_at',
      key: 'claimed_at',
      render: (time?: string) => (time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-'),
    },
    {
      title: '剩余时间',
      dataIndex: 'expires_at',
      key: 'expires_at',
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
      render: (_: any, record: Task) => (
        <Space>
          {(record.status === TaskStatus.CLAIMED || record.status === TaskStatus.IN_PROGRESS) && (
            <Button type="link" danger icon={<DeleteOutlined />} onClick={() => handleAbandonTask(record.id)}>
              放弃
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Table columns={columns} dataSource={tasks} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
  );
}


