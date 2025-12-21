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

  const loadProblem = useCallback(async (problemId: number) => {
    setLoading(true);
    try {
      const res: ReviewChoiceResponse = await reviewApi.getProblemChoices(problemId);
      setProblemData(res);
      setOptions(res.choices || []);
    } catch (error: any) {
      if (error.response?.status === 404) {
        message.info('题目不存在，尝试下一题');
        // 交由 loadNextTask 继续推进
        throw Object.assign(new Error('PROBLEM_NOT_FOUND'), { code: 404 });
      } else {
        message.error('加载题目失败');
        throw error;
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const clearCurrent = useCallback(() => {
    setCurrentTask(null);
    setCurrentBatch(null);
    setProblemData(null);
    setOptions([]);
  }, []);

  const loadNextTask = useCallback(async () => {
    setLoading(true);
    try {
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

      const task = targetBatch.tasks.find((t) => t.problem_id);
      if (!task) {
        setCurrentTask(null);
        setCurrentBatch(targetBatch);
        setProblemData(null);
        setOptions([]);
        return;
      }

      setCurrentTask(task);
      setCurrentBatch(targetBatch);

      try {
        await loadProblem(task.problem_id);
      } catch (e: any) {
        if (e?.code === 404) {
          // 题目不存在：继续下一题
          await loadNextTask();
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
  }, [clearCurrent, loadProblem]);

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


