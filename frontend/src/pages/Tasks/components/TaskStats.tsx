import { Card, Col, Row, Statistic } from 'antd';
import { CheckCircleOutlined, FileTextOutlined } from '@ant-design/icons';

import { BUSINESS_CONSTANTS } from '../../../config/constants';

export function TaskStats({
  problemCreationTotal,
  problemReviewTotal,
}: {
  problemCreationTotal: number;
  problemReviewTotal: number;
}) {
  return (
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
  );
}


