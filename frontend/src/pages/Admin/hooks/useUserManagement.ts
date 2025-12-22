import { useCallback, useEffect, useMemo, useState } from 'react';
import { message } from 'antd';
import { useNavigate } from 'react-router-dom';

import { authApi } from '../../../api';
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
      // TODO: 后端用户列表 API 就绪后替换
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


