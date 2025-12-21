/**
 * 简化版仪表盘（不调用 API）
 */

import { Card, Typography, Row, Col, Statistic } from 'antd';
import {
  WalletOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../../store/useAuthStore';

const { Title } = Typography;

export default function SimpleDashboard() {
  const { user } = useAuthStore();

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>仪表盘</Title>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="当前余额"
              value={user?.balance || 0}
              precision={2}
              prefix="¥"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="已出题目"
              value={user?.problems_created_count || 0}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="已完成评分"
              value={user?.reviews_completed_count || 0}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="我的排名"
              value="-"
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card title="收入说明" style={{ marginTop: 24 }}>
        <p>每个合格题目奖励：¥50</p>
        <p>每完成一个评分任务奖励：¥10</p>
      </Card>
    </div>
  );
}

