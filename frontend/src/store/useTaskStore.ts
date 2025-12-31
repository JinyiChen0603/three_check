/**
 * 任务状态管理
 * 支持跨页面保持状态，避免重复请求
 */

import { create } from 'zustand';
import { message } from 'antd';
import type { Task, TaskBatchesResponse } from '../types';
import { TaskType } from '../config/constants';
import { taskApi } from '../api';
import { convertBatchesToTasks} from '../services/taskService';

interface TaskState {
  // 任务列表
  tasks: Task[];
  // 加载状态
  loading: boolean;
  // 出题任务累计总数
  totalProblemsCreated: number;
  // 评分任务累计总数
  totalReviewsCompleted: number;
  // 最后一次请求时间（用于缓存）
  lastFetchTime: number;
  // 是否已初始化
  initialized: boolean;
  
  // Actions
  fetchTasks: () => Promise<void>;
  refreshIfNeeded: (force?: boolean) => Promise<void>;
  claimTasks: (taskType: TaskType, count: number) => Promise<void>;
  abandonTask: (taskId: number, confirmed?: boolean) => Promise<any>;
  submitTask: (taskId: number) => Promise<void>;
}

const CACHE_DURATION = 3000; // 3秒缓存时间，避免频繁请求

export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: [],
  loading: false,
  totalProblemsCreated: 0,
  totalReviewsCompleted: 0,
  lastFetchTime: 0,
  initialized: false,

  // 获取任务列表
  fetchTasks: async () => {
    set({ loading: true });
    try {
      const response = await taskApi.getMyTasks();
      
      console.log('[TaskStore] API返回数据:', response);
      
      // 后端返回的是批次格式，需要转换
      if (response && typeof response === 'object' && 'batches' in response) {
        const batchesResponse = response as unknown as TaskBatchesResponse;
        const convertedTasks = convertBatchesToTasks(batchesResponse);
        
        set({
          tasks: convertedTasks,
          totalProblemsCreated: batchesResponse.total_problems_created || 0,
          totalReviewsCompleted: batchesResponse.total_reviews_completed || 0,
          lastFetchTime: Date.now(),
          initialized: true,
        });
      } else if (Array.isArray(response)) {
        set({
          tasks: response as Task[],
          lastFetchTime: Date.now(),
          initialized: true,
        });
      } else {
        console.warn('[TaskStore] 未知的数据格式:', response);
        set({
          tasks: [],
          lastFetchTime: Date.now(),
          initialized: true,
        });
      }
    } catch (error: any) {
      console.error('[TaskStore] 获取任务列表失败:', error);
      message.error(error.response?.data?.detail || '加载任务失败');
      set({ 
        tasks: [],
        initialized: true,
      });
    } finally {
      set({ loading: false });
    }
  },

  // 智能刷新：只在需要时才刷新
  refreshIfNeeded: async (force = false) => {
    const { lastFetchTime, loading, initialized } = get();
    
    // 如果正在加载，跳过
    if (loading) {
      console.log('[TaskStore] 正在加载中，跳过刷新');
      return;
    }
    
    // 如果强制刷新或未初始化
    if (force || !initialized) {
      console.log('[TaskStore] 强制刷新或首次加载');
      await get().fetchTasks();
      return;
    }
    
    // 检查缓存时间
    const timeSinceLastFetch = Date.now() - lastFetchTime;
    if (timeSinceLastFetch < CACHE_DURATION) {
      console.log(`[TaskStore] 使用缓存数据（${Math.round(timeSinceLastFetch / 1000)}秒前）`);
      return;
    }
    
    // 缓存过期，重新获取
    console.log('[TaskStore] 缓存过期，重新获取');
    await get().fetchTasks();
  },

  // 领取任务
  claimTasks: async (taskType: TaskType, count: number) => {
    try {
      const taskTypeStr = taskType === TaskType.PROBLEM_CREATION ? 'create_problem' : 'review_problem';
      
      console.log('[TaskStore] 开始领取任务:', { taskTypeStr, count });
      const response = await taskApi.claimTasks(taskTypeStr, count);
      console.log('[TaskStore] 领取任务响应:', response);
      
      message.success(`成功领取 ${count} 个任务！`);
      
      // 领取成功后刷新列表（强制刷新）
      await new Promise(resolve => setTimeout(resolve, 500));
      await get().fetchTasks();
    } catch (error: any) {
      console.error('[TaskStore] 领取任务失败:', error);
      throw error;
    }
  },

  // 放弃任务
  abandonTask: async (taskId: number, confirmed: boolean = false) => {
    try {
      const response = await taskApi.abandonTask(taskId, confirmed);
      
      // 检查是否需要确认
      if (response.requires_confirmation) {
        return response;
      }
      
      const successMsg = response.deleted_problem_count > 0 
        ? `任务已放弃，已删除 ${response.deleted_problem_count} 道题目`
        : '任务已放弃';
      message.success(successMsg);
      
      // 放弃成功后刷新列表（强制刷新）
      await get().fetchTasks();
      return response;
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || '放弃任务失败';
      message.error(errorMsg);
      throw error;
    }
  },

  // 提交任务
  submitTask: async (taskId: number) => {
    try {
      await taskApi.submitTask(taskId);
      message.success('任务提交成功');
      
      // 提交成功后刷新列表（强制刷新）
      await get().fetchTasks();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || '提交任务失败';
      message.error(errorMsg);
      throw error;
    }
  },
}));

