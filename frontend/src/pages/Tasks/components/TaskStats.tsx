import { Card, Col, Row, Statistic, Progress, Typography } from 'antd';
import { EditOutlined, StarOutlined, DollarOutlined, TrophyOutlined } from '@ant-design/icons';

import { BUSINESS_CONSTANTS } from '../../../config/constants';

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
  const creationPercent = problemCreationTotal > 0 
    ? Math.round((problemCreationCompleted / problemCreationTotal) * 100) 
    : 0;
  const reviewPercent = problemReviewTotal > 0 
    ? Math.round((problemReviewCompleted / problemReviewTotal) * 100) 
    : 0;

  // 是否有进行中的任务
  const hasCreationTask = problemCreationTotal > 0;
  const hasReviewTask = problemReviewTotal > 0;

  return (
    <Row gutter={16} style={{ marginBottom: 24 }}>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <div style={{ textAlign: 'center' }}>
            <EditOutlined style={{ fontSize: 24, color: '#1890ff', marginBottom: 8 }} />
            {hasCreationTask ? (
              // 已领取任务：显示进度
              <>
                <Statistic
                  title="出题任务进度"
                  value={problemCreationCompleted}
                  suffix={`/ ${problemCreationTotal}`}
                />
                <Progress 
                  percent={creationPercent} 
                  size="small" 
                  status={creationPercent >= 100 ? 'success' : 'active'}
                  style={{ marginTop: 8 }}
                />
              </>
            ) : (
              // 未领取任务：显示可领取数量
              <>
                <Statistic
                  title="出题任务"
                  value={0}
                  suffix={`/ ${BUSINESS_CONSTANTS.MAX_TASKS_PER_CLAIM}`}
                />
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
                  单次最多领取 {BUSINESS_CONSTANTS.MAX_TASKS_PER_CLAIM} 个
                </Text>
              </>
            )}
          </div>
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <div style={{ textAlign: 'center' }}>
            <StarOutlined style={{ fontSize: 24, color: '#722ed1', marginBottom: 8 }} />
            {hasReviewTask ? (
              // 已领取任务：显示进度
              <>
                <Statistic
                  title="评分任务进度"
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
              </>
            ) : (
              // 未领取任务：显示可领取数量
              <>
                <Statistic
                  title="评分任务"
                  value={0}
                  suffix={`/ ${BUSINESS_CONSTANTS.MAX_TASKS_PER_CLAIM}`}
                />
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
                  单次最多领取 {BUSINESS_CONSTANTS.MAX_TASKS_PER_CLAIM} 个
                </Text>
              </>
            )}
          </div>
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <div style={{ textAlign: 'center' }}>
            <DollarOutlined style={{ fontSize: 24, color: '#52c41a', marginBottom: 8 }} />
            <Statistic
              title="出题奖励"
              value={BUSINESS_CONSTANTS.REWARD_PER_PROBLEM}
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
              value={BUSINESS_CONSTANTS.REWARD_PER_REVIEW}
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


