import { useCallback, useEffect, useMemo, useState } from 'react';
import { message } from 'antd';
import { useNavigate } from 'react-router-dom';

import { authApi, userApi } from '../../../api';
import type { User } from '../../../types';
import { UserRole } from '../../../types';
import { useAuthStore } from '../../../store/useAuthStore';

export function useUserManagement() {
  const navigate = useNavigate();
  const { user: currentUser, setAuth } = useAuthStore();

  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [searchText, setSearchText] = useState('');

  const [impersonateOpen, setImpersonateOpen] = useState(false);
  const [impersonateTarget, setImpersonateTarget] = useState<User | null>(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const response = await userApi.getUserList(0, 1000);
      const userList = response.users.map((u: any) => ({
        id: u.id,
        username: u.username,
        email: u.email || '',
        role: u.role === 'admin' ? UserRole.ADMIN : UserRole.USER,
        balance: u.balance,
        problems_created_count: u.problems_created_count,
        reviews_completed_count: u.reviews_completed_count,
        is_active: u.is_active,
        is_impersonating: false,
        created_at: u.created_at,
      }));
      setUsers(userList);
    } catch (error) {
      message.error('加载用户列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  // 权限 + 初始化加载
  useEffect(() => {
    if (currentUser?.role !== UserRole.ADMIN) {
      message.error('您没有权限访问此页面');
      navigate('/dashboard');
      return;
    }
    fetchUsers();
  }, [currentUser, fetchUsers, navigate]);

  const openImpersonate = useCallback((targetUser: User) => {
    setImpersonateTarget(targetUser);
    setImpersonateOpen(true);
  }, []);

  const closeImpersonate = useCallback(() => {
    setImpersonateOpen(false);
    setImpersonateTarget(null);
  }, []);

  const confirmImpersonate = useCallback(async () => {
    if (!impersonateTarget) return;
    try {
      const response = await authApi.impersonate(impersonateTarget.username);
      setAuth(response.access_token, response.user_info);
      message.success(`已切换到 ${impersonateTarget.username} 的视角`);
      closeImpersonate();
      navigate('/dashboard');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '切换失败');
    }
  }, [closeImpersonate, impersonateTarget, navigate, setAuth]);

  const handleToggleActive = useCallback(async (_user: User) => {
    message.info('此功能需要后端 API 支持');
    // TODO: await userApi.toggleUserStatus(user.id, !user.is_active);
    // await fetchUsers();
  }, []);

  const filteredUsers = useMemo(() => {
    const q = searchText.toLowerCase();
    return users.filter(
      (user) =>
        user.username.toLowerCase().includes(q) || user.email?.toLowerCase().includes(q)
    );
  }, [searchText, users]);

  const stats = useMemo(() => {
    const totalUsers = users.length;
    const adminUsers = users.filter((u) => u.role === UserRole.ADMIN).length;
    const normalUsers = users.filter((u) => u.role === UserRole.USER).length;
    const activeUsers = users.filter((u) => u.is_active).length;
    return { totalUsers, adminUsers, normalUsers, activeUsers };
  }, [users]);

  return {
    loading,
    users,
    searchText,
    setSearchText,
    filteredUsers,
    stats,
    openImpersonate,
    impersonateOpen,
    impersonateTarget,
    closeImpersonate,
    confirmImpersonate,
    handleToggleActive,
  };
}


