import { Card, Col, Row, Statistic, Progress, Typography } from 'antd';
import { EditOutlined, StarOutlined, DollarOutlined, TrophyOutlined } from '@ant-design/icons';

import { useConfig } from '../../../hooks/useConfig';

const { Text } = Typography;

export function TaskStats({
  problemCreationTotal,
  problemCreationCompleted,
  problemReviewTotal,
  problemReviewCompleted,
}: {
  problemCreationTotal: number;
  problemCreationCompleted: number;
  problemReviewTotal: number;
  problemReviewCompleted: number;
}) {
  const config = useConfig();
  
  // 计算进度百分比（基于当前显示的 total）
  const creationPercent = problemCreationTotal > 0 
    ? Math.round((problemCreationCompleted / problemCreationTotal) * 100) 
    : 0;
  const reviewPercent = problemReviewTotal > 0 
    ? Math.round((problemReviewCompleted / problemReviewTotal) * 100) 
    : 0;

  return (
    <Row gutter={16} style={{ marginBottom: 24 }}>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <div style={{ textAlign: 'center' }}>
            <EditOutlined style={{ fontSize: 24, color: '#1890ff', marginBottom: 8 }} />
            <Statistic
              title="出题任务"
              value={problemCreationCompleted}
              suffix={`/ ${problemCreationTotal}`}
            />
            <Progress 
              percent={creationPercent} 
              size="small" 
              status={creationPercent >= 100 ? 'success' : 'active'}
              style={{ marginTop: 8 }}
            />
            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
              当前进度
            </Text>
          </div>
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <div style={{ textAlign: 'center' }}>
            <StarOutlined style={{ fontSize: 24, color: '#722ed1', marginBottom: 8 }} />
            <Statistic
              title="评分任务"
              value={problemReviewCompleted}
              suffix={`/ ${problemReviewTotal}`}
            />
            <Progress 
              percent={reviewPercent} 
              size="small" 
              strokeColor="#722ed1"
              status={reviewPercent >= 100 ? 'success' : 'active'}
              style={{ marginTop: 8 }}
            />
            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
              当前进度
            </Text>
          </div>
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <div style={{ textAlign: 'center' }}>
            <DollarOutlined style={{ fontSize: 24, color: '#52c41a', marginBottom: 8 }} />
            <Statistic
              title="出题奖励"
              value={config.rewardPerProblem}
              prefix="¥"
              suffix="元/题"
              valueStyle={{ color: '#52c41a' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              有所变动，以实际金额为准
            </Text>
          </div>
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <div style={{ textAlign: 'center' }}>
            <TrophyOutlined style={{ fontSize: 24, color: '#faad14', marginBottom: 8 }} />
            <Statistic
              title="评分奖励"
              value={config.rewardPerReview}
              prefix="¥"
              suffix="元/题"
              valueStyle={{ color: '#faad14' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              评分后立即发放
            </Text>
          </div>
        </Card>
      </Col>
    </Row>
  );
}


