/**
 * 管理员功能页面（简化版 - 静态数据）
 */

import { useState } from 'react';
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
  TeamOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/useAuthStore';
import axios from 'axios';

const { Title, Text } = Typography;
const { Search } = Input;

// 静态用户数据
const mockUsers = [
  {
    id: 1,
    username: 'lifanghe',
    email: 'lifanghe@mathtasks.com',
    role: 'admin',
    balance: 0,
    problems_created_count: 0,
    reviews_completed_count: 0,
    is_active: true,
  },
  {
    id: 2,
    username: 'gexinlin',
    email: 'gexinlin@mathtasks.com',
    role: 'admin',
    balance: 0,
    problems_created_count: 0,
    reviews_completed_count: 0,
    is_active: true,
  },
  {
    id: 3,
    username: 'hewenze',
    email: 'hewenze@mathtasks.com',
    role: 'user',
    balance: 210,
    problems_created_count: 5,
    reviews_completed_count: 12,
    is_active: true,
  },
  {
    id: 4,
    username: 'chenjinyi',
    email: 'chenjinyi@mathtasks.com',
    role: 'user',
    balance: 294,
    problems_created_count: 8,
    reviews_completed_count: 6,
    is_active: true,
  },
];

export default function AdminSimple() {
  const navigate = useNavigate();
  const { user: currentUser, setAuth } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [users] = useState(mockUsers);
  const [searchText, setSearchText] = useState('');

  // 检查权限
  if (currentUser?.role !== 'admin') {
    return (
      <Card>
        <Text type="danger">您没有权限访问此页面</Text>
      </Card>
    );
  }

  const handleImpersonate = (targetUser: any) => {
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
        setLoading(true);
        try {
          // 调用后端 API
          const response = await axios.post(
            'http://localhost:8001/api/auth/impersonate',
            { target_username: targetUser.username },
            {
              headers: {
                'Authorization': `Bearer ${currentUser?.id}`, // 这里应该用真实的token
                'Content-Type': 'application/json',
              },
            }
          );
          
          setAuth(response.data.access_token, response.data.user_info);
          message.success(`已切换到 ${targetUser.username} 的视角`);
          navigate('/dashboard');
        } catch (error: any) {
          console.error('冒充失败:', error);
          message.error(error.response?.data?.detail || '切换失败');
        } finally {
          setLoading(false);
        }
      },
    });
  };

  const columns = [
    {
      title: '用户',
      key: 'user',
      render: (_: any, user: any) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div>
              <Text strong>{user.username}</Text>
              {user.role === 'admin' && (
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
      sorter: (a: any, b: any) => a.balance - b.balance,
    },
    {
      title: '出题数',
      dataIndex: 'problems_created_count',
      key: 'problems_created_count',
      sorter: (a: any, b: any) =>
        a.problems_created_count - b.problems_created_count,
    },
    {
      title: '评分数',
      dataIndex: 'reviews_completed_count',
      key: 'reviews_completed_count',
      sorter: (a: any, b: any) =>
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
      render: (_: any, user: any) => (
        <Space>
          {user.role !== 'admin' && (
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => handleImpersonate(user)}
              loading={loading}
            >
              冒充
            </Button>
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
  const adminUsers = users.filter((u) => u.role === 'admin').length;
  const normalUsers = users.filter((u) => u.role === 'user').length;
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

