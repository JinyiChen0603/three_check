/**
 * 仪表盘页面
 */

import { useEffect, useState } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Table,
  Typography,
  Space,
  Tag,
  Spin,
  message,
} from 'antd';
import {
  FileTextOutlined,
  CheckCircleOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../../store/useAuthStore';
import { userApi } from '../../api';
import type { Ranking } from '../../types';
import { BUSINESS_CONSTANTS } from '../../config/constants';

const { Title } = Typography;

export default function Dashboard() {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [rankings, setRankings] = useState<Ranking[]>([]);
  const [stats, setStats] = useState<any>({});

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [rankingsData, statsData] = await Promise.all([
        userApi.getRankings(),
        userApi.getStats(),
      ]);
      setRankings(rankingsData);
      setStats(statsData);
    } catch (error) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 排名表格列定义
  const columns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 80,
      render: (rank: number) => {
        if (rank === 1) return <Tag color="gold">🥇 {rank}</Tag>;
        if (rank === 2) return <Tag color="silver">🥈 {rank}</Tag>;
        if (rank === 3) return <Tag color="bronze">🥉 {rank}</Tag>;
        return rank;
      },
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (username: string, record: Ranking) => (
        <Space>
          {username}
          {record.user_id === user?.id && <Tag color="blue">我</Tag>}
        </Space>
      ),
    },
    {
      title: '总收入',
      dataIndex: 'total_earnings',
      key: 'total_earnings',
      render: (earnings: number) => `¥${earnings.toFixed(2)}`,
    },
    {
      title: '出题数',
      dataIndex: 'problems_created',
      key: 'problems_created',
    },
    {
      title: '评分数',
      dataIndex: 'reviews_completed',
      key: 'reviews_completed',
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Title level={2}>仪表盘</Title>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="当前余额"
              value={user?.balance || 0}
              precision={2}
              prefix="¥"
              styles={{ content: { color: '#3f8600' } }}
              suffix={
                <span style={{ fontSize: 14, color: '#999' }}>
                  元
                </span>
              }
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="已出题目"
              value={user?.problems_created_count || 0}
              prefix={<FileTextOutlined />}
              suffix={
                <span style={{ fontSize: 14, color: '#999' }}>
                  / {stats.total_problems || 300} 题
                </span>
              }
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="已完成评分"
              value={user?.reviews_completed_count || 0}
              prefix={<CheckCircleOutlined />}
              suffix={
                <span style={{ fontSize: 14, color: '#999' }}>
                  题
                </span>
              }
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="我的排名"
              value={stats.rank || '-'}
              prefix={<TrophyOutlined />}
              suffix={
                <span style={{ fontSize: 14, color: '#999' }}>
                  / {rankings.length}
                </span>
              }
            />
          </Card>
        </Col>
      </Row>

      {/* 收入说明 */}
      <Card title="收入说明" style={{ marginTop: 24 }}>
        <Space orientation="vertical" size="middle">
          <div>
            <Tag color="green">出题奖励</Tag>
            每个合格题目奖励 <strong>¥{BUSINESS_CONSTANTS.REWARD_PER_PROBLEM}</strong> 元
          </div>
          <div>
            <Tag color="blue">评分奖励</Tag>
            每完成一个评分任务奖励 <strong>¥{BUSINESS_CONSTANTS.REWARD_PER_REVIEW}</strong> 元
          </div>
          <div>
            <Tag color="orange">任务规则</Tag>
            每次最多领取 <strong>{BUSINESS_CONSTANTS.MAX_TASKS_PER_CLAIM}</strong> 个任务，
            超过 <strong>{BUSINESS_CONSTANTS.TASK_TIMEOUT_HOURS}</strong> 小时未完成将自动取消
          </div>
        </Space>
      </Card>

      {/* 排行榜 */}
      <Card 
        title={
          <Space>
            <TrophyOutlined />
            排行榜
          </Space>
        } 
        style={{ marginTop: 24 }}
      >
        <Table
          columns={columns}
          dataSource={rankings}
          rowKey="user_id"
          pagination={false}
          size="middle"
        />
      </Card>
    </div>
  );
}

