/**
 * 认证相关 API
 */

import apiClient from './axios';
import { LoginResponse, User } from '../types';

export const authApi = {
  /**
   * 登录
   */
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await apiClient.post<LoginResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  /**
   * 获取当前用户信息
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  /**
   * 修改密码
   */
  changePassword: async (oldPassword: string, newPassword: string): Promise<void> => {
    await apiClient.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  /**
   * 登出
   */
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },

  /**
   * 管理员冒充用户
   */
  impersonate: async (targetUsername: string): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/impersonate', {
      target_username: targetUsername,
    });
    return response.data;
  },
};

