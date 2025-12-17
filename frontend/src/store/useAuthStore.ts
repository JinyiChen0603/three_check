/**
 * 认证状态管理（完整版 - 延迟加载 API）
 */

import { create } from 'zustand';

interface User {
  id: number;
  username: string;
  role: string;
  balance: number;
  problems_created_count: number;
  reviews_completed_count: number;
  is_active: boolean;
  is_impersonating: boolean;
  created_at: string;
  email?: string;
  last_login_at?: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  
  // Actions
  setAuth: (token: string, user: User) => void;
  clearAuth: () => void;
  updateUser: (user: User) => void;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
}

const TOKEN_KEY = 'mathtasks_token';
const USER_INFO_KEY = 'mathtasks_user';

export const useAuthStore = create<AuthState>((set, get) => ({
  token: (() => {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  })(),
  user: (() => {
    try {
      const userStr = localStorage.getItem(USER_INFO_KEY);
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  })(),
  isAuthenticated: (() => {
    try {
      return !!localStorage.getItem(TOKEN_KEY);
    } catch {
      return false;
    }
  })(),

  setAuth: (token, user) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(user));
    set({ token, user, isAuthenticated: true });
  },

  clearAuth: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_INFO_KEY);
    set({ token: null, user: null, isAuthenticated: false });
  },

  updateUser: (user) => {
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(user));
    set({ user });
  },

  login: async (username, password) => {
    // 动态导入 API 避免循环依赖
    const { authApi } = await import('../api');
    const response = await authApi.login(username, password);
    get().setAuth(response.access_token, response.user_info);
  },

  logout: async () => {
    try {
      // 动态导入 API 避免循环依赖
      const { authApi } = await import('../api');
      await authApi.logout();
    } catch (error) {
      console.error('Logout API failed:', error);
    } finally {
      get().clearAuth();
    }
  },

  fetchCurrentUser: async () => {
    // 动态导入 API 避免循环依赖
    const { authApi } = await import('../api');
    const user = await authApi.getCurrentUser();
    get().updateUser(user);
  },
}));
