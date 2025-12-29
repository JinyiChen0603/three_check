/**
 * 任务管理Hook
 * 负责任务的状态管理、API调用和数据转换
 */

import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import type { Task, TaskBatchesResponse } from '../types';
import { TaskType } from '../config/constants';
import { taskApi } from '../api';
import { convertBatchesToTasks, getCurrentTaskStats } from '../services/taskService';
import { useConfig } from './useConfig';

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
  const config = useConfig();  // 获取配置
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalProblemsCreated, setTotalProblemsCreated] = useState(0);
  const [totalReviewsCompleted, setTotalReviewsCompleted] = useState(0);

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
        
        // 保存累计总数
        setTotalProblemsCreated(batchesResponse.total_problems_created || 0);
        setTotalReviewsCompleted(batchesResponse.total_reviews_completed || 0);
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
  const abandonTask = useCallback(async (taskId: number, confirmed: boolean = false) => {
    try {
      const response = await taskApi.abandonTask(taskId, confirmed);
      
      // 检查是否需要确认
      if (response.requires_confirmation) {
        // 返回需要确认的信息，由调用方处理
        return response;
      }
      
      // 已确认或无需确认，放弃成功
      const successMsg = response.deleted_problem_count > 0 
        ? `任务已放弃，已删除 ${response.deleted_problem_count} 道题目`
        : '任务已放弃';
      message.success(successMsg);
      
      // 放弃成功后刷新列表
      await fetchTasks();
      return response;
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
  // 使用新的逻辑：如果有进行中的任务显示当前任务进度，否则显示累计进度（从后端获取）
  const problemCreationStats = getCurrentTaskStats(
    tasks, 
    TaskType.PROBLEM_CREATION, 
    totalProblemsCreated, 
    config.maxProblemsTotal  // 从配置获取最大值
  );
  const problemReviewStats = getCurrentTaskStats(
    tasks, 
    TaskType.PROBLEM_REVIEW, 
    totalReviewsCompleted,
    config.maxProblemsTotal  // 从配置获取最大值
  );

  return {
    tasks,
    loading,
    problemCreationTotal: problemCreationStats.total,
    problemCreationCompleted: problemCreationStats.completed,
    problemReviewTotal: problemReviewStats.total,
    problemReviewCompleted: problemReviewStats.completed,
    refreshTasks: fetchTasks,
    claimTasks,
    abandonTask,
    submitTask,
  };
}

