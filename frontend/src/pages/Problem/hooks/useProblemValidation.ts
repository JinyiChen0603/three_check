import { useCallback, useEffect, useRef, useState } from 'react';
import { message } from 'antd';

import { problemApi } from '../../../api';
import type { ProblemItem, ValidationStatus } from '../types';

export function useProblemValidation({
  onParentCreated,
  goToTransformStep,
}: {
  onParentCreated: (createdId: number, source: ProblemItem) => void;
  goToTransformStep: () => void;
}) {
  const [problems, setProblems] = useState<ProblemItem[]>([]);
  const problemsRef = useRef<ProblemItem[]>([]);
  const [ocrLoading, setOcrLoading] = useState(false);

  useEffect(() => {
    problemsRef.current = problems;
  }, [problems]);

  // 简化的验证队列逻辑
  const validationQueueRef = useRef<string[]>([]);

  const removeFromQueue = useCallback((key: string) => {
    validationQueueRef.current = validationQueueRef.current.filter((k) => k !== key);
  }, []);

  const enqueueProblems = useCallback((keys: string[]) => {
    setProblems((prev) =>
      prev.map((p) =>
        keys.includes(p.key) && p.validationStatus !== 'validating' && p.validationStatus !== 'queued'
          ? { ...p, validationStatus: 'queued' as ValidationStatus }
          : p
      )
    );
    const existing = new Set(validationQueueRef.current);
    keys.forEach((k) => {
      if (!existing.has(k)) {
        validationQueueRef.current.push(k);
        existing.add(k);
      }
    });
  }, []);

  const handleAddProblem = useCallback(() => {
    setProblems((prev) => [
      ...prev,
      {
        key: `problem-${Date.now()}`,
        content: '',
        answer: '',
        validationStatus: 'pending',
      },
    ]);
  }, []);

  const handleRemoveProblem = useCallback(
    (key: string) => {
      setProblems((prev) => prev.filter((p) => p.key !== key));
      removeFromQueue(key);
    },
    [removeFromQueue]
  );

  const handleProblemChange = useCallback(
    (key: string, field: keyof ProblemItem, value: string) => {
      setProblems((prev) => prev.map((p) => (p.key === key ? { ...p, [field]: value } : p)));
    },
    []
  );

  const handleOCR = useCallback(async (file: File) => {
    setOcrLoading(true);
    try {
      const result = await problemApi.ocrImage(file);
      message.success('OCR识别成功');

      setProblems((prev) => [
        ...prev,
        {
          key: `problem-${Date.now()}`,
          content: result.problem || '',
          answer: result.answer || '',
          explanation: result.explanation || '',
          validationStatus: 'pending',
        },
      ]);
    } catch (error: any) {
      message.error(`OCR识别失败：${error.response?.data?.detail || error.message}`);
      console.error('OCR错误：', error);
    } finally {
      setOcrLoading(false);
    }
    return false;
  }, []);

  const handleValidateSingle = useCallback(
    (problem: ProblemItem) => {
      if (!problem.content || !problem.answer) {
        message.warning('请填写完整的题目和答案');
        return;
      }
      enqueueProblems([problem.key]);
    },
    [enqueueProblems]
  );

  const handleValidateBatch = useCallback(() => {
    setProblems((prev) => {
      const validProblems = prev.filter((p) => p.content && p.answer);
      if (validProblems.length === 0) {
        message.warning('没有可验证的题目');
        return prev;
      }

      const validKeys = validProblems.map((p) => p.key);
      // 标记排队
      const next = prev.map((p) => (validKeys.includes(p.key) ? { ...p, validationStatus: 'queued' as ValidationStatus } : p));
      enqueueProblems(validKeys);
      message.success('已加入验证队列');
      return next;
    });
  }, [enqueueProblems]);

  const handleUseSingle = useCallback(
    async (record: ProblemItem) => {
      if (record.validationStatus !== 'passed') {
        message.warning('请先验证题目并通过验证');
        return;
      }

      try {
        const problemData = {
          title: `母题-${Date.now()}`,
          content: { text: record.content },
          explanation: record.explanation,
          answer: record.answer,
          category: 'high_school_comprehensive',
          source_type: 'manual',
        };

        const created = await problemApi.createProblem(problemData);

        onParentCreated(created.id, record);
        goToTransformStep();
        message.success('母题已保存到数据库，ID: ' + created.id);
      } catch (error: any) {
        console.error('❌ [DEBUG] 保存母题失败:', error);
        console.error('❌ [DEBUG] 错误详情:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          config: error.config,
        });
        message.error('保存母题失败: ' + (error.response?.data?.detail || error.message));
      }
    },
    [goToTransformStep, onParentCreated]
  );

  const handleBatchUse = useCallback(async () => {
    const passed = problems.filter((p) => p.validationStatus === 'passed');
    if (passed.length === 0) {
      message.warning('请先完成验证并选择通过的题目');
      return;
    }
    try {
      const createdList: Array<{ id: number; source: ProblemItem }> = [];
      for (const item of passed) {
        const problemData = {
          title: `母题-${Date.now()}`,
          content: { text: item.content },
          explanation: item.explanation,
          answer: item.answer,
          category: 'high_school_comprehensive',
          source_type: 'manual',
        };
        const created = await problemApi.createProblem(problemData);
        createdList.push({ id: created.id, source: item });
        onParentCreated(created.id, item);
      }
      if (createdList.length > 0) {
        goToTransformStep();
        message.success(`批量使用成功，已创建 ${createdList.length} 个母题`);
      }
    } catch (error: any) {
      message.error('批量使用失败: ' + (error.response?.data?.detail || error.message));
    }
  }, [goToTransformStep, onParentCreated, problems]);

  return {
    problems,
    setProblems,
    ocrLoading,
    handleAddProblem,
    handleRemoveProblem,
    handleProblemChange,
    handleOCR,
    handleValidateSingle,
    handleValidateBatch,
    handleUseSingle,
    handleBatchUse,
  };
}



