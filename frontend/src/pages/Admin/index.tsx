/**
 * 管理员功能页面
 */

import { Card, Input, Space, Typography } from 'antd';
import { TeamOutlined } from '@ant-design/icons';

import { useUserManagement } from './hooks/useUserManagement';
import { UserStats } from './components/UserStats';
import { UserTable } from './components/UserTable';
import { ImpersonateModal } from './components/ImpersonateModal';

const { Title, Text } = Typography;
const { Search } = Input;

export default function Admin() {
  const um = useUserManagement();

  return (
    <div>
      <Title level={2}>
        <TeamOutlined /> 用户管理
      </Title>

      {/* 统计卡片 */}
      <UserStats
        totalUsers={um.stats.totalUsers}
        adminUsers={um.stats.adminUsers}
        normalUsers={um.stats.normalUsers}
        activeUsers={um.stats.activeUsers}
      />

      {/* 用户列表 */}
      <Card>
        <Space orientation="vertical" style={{ width: '100%' }} size="large">
          <Search
            placeholder="搜索用户名或邮箱"
            allowClear
            onSearch={um.setSearchText}
            onChange={(e) => um.setSearchText(e.target.value)}
            style={{ width: 300 }}
          />

          <UserTable
            users={um.filteredUsers}
            loading={um.loading}
            onImpersonate={um.openImpersonate}
            onToggleActive={um.handleToggleActive}
          />
        </Space>
      </Card>

      <ImpersonateModal
        open={um.impersonateOpen}
        targetUser={um.impersonateTarget}
        onOk={um.confirmImpersonate}
        onCancel={um.closeImpersonate}
      />
    </div>
  );
}

