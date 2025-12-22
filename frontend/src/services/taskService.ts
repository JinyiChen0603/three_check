/**
 * 任务数据处理服务
 * 负责将后端返回的批次数据转换为前端需要的格式
 */

import type { Task, TaskBatch, TaskBatchesResponse } from '../types';
import { TaskType, TaskStatus } from '../config/constants';

/**
 * 将后端返回的批次数据转换为前端Task数组
 */
export function convertBatchesToTasks(batchesResponse: TaskBatchesResponse): Task[] {
  const tasks: Task[] = [];
  
  batchesResponse.batches.forEach((batch: TaskBatch) => {
    // 转换任务类型：后端格式 -> 前端枚举
    const taskType = batch.task_type === 'create_problem' 
      ? TaskType.PROBLEM_CREATION 
      : TaskType.PROBLEM_REVIEW;
    
    // 将批次转换为Task对象
    // 后端返回的batch.tasks包含该批次的所有Task记录
    // 对于出题任务，通常只有1条记录；对于评分任务，可能有多条记录
    
    if (batch.tasks.length === 0) {
      // 如果batch.tasks为空（异常情况），创建一个批次级别的Task记录
      let taskId = 0;
      try {
        const hexPart = batch.batch_id.replace('batch_', '').substring(0, 8);
        taskId = parseInt(hexPart, 16) || Math.abs(batch.batch_id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0));
      } catch (e) {
        taskId = Math.abs(batch.batch_id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0));
      }
      
      tasks.push({
        id: taskId,
        batch_id: batch.batch_id,
        task_type: taskType,
        status: batch.status as any,
        total_count: batch.total_count,
        completed_count: batch.completed_count,
        claimed_at: batch.claimed_at,
        expires_at: batch.expires_at,
      });
    } else {
      // 为每个子任务创建一条记录
      // 对于出题任务，通常只有1条；对于评分任务，可能有多条
      batch.tasks.forEach((subTask) => {
        tasks.push({
          id: subTask.task_id,
          batch_id: batch.batch_id,
          task_type: taskType,
          status: batch.status as any,
          total_count: batch.total_count,
          completed_count: batch.completed_count,
          claimed_at: batch.claimed_at,
          expires_at: batch.expires_at,
          problem_id: subTask.problem_id,
        });
      });
    }
  });
  
  return tasks;
}

/**
 * 计算指定类型任务的总数量（total_count总和）
 * 只统计进行中（IN_PROGRESS）的任务，不包括已放弃、已完成、已提交等状态的任务
 */
export function calculateTotalTaskCount(tasks: Task[], taskType: TaskType): number {
  // 按batch_id去重，只计算每个批次的总数
  const batchTotals = new Map<string, number>();
  
  tasks
    .filter((task) => {
      // 只统计指定类型且状态为进行中的任务
      return (
        task.task_type === taskType &&
        task.status === TaskStatus.IN_PROGRESS // 只统计进行中的任务，排除已放弃、已完成等
      );
    })
    .forEach((task) => {
      if (task.batch_id && task.total_count !== undefined) {
        // 只记录一次每个批次的总数
        if (!batchTotals.has(task.batch_id)) {
          batchTotals.set(task.batch_id, task.total_count);
        }
      }
    });
  
  // 计算总和
  let total = 0;
  batchTotals.forEach((count) => {
    total += count;
  });
  
  return total;
}

/**
 * 计算指定类型任务的已完成数量（completed_count总和）
 * 只统计进行中（IN_PROGRESS）的任务的完成数，不包括已放弃、已完成、已提交等状态的任务
 */
export function calculateCompletedTaskCount(tasks: Task[], taskType: TaskType): number {
  // 按batch_id去重，只计算每个批次的完成数
  const batchCompleted = new Map<string, number>();
  
  tasks
    .filter((task) => {
      // 只统计指定类型且状态为进行中的任务
      return (
        task.task_type === taskType &&
        task.status === TaskStatus.IN_PROGRESS // 只统计进行中的任务，排除已放弃、已完成等
      );
    })
    .forEach((task) => {
      if (task.batch_id && task.completed_count !== undefined) {
        // 只记录一次每个批次的完成数
        if (!batchCompleted.has(task.batch_id)) {
          batchCompleted.set(task.batch_id, task.completed_count);
        }
      }
    });
  
  // 计算总和
  let total = 0;
  batchCompleted.forEach((count) => {
    total += count;
  });
  
  return total;
}

/**
 * 按批次ID分组任务
 */
export function groupTasksByBatch(tasks: Task[]): Map<string, Task[]> {
  const grouped = new Map<string, Task[]>();
  
  tasks.forEach((task) => {
    const batchId = task.batch_id || 'no-batch';
    if (!grouped.has(batchId)) {
      grouped.set(batchId, []);
    }
    grouped.get(batchId)!.push(task);
  });
  
  return grouped;
}

/**
 * 获取按批次合并的任务列表（用于任务管理表格显示）
 * 每个批次只显示一条记录，避免评分任务显示多条重复记录
 */
export function getUniqueBatchTasks(tasks: Task[]): Task[] {
  const batchMap = new Map<string, Task>();
  
  tasks.forEach((task) => {
    const key = task.batch_id || `single-${task.id}`;
    if (!batchMap.has(key)) {
      batchMap.set(key, task);
    }
  });
  
  return Array.from(batchMap.values());
}

