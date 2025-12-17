/**
 * 管理员功能页面
 */

import { useEffect, useState } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Input,
  message,
  Typography,
  Statistic,
  Row,
  Col,
  Avatar,
} from 'antd';
import {
  UserOutlined,
  EyeOutlined,
  LockOutlined,
  UnlockOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { User, UserRole } from '../../types';
import { authApi, userApi } from '../../api';
import { useAuthStore } from '../../store/useAuthStore';

const { Title, Text } = Typography;
const { Search } = Input;

export default function Admin() {
  const navigate = useNavigate();
  const { user: currentUser, setAuth } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [searchText, setSearchText] = useState('');

  // 检查权限
  useEffect(() => {
    if (currentUser?.role !== UserRole.ADMIN) {
      message.error('您没有权限访问此页面');
      navigate('/dashboard');
      return;
    }
    fetchUsers();
  }, [currentUser, navigate]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      // 这里暂时模拟数据，实际需要后端提供用户列表API
      const mockUsers: User[] = [
        {
          id: 1,
          username: 'lifanghe',
          email: 'lifanghe@mathtasks.com',
          role: UserRole.ADMIN,
          balance: 0,
          problems_created_count: 0,
          reviews_completed_count: 0,
          is_active: true,
          is_impersonating: false,
          created_at: '2025-12-17T10:00:00',
        },
        {
          id: 2,
          username: 'gexinlin',
          email: 'gexinlin@mathtasks.com',
          role: UserRole.ADMIN,
          balance: 0,
          problems_created_count: 0,
          reviews_completed_count: 0,
          is_active: true,
          is_impersonating: false,
          created_at: '2025-12-17T10:00:00',
        },
        {
          id: 3,
          username: 'hewenze',
          email: 'hewenze@mathtasks.com',
          role: UserRole.USER,
          balance: 210,
          problems_created_count: 5,
          reviews_completed_count: 12,
          is_active: true,
          is_impersonating: false,
          created_at: '2025-12-17T10:00:00',
        },
        {
          id: 4,
          username: 'chenjinyi',
          email: 'chenjinyi@mathtasks.com',
          role: UserRole.USER,
          balance: 294,
          problems_created_count: 8,
          reviews_completed_count: 6,
          is_active: true,
          is_impersonating: false,
          created_at: '2025-12-17T10:00:00',
        },
      ];
      setUsers(mockUsers);
    } catch (error) {
      message.error('加载用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleImpersonate = (targetUser: User) => {
    Modal.confirm({
      title: '确认冒充用户',
      content: (
        <div>
          <p>您将以访客模式查看用户 <Text strong>{targetUser.username}</Text> 的视角</p>
          <p>在冒充模式下，您可以：</p>
          <ul>
            <li>查看该用户的所有信息</li>
            <li>以该用户身份浏览系统</li>
          </ul>
          <p style={{ color: '#ff4d4f', marginTop: 16 }}>
            ⚠️ 注意：您仍然是管理员身份，不能代替用户执行操作
          </p>
        </div>
      ),
      okText: '确认切换',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await authApi.impersonate(targetUser.username);
          setAuth(response.access_token, response.user_info);
          message.success(`已切换到 ${targetUser.username} 的视角`);
          navigate('/dashboard');
        } catch (error: any) {
          message.error(error.response?.data?.detail || '切换失败');
        }
      },
    });
  };

  const handleToggleActive = (user: User) => {
    Modal.confirm({
      title: user.is_active ? '禁用用户' : '启用用户',
      content: `确定要${user.is_active ? '禁用' : '启用'}用户 ${user.username} 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        message.info('此功能需要后端 API 支持');
        // TODO: 调用后端 API
        // await userApi.toggleUserStatus(user.id, !user.is_active);
        // fetchUsers();
      },
    });
  };

  const columns = [
    {
      title: '用户',
      key: 'user',
      render: (_: any, user: User) => (
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
      sorter: (a: User, b: User) => a.balance - b.balance,
    },
    {
      title: '出题数',
      dataIndex: 'problems_created_count',
      key: 'problems_created_count',
      sorter: (a: User, b: User) =>
        a.problems_created_count - b.problems_created_count,
    },
    {
      title: '评分数',
      dataIndex: 'reviews_completed_count',
      key: 'reviews_completed_count',
      sorter: (a: User, b: User) =>
        a.reviews_completed_count - b.reviews_completed_count,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'error'}>
          {isActive ? '正常' : '已禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, user: User) => (
        <Space>
          {user.role !== UserRole.ADMIN && (
            <>
              <Button
                type="link"
                icon={<EyeOutlined />}
                onClick={() => handleImpersonate(user)}
              >
                冒充
              </Button>
              <Button
                type="link"
                danger={user.is_active}
                icon={user.is_active ? <LockOutlined /> : <UnlockOutlined />}
                onClick={() => handleToggleActive(user)}
              >
                {user.is_active ? '禁用' : '启用'}
              </Button>
            </>
          )}
        </Space>
      ),
    },
  ];

  // 过滤用户
  const filteredUsers = users.filter((user) =>
    user.username.toLowerCase().includes(searchText.toLowerCase()) ||
    user.email?.toLowerCase().includes(searchText.toLowerCase())
  );

  // 统计数据
  const totalUsers = users.length;
  const adminUsers = users.filter((u) => u.role === UserRole.ADMIN).length;
  const normalUsers = users.filter((u) => u.role === UserRole.USER).length;
  const activeUsers = users.filter((u) => u.is_active).length;

  return (
    <div>
      <Title level={2}>
        <TeamOutlined /> 用户管理
      </Title>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总用户数"
              value={totalUsers}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="管理员"
              value={adminUsers}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="普通用户"
              value={normalUsers}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={activeUsers}
              suffix={`/ ${totalUsers}`}
            />
          </Card>
        </Col>
      </Row>

      {/* 用户列表 */}
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Search
            placeholder="搜索用户名或邮箱"
            allowClear
            onSearch={setSearchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
          />

          <Table
            columns={columns}
            dataSource={filteredUsers}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
          />
        </Space>
      </Card>
    </div>
  );
}

