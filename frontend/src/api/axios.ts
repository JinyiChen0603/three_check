/**
 * Axios 配置 - 三重质检工具
 */

import axios, { AxiosError } from 'axios';
import { message } from 'antd';

// API 基础URL
const API_BASE_URL = '/api';

// 创建 axios 实例
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 日志记录
apiClient.interceptors.request.use(
  (config: any) => {
    console.log('🔵 [API Request]', config.method?.toUpperCase(), config.url, {
      data: config.data,
    });
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
        case 404:
          message.error('请求的资源不存在');
          break;
        case 500:
          message.error('服务器错误，请稍后重试');
          break;
        default:
          // 显示后端返回的错误信息
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
      message.error('网络错误，请检查您的网络连接');
    } else {
      message.error('请求配置错误');
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
