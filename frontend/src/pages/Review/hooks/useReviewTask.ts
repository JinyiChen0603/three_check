import { useCallback, useEffect, useState } from 'react';
import { message } from 'antd';

import { reviewApi, taskApi } from '../../../api';
import type { ReviewChoiceResponse, TaskBatch, TaskItem } from '../types';

export function useReviewTask() {
  const [loading, setLoading] = useState(false);
  const [currentTask, setCurrentTask] = useState<TaskItem | null>(null);
  const [currentBatch, setCurrentBatch] = useState<TaskBatch | null>(null);
  const [problemData, setProblemData] = useState<ReviewChoiceResponse | null>(null);
  const [options, setOptions] = useState<string[]>([]);

  const clearCurrent = useCallback(() => {
    setCurrentTask(null);
    setCurrentBatch(null);
    setProblemData(null);
    setOptions([]);
  }, []);

  const loadNextTask = useCallback(async () => {
    setLoading(true);
    try {
      // 1. 检查是否有进行中的评分批次
      const data = await taskApi.getMyTasks();
      const batches: TaskBatch[] = data?.batches || [];
      const targetBatch = batches.find(
        (b) =>
          b.task_type === 'review_problem' &&
          b.status === 'in_progress' &&
          Array.isArray(b.tasks) &&
          b.tasks.length > 0
      );

      if (!targetBatch) {
        clearCurrent();
        return;
      }

      setCurrentBatch(targetBatch);

      // 2. 直接调用新API获取下一个可评分题目（不再从Task列表中选择）
      try {
        const nextProblem: ReviewChoiceResponse = await reviewApi.getNextProblem();
        
        // 构造一个虚拟的Task对象，保持兼容性
        const virtualTask: TaskItem = {
          task_id: targetBatch.tasks[0]?.task_id || 0,
          validated_problem_id: nextProblem.validated_problem_id,
          status: 'in_progress',
          has_review: false
        };
        
        setCurrentTask(virtualTask);
        setProblemData(nextProblem);
        setOptions(nextProblem.choices || []);
      } catch (e: any) {
        if (e?.response?.status === 404) {
          // 没有可评分的题目了
          setCurrentTask(null);
          setProblemData(null);
          setOptions([]);
          message.info('当前批次已无待评分题目');
          return;
        }
        throw e;
      }
    } catch (error) {
      message.error('加载任务失败');
      clearCurrent();
    } finally {
      setLoading(false);
    }
  }, [clearCurrent]);

  useEffect(() => {
    loadNextTask();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    loading,
    currentTask,
    currentBatch,
    problemData,
    options,
    loadNextTask,
  };
}


