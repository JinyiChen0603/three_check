import { Avatar, Button, Space, Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { EyeOutlined, LockOutlined, UnlockOutlined, UserOutlined } from '@ant-design/icons';

import type { User } from '../../../types';
import { UserRole } from '../../../types';

const { Text } = Typography;

export function UserTable({
  users,
  loading,
  onImpersonate,
  onToggleActive,
}: {
  users: User[];
  loading: boolean;
  onImpersonate: (user: User) => void;
  onToggleActive: (user: User) => void;
}) {
  const columns: ColumnsType<User> = [
    {
      title: '用户',
      key: 'user',
      render: (_, user) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div>
              <Text strong>{user.username}</Text>
              {user.role === UserRole.ADMIN && (
                <Tag color="red" style={{ marginLeft: 8 }}>
                  管理员
                </Tag>
              )}
            </div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {user.email}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: '余额',
      dataIndex: 'balance',
      key: 'balance',
      render: (balance: number) => `¥${balance.toFixed(2)}`,
      sorter: (a, b) => a.balance - b.balance,
    },
    {
      title: '出题数',
      dataIndex: 'problems_created_count',
      key: 'problems_created_count',
      sorter: (a, b) => a.problems_created_count - b.problems_created_count,
    },
    {
      title: '评分数',
      dataIndex: 'reviews_completed_count',
      key: 'reviews_completed_count',
      sorter: (a, b) => a.reviews_completed_count - b.reviews_completed_count,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'error'}>{isActive ? '正常' : '已禁用'}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, user) => (
        <Space>
          {user.role !== UserRole.ADMIN && (
            <>
              <Button type="link" icon={<EyeOutlined />} onClick={() => onImpersonate(user)}>
                冒充
              </Button>
              <Button
                type="link"
                danger={user.is_active}
                icon={user.is_active ? <LockOutlined /> : <UnlockOutlined />}
                onClick={() => onToggleActive(user)}
              >
                {user.is_active ? '禁用' : '启用'}
              </Button>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Table columns={columns} dataSource={users} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
  );
}


