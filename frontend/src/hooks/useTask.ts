/**
 * 任务管理Hook
 * 现在基于全局 TaskStore，避免重复请求
 */

import { useEffect } from 'react';
import type { Task } from '../types';
import { TaskType } from '../config/constants';
import { getCurrentTaskStats } from '../services/taskService';
import { useConfig } from './useConfig';
import { useTaskStore } from '../store/useTaskStore';

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
  abandonTask: (taskId: number, confirmed?: boolean) => Promise<any>;
  // 提交任务
  submitTask: (taskId: number) => Promise<void>;
}

export function useTask(): UseTaskReturn {
  const config = useConfig();  // 获取配置
  
  // 从全局 store 获取状态和方法
  const {
    tasks,
    loading,
    totalProblemsCreated,
    totalReviewsCompleted,
    refreshIfNeeded,
    fetchTasks,
    claimTasks,
    abandonTask,
    submitTask,
  } = useTaskStore();

  // 初始化时智能加载任务（使用缓存机制）
  useEffect(() => {
    refreshIfNeeded();
  }, []); // 空依赖，只在挂载时执行一次

  // 计算统计数据
  const problemCreationStats = getCurrentTaskStats(
    tasks, 
    TaskType.PROBLEM_CREATION, 
    totalProblemsCreated, 
    config.maxProblemsTotal
  );
  const problemReviewStats = getCurrentTaskStats(
    tasks, 
    TaskType.PROBLEM_REVIEW, 
    totalReviewsCompleted,
    config.maxProblemsTotal
  );

  return {
    tasks,
    loading,
    problemCreationTotal: problemCreationStats.total,
    problemCreationCompleted: problemCreationStats.completed,
    problemReviewTotal: problemReviewStats.total,
    problemReviewCompleted: problemReviewStats.completed,
    refreshTasks: fetchTasks,  // 提供强制刷新方法
    claimTasks,
    abandonTask,
    submitTask,
  };
}

