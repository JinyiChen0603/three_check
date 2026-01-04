/**
 * 主布局组件
 */

import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout,
  Menu,
  Avatar,
  Dropdown,
  Typography,
  Space,
  Badge,
  Modal,
  message,
} from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  BookOutlined,
  UserOutlined,
  LogoutOutlined,
  LockOutlined,
  TeamOutlined,
  WalletOutlined,
  HistoryOutlined,
  FileExcelOutlined,
  FireOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../store/useAuthStore';
import { UserRole } from '../config/constants';
import './MainLayout.css';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    Modal.confirm({
      title: '确认退出',
      content: '确定要退出登录吗？',
      onOk: async () => {
        await logout();
        message.success('已退出登录');
        navigate('/login');
      },
    });
  };

  const handleChangePassword = () => {
    navigate('/change-password');
  };

  // 用户下拉菜单
  const userMenuItems = [
    {
      key: 'change-password',
      icon: <LockOutlined />,
      label: '修改密码',
      onClick: handleChangePassword,
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  // 侧边栏菜单
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/tasks',
      icon: <FileTextOutlined />,
      label: '任务管理',
    },
    // 以下页面已隐藏，但保留代码以便将来恢复
    // {
    //   key: '/problem',
    //   icon: <FileTextOutlined />,
    //   label: '出题流程',
    // },
    {
      key: '/totalpage',
      icon: <FileExcelOutlined />,
      label: '题目验证导出',
    },
    {
      key: '/variant-generator',
      icon: <FireOutlined />,
      label: '变体生成',
    },
    {
      key: '/review',
      icon: <CheckCircleOutlined />,
      label: '评分流程',
    },
    {
      key: '/review-history',
      icon: <HistoryOutlined />,
      label: '我的评分记录',
    },
    {
      key: '/materials',
      icon: <BookOutlined />,
      label: '资料库',
    },
    // 管理员专属菜单
    ...(user?.role === UserRole.ADMIN
      ? [
          {
            key: '/admin',
            icon: <TeamOutlined />,
            label: '用户管理',
          },
          {
            key: '/admin/problem-review',
            icon: <CheckCircleOutlined />,
            label: '题目审核',
          },
        ]
      : []),
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={setCollapsed}
        theme="light"
        width={220}
      >
        <div className="logo">
          <FileTextOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          {!collapsed && <span>MathTasks</span>}
        </div>
        
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>

      <Layout>
        {/* 顶部栏 */}
        <Header className="main-header">
          <div className="header-left">
            <Space size="large">
              {user?.is_impersonating && (
                <Badge.Ribbon text="冒充模式" color="red">
                  <div style={{ padding: '4px 12px', background: '#fff', borderRadius: 4 }}>
                    <Text type="warning">当前以访客身份查看</Text>
                  </div>
                </Badge.Ribbon>
              )}
            </Space>
          </div>

          <div className="header-right">
            <Space size="large">
              {/* 收入显示 */}
              <Space>
                <WalletOutlined style={{ fontSize: 18 }} />
                <Text strong>收入：</Text>
                <Text type="success" strong style={{ fontSize: 16 }}>
                  ¥{user?.balance.toFixed(2)}
                </Text>
              </Space>

              {/* 用户信息 */}
              <Dropdown 
                menu={{ items: userMenuItems as any }} 
                placement="bottomRight"
              >
                <Space style={{ cursor: 'pointer' }}>
                  <Avatar icon={<UserOutlined />} />
                  <div>
                    <div>
                      <Text strong>{user?.username}</Text>
                      {user?.role === UserRole.ADMIN && (
                        <Badge 
                          count="管理员" 
                          style={{ 
                            backgroundColor: '#52c41a', 
                            marginLeft: 8 
                          }} 
                        />
                      )}
                    </div>
                  </div>
                </Space>
              </Dropdown>
            </Space>
          </div>
        </Header>

        {/* 主内容区 */}
        <Content className="main-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

