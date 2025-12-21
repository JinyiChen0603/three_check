/**
 * 任务管理Hook
 * 负责任务的状态管理、API调用和数据转换
 */

import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import type { Task, TaskBatchesResponse } from '../types';
import { TaskType } from '../config/constants';
import { taskApi } from '../api';
import { convertBatchesToTasks, calculateTotalTaskCount, calculateCompletedTaskCount } from '../services/taskService';

interface UseTaskReturn {
  // 任务列表
  tasks: Task[];
  // 加载状态
  loading: boolean;
  // 出题任务总数
  problemCreationTotal: number;
  // 出题任务已完成数
  problemCreationCompleted: number;
  // 评分任务总数
  problemReviewTotal: number;
  // 评分任务已完成数
  problemReviewCompleted: number;
  // 刷新任务列表
  refreshTasks: () => Promise<void>;
  // 领取任务
  claimTasks: (taskType: TaskType, count: number) => Promise<void>;
  // 放弃任务
  abandonTask: (taskId: number) => Promise<void>;
  // 提交任务
  submitTask: (taskId: number) => Promise<void>;
}

export function useTask(): UseTaskReturn {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);

  // 获取任务列表
  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      // 调用修复后的API
      const response = await taskApi.getMyTasks();
      
      console.log('API返回数据:', response);
      
      // 后端返回的是批次格式，需要转换
      if (response && typeof response === 'object' && 'batches' in response) {
        const batchesResponse = response as unknown as TaskBatchesResponse;
        console.log('批次数据:', batchesResponse);
        const convertedTasks = convertBatchesToTasks(batchesResponse);
        console.log('转换后的任务:', convertedTasks);
        setTasks(convertedTasks);
      } else if (Array.isArray(response)) {
        // 如果返回的是数组格式（兼容处理）
        console.log('数组格式数据:', response);
        setTasks(response as Task[]);
      } else {
        console.warn('未知的数据格式:', response);
        setTasks([]);
      }
    } catch (error: any) {
      console.error('获取任务列表失败:', error);
      console.error('错误详情:', error.response?.data);
      message.error(error.response?.data?.detail || '加载任务失败');
      setTasks([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // 领取任务
  const claimTasks = useCallback(async (taskType: TaskType, count: number) => {
    try {
      // 转换任务类型格式：前端枚举 -> 后端API格式
      const taskTypeStr = taskType === TaskType.PROBLEM_CREATION ? 'create_problem' : 'review_problem';
      
      console.log('开始领取任务:', { taskTypeStr, count });
      const response = await taskApi.claimTasks(taskTypeStr, count);
      console.log('领取任务响应:', response);
      
      // 使用 setTimeout 确保在 effect 中调用，避免 React 18 并发模式警告
      setTimeout(() => {
        message.success(`成功领取 ${count} 个任务！`);
      }, 0);
      
      // 领取成功后刷新列表（等待一小段时间确保数据库已更新）
      await new Promise(resolve => setTimeout(resolve, 500));
      await fetchTasks();
      console.log('任务列表已刷新');
    } catch (error: any) {
      console.error('领取任务失败:', error);
      // 错误消息已在API拦截器中显示，这里只抛出错误
      throw error;
    }
  }, [fetchTasks]);

  // 放弃任务
  const abandonTask = useCallback(async (taskId: number) => {
    try {
      await taskApi.abandonTask(taskId);
      message.success('已放弃任务');
      
      // 放弃成功后刷新列表
      await fetchTasks();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || '放弃任务失败';
      message.error(errorMsg);
      throw error;
    }
  }, [fetchTasks]);

  // 提交任务
  const submitTask = useCallback(async (taskId: number) => {
    try {
      await taskApi.submitTask(taskId);
      message.success('任务提交成功');
      
      // 提交成功后刷新列表
      await fetchTasks();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || '提交任务失败';
      message.error(errorMsg);
      throw error;
    }
  }, [fetchTasks]);

  // 初始化时加载任务
  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  // 计算统计数据
  const problemCreationTotal = calculateTotalTaskCount(tasks, TaskType.PROBLEM_CREATION);
  const problemCreationCompleted = calculateCompletedTaskCount(tasks, TaskType.PROBLEM_CREATION);
  const problemReviewTotal = calculateTotalTaskCount(tasks, TaskType.PROBLEM_REVIEW);
  const problemReviewCompleted = calculateCompletedTaskCount(tasks, TaskType.PROBLEM_REVIEW);

  return {
    tasks,
    loading,
    problemCreationTotal,
    problemCreationCompleted,
    problemReviewTotal,
    problemReviewCompleted,
    refreshTasks: fetchTasks,
    claimTasks,
    abandonTask,
    submitTask,
  };
}

