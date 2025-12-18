/**
 * 任务管理页面
 */

import { useState } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  InputNumber,
  Tabs,
  Typography,
  Statistic,
  Row,
  Col,
} from 'antd';
import {
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { useTask } from '../../hooks/useTask';
import type { Task } from '../../types';
import { TaskType, TaskStatus } from '../../config/constants';
import { BUSINESS_CONSTANTS } from '../../config/constants';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import utc from 'dayjs/plugin/utc';
import 'dayjs/locale/zh-cn';

dayjs.extend(relativeTime);
dayjs.extend(utc);
dayjs.locale('zh-cn');

const { Title, Text } = Typography;
const { TabPane } = Tabs;

export default function Tasks() {
  // 使用自定义Hook管理任务状态
  const {
    tasks,
    loading,
    problemCreationTotal,
    problemReviewTotal,
    claimTasks,
    abandonTask,
  } = useTask();

  const [claimModalVisible, setClaimModalVisible] = useState(false);
  const [claimCount, setClaimCount] = useState(10);
  const [currentTaskType, setCurrentTaskType] = useState<TaskType>(
    TaskType.PROBLEM_CREATION
  );

  const handleClaimTasks = async () => {
    if (claimCount < 1 || claimCount > BUSINESS_CONSTANTS.MAX_TASKS_PER_CLAIM) {
      return;
    }

    try {
      await claimTasks(currentTaskType, claimCount);
      setClaimModalVisible(false);
      setClaimCount(10); // 重置数量
    } catch (error) {
      // 错误已在Hook中处理
    }
  };

  const handleAbandonTask = (taskId: number) => {
    Modal.confirm({
      title: '确认放弃任务',
      content: '放弃后此任务将返回任务池，您确定要放弃吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await abandonTask(taskId);
        } catch (error) {
          // 错误已在Hook中处理
        }
      },
    });
  };

  const getTimeRemaining = (expiresAt?: string) => {
    if (!expiresAt) return null;
    
    // 后端返回的是 UTC 时间，需要正确解析
    // 如果时间字符串没有时区信息，dayjs 会按本地时区解析，需要明确指定 UTC
    const expires = dayjs.utc(expiresAt);
    const now = dayjs.utc(); // 使用 UTC 时间进行比较，避免时区问题
    
    const diff = expires.diff(now, 'minute');
    
    if (diff < 0) return <Text type="danger">已超时</Text>;
    
    const hours = Math.floor(diff / 60);
    const minutes = diff % 60;
    
    if (hours === 0) {
      return <Text type="warning">{minutes} 分钟后超时</Text>;
    }
    
    return <Text>{hours} 小时 {minutes} 分钟后超时</Text>;
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

  const columns = [
    {
      title: '任务ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
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
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: TaskStatus) => getStatusTag(status),
    },
    {
      title: '任务数量',
      dataIndex: 'total_count',
      key: 'total_count',
      width: 100,
      render: (count?: number) => count !== undefined ? count : '-',
    },
    {
      title: '领取时间',
      dataIndex: 'claimed_at',
      key: 'claimed_at',
      render: (time?: string) => time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-',
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
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleAbandonTask(record.id)}
            >
              放弃
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const problemCreationTasks = tasks.filter(
    (t) => t.task_type === TaskType.PROBLEM_CREATION
  );
  const problemReviewTasks = tasks.filter(
    (t) => t.task_type === TaskType.PROBLEM_REVIEW
  );

  return (
    <div>
      <Title level={2}>任务管理</Title>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="出题任务"
              value={problemCreationTotal}
              suffix={`/ ${BUSINESS_CONSTANTS.MAX_TASKS_PER_CLAIM}`}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="评分任务"
              value={problemReviewTotal}
              suffix={`/ ${BUSINESS_CONSTANTS.MAX_TASKS_PER_CLAIM}`}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="出题奖励"
              value={BUSINESS_CONSTANTS.REWARD_PER_PROBLEM}
              prefix="¥"
              suffix="元/题"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="评分奖励"
              value={BUSINESS_CONSTANTS.REWARD_PER_REVIEW}
              prefix="¥"
              suffix="元/题"
            />
          </Card>
        </Col>
      </Row>

      {/* 任务列表 */}
      <Card>
        <Tabs defaultActiveKey="problem_creation">
          <TabPane
            tab={
              <span>
                <FileTextOutlined />
                出题任务 ({problemCreationTotal})
              </span>
            }
            key="problem_creation"
          >
            <Space style={{ marginBottom: 16 }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setCurrentTaskType(TaskType.PROBLEM_CREATION);
                  setClaimModalVisible(true);
                }}
              >
                领取出题任务
              </Button>
              <Text type="secondary">
                每个任务需在 {BUSINESS_CONSTANTS.TASK_TIMEOUT_HOURS} 小时内完成
              </Text>
            </Space>
            
            <Table
              columns={columns}
              dataSource={problemCreationTasks}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </TabPane>

          <TabPane
            tab={
              <span>
                <CheckCircleOutlined />
                评分任务 ({problemReviewTotal})
              </span>
            }
            key="problem_review"
          >
            <Space style={{ marginBottom: 16 }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setCurrentTaskType(TaskType.PROBLEM_REVIEW);
                  setClaimModalVisible(true);
                }}
              >
                领取评分任务
              </Button>
              <Text type="secondary">
                每个任务需在 {BUSINESS_CONSTANTS.TASK_TIMEOUT_HOURS} 小时内完成
              </Text>
            </Space>
            
            <Table
              columns={columns}
              dataSource={problemReviewTasks}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 领取任务对话框 */}
      <Modal
        title={`领取${currentTaskType === TaskType.PROBLEM_CREATION ? '出题' : '评分'}任务`}
        open={claimModalVisible}
        onOk={handleClaimTasks}
        onCancel={() => setClaimModalVisible(false)}
        okText="确认领取"
        cancelText="取消"
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Text>领取数量：</Text>
            <InputNumber
              min={1}
              max={BUSINESS_CONSTANTS.MAX_TASKS_PER_CLAIM}
              value={claimCount}
              onChange={(value) => setClaimCount(value || 1)}
              style={{ width: '100%', marginTop: 8 }}
            />
            <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
              每次最多领取 {BUSINESS_CONSTANTS.MAX_TASKS_PER_CLAIM} 个任务
            </Text>
          </div>

          <div>
            <Text strong>注意事项：</Text>
            <ul style={{ marginTop: 8, paddingLeft: 20 }}>
              <li>领取后需在 {BUSINESS_CONSTANTS.TASK_TIMEOUT_HOURS} 小时内完成</li>
              <li>只有完成当前任务后才能继续领取新任务</li>
              <li>可以随时放弃任务，放弃的任务会返回任务池</li>
            </ul>
          </div>
        </Space>
      </Modal>
    </div>
  );
}

