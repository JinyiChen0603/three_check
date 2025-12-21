import { Card, Col, Row, Statistic } from 'antd';
import { TeamOutlined } from '@ant-design/icons';

export function UserStats({
  totalUsers,
  adminUsers,
  normalUsers,
  activeUsers,
}: {
  totalUsers: number;
  adminUsers: number;
  normalUsers: number;
  activeUsers: number;
}) {
  return (
    <Row gutter={16} style={{ marginBottom: 24 }}>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic title="总用户数" value={totalUsers} prefix={<TeamOutlined />} />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic title="管理员" value={adminUsers} valueStyle={{ color: '#cf1322' }} />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic title="普通用户" value={normalUsers} valueStyle={{ color: '#3f8600' }} />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic title="活跃用户" value={activeUsers} suffix={`/ ${totalUsers}`} />
        </Card>
      </Col>
    </Row>
  );
}


