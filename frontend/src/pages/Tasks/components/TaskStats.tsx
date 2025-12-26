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
  
  // 0/50页面：始终显示已提交的题目总数/配置的最大任务数（从后端获取）
  const creationPercent = Math.round((problemCreationCompleted / config.maxTasksPerClaim) * 100);
  const reviewPercent = Math.round((problemReviewCompleted / config.maxTasksPerClaim) * 100);

  return (
    <Row gutter={16} style={{ marginBottom: 24 }}>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <div style={{ textAlign: 'center' }}>
            <EditOutlined style={{ fontSize: 24, color: '#1890ff', marginBottom: 8 }} />
            <Statistic
              title="出题任务"
              value={problemCreationCompleted}
              suffix={`/ ${config.maxTasksPerClaim}`}
            />
            <Progress 
              percent={creationPercent} 
              size="small" 
              status={creationPercent >= 100 ? 'success' : 'active'}
              style={{ marginTop: 8 }}
            />
            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
              已提交题目数
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
              suffix={`/ ${config.maxTasksPerClaim}`}
            />
            <Progress 
              percent={reviewPercent} 
              size="small" 
              strokeColor="#722ed1"
              status={reviewPercent >= 100 ? 'success' : 'active'}
              style={{ marginTop: 8 }}
            />
            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
              已提交题目数
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
              通过审核后发放
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


