/**
 * Axios 配置和拦截器
 */

import axios, { AxiosError } from 'axios';
import { message } from 'antd';
import { API_BASE_URL, TOKEN_KEY } from '../config/constants';

// 创建 axios 实例
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  //timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加 Token
apiClient.interceptors.request.use(
  (config: any) => {
    const token = localStorage.getItem(TOKEN_KEY);
    console.log('🔵 [API Request]', config.method?.toUpperCase(), config.url, {
      hasToken: !!token,
      data: config.data,
    });
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    console.error('❌ [API Request Error]', error);
    return Promise.reject(error);
  }
);

// 响应拦截器 - 统一错误处理
apiClient.interceptors.response.use(
  (response) => {
    console.log('✅ [API Response]', response.config.method?.toUpperCase(), response.config.url, {
      status: response.status,
      data: response.data,
    });
    return response;
  },
  (error: AxiosError<any>) => {
    console.error('❌ [API Error]', error.config?.method?.toUpperCase(), error.config?.url, {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message,
    });
    // 处理HTTP错误
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 401:
          // 登录接口的 401 表示用户名密码错误，不跳转
          if (error.config?.url?.includes('/auth/login')) {
            // 不做处理，让调用方捕获错误并显示提示
            break;
          }
          // 其他接口的 401 表示 token 过期
          localStorage.removeItem(TOKEN_KEY);
          message.error('登录已过期，请重新登录');
          window.location.href = '/login';
          break;
        case 403:
          message.error('没有权限访问此资源');
          break;
        case 404:
          message.error('请求的资源不存在');
          break;
        case 500:
          message.error('服务器错误，请稍后重试');
          break;
        default:
          // 显示后端返回的错误信息
          // 处理验证错误（422）和其他错误格式
          let errorMsg = '请求失败';
          
          if (data?.detail) {
            // 如果是数组（FastAPI验证错误格式）
            if (Array.isArray(data.detail)) {
              errorMsg = data.detail.map((err: any) => {
                if (typeof err === 'string') return err;
                if (err.msg) return err.msg;
                if (err.message) return err.message;
                return JSON.stringify(err);
              }).join(', ');
            } 
            // 如果是字符串
            else if (typeof data.detail === 'string') {
              errorMsg = data.detail;
            }
            // 如果是对象，尝试提取消息
            else if (typeof data.detail === 'object') {
              errorMsg = data.detail.msg || data.detail.message || JSON.stringify(data.detail);
            }
          } else if (data?.message) {
            errorMsg = data.message;
          }
          
          message.error(errorMsg);
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      message.error('网络错误，请检查您的网络连接');
    } else {
      // 请求配置出错
      message.error('请求配置错误');
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;

