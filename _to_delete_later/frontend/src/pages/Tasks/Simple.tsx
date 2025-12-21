/**
 * 任务管理页面（简化版）
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
  message,
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

const { Title, Text } = Typography;

export default function TasksSimple() {
  const [claimModalVisible, setClaimModalVisible] = useState(false);
  const [claimCount, setClaimCount] = useState(10);
  const [currentTaskType, setCurrentTaskType] = useState<'problem_creation' | 'problem_review'>('problem_creation');
  
  // 模拟任务数据
  const [problemCreationTasks] = useState([
    { id: 1, status: 'claimed', claimed_at: '2025-12-17 10:00:00', expires_at: '2025-12-17 22:00:00' },
    { id: 2, status: 'claimed', claimed_at: '2025-12-17 10:00:00', expires_at: '2025-12-17 22:00:00' },
  ]);
  
  const [problemReviewTasks] = useState([
    { id: 3, status: 'claimed', claimed_at: '2025-12-17 11:00:00', expires_at: '2025-12-17 23:00:00' },
  ]);

  const handleClaimTasks = () => {
    if (claimCount < 1 || claimCount > 50) {
      message.error('领取数量必须在 1-50 之间');
      return;
    }
    
    message.success(`成功领取 ${claimCount} 个任务！`);
    setClaimModalVisible(false);
  };

  const handleAbandonTask = (taskId: number) => {
    Modal.confirm({
      title: '确认放弃任务',
      content: '放弃后此任务将返回任务池，您确定要放弃吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: () => {
        message.success('已放弃任务');
      },
    });
  };

  const getTimeRemaining = (expiresAt: string) => {
    const now = new Date();
    const expires = new Date(expiresAt);
    const diff = expires.getTime() - now.getTime();
    
    if (diff < 0) return <Text type="danger">已超时</Text>;
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours === 0) {
      return <Text type="warning">{minutes} 分钟后超时</Text>;
    }
    
    return <Text>{hours} 小时 {minutes} 分钟后超时</Text>;
  };

  const getStatusTag = (status: string) => {
    const statusConfig: Record<string, { color: string; text: string }> = {
      available: { color: 'default', text: '可领取' },
      claimed: { color: 'processing', text: '已领取' },
      in_progress: { color: 'blue', text: '进行中' },
      submitted: { color: 'orange', text: '已提交' },
      completed: { color: 'success', text: '已完成' },
      rejected: { color: 'error', text: '已拒绝' },
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
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '领取时间',
      dataIndex: 'claimed_at',
      key: 'claimed_at',
    },
    {
      title: '剩余时间',
      dataIndex: 'expires_at',
      key: 'expires_at',
      render: (expiresAt: string) => (
        <Space>
          <ClockCircleOutlined />
          {getTimeRemaining(expiresAt)}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          {record.status === 'claimed' && (
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

  return (
    <div>
      <Title level={2}>任务管理</Title>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="出题任务"
              value={problemCreationTasks.length}
              suffix="/ 50"
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="评分任务"
              value={problemReviewTasks.length}
              suffix="/ 50"
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="出题奖励"
              value={50}
              prefix="¥"
              suffix="元/题"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="评分奖励"
              value={10}
              prefix="¥"
              suffix="元/题"
            />
          </Card>
        </Col>
      </Row>

      {/* 任务列表 */}
      <Card>
        <Tabs defaultActiveKey="problem_creation">
          <Tabs.TabPane
            tab={
              <span>
                <FileTextOutlined />
                出题任务 ({problemCreationTasks.length})
              </span>
            }
            key="problem_creation"
          >
            <Space style={{ marginBottom: 16 }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setCurrentTaskType('problem_creation');
                  setClaimModalVisible(true);
                }}
              >
                领取出题任务
              </Button>
              <Text type="secondary">
                每个任务需在 12 小时内完成
              </Text>
            </Space>
            
            <Table
              columns={columns}
              dataSource={problemCreationTasks}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Tabs.TabPane>

          <Tabs.TabPane
            tab={
              <span>
                <CheckCircleOutlined />
                评分任务 ({problemReviewTasks.length})
              </span>
            }
            key="problem_review"
          >
            <Space style={{ marginBottom: 16 }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setCurrentTaskType('problem_review');
                  setClaimModalVisible(true);
                }}
              >
                领取评分任务
              </Button>
              <Text type="secondary">
                每个任务需在 12 小时内完成
              </Text>
            </Space>
            
            <Table
              columns={columns}
              dataSource={problemReviewTasks}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Tabs.TabPane>
        </Tabs>
      </Card>

      {/* 领取任务对话框 */}
      <Modal
        title={`领取${currentTaskType === 'problem_creation' ? '出题' : '评分'}任务`}
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
              max={50}
              value={claimCount}
              onChange={(value) => setClaimCount(value || 1)}
              style={{ width: '100%', marginTop: 8 }}
            />
            <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
              每次最多领取 50 个任务
            </Text>
          </div>

          <div>
            <Text strong>注意事项：</Text>
            <ul style={{ marginTop: 8, paddingLeft: 20 }}>
              <li>领取后需在 12 小时内完成</li>
              <li>只有完成当前任务后才能继续领取新任务</li>
              <li>可以随时放弃任务，放弃的任务会返回任务池</li>
            </ul>
          </div>
        </Space>
      </Modal>
    </div>
  );
}

