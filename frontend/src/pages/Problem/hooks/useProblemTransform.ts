import { useCallback, useState } from 'react';

import type { ProblemItem, VariantItem } from '../types';
import { BUSINESS_CONSTANTS } from '../../../config/constants';
import { problemApi } from '../../../api';

export interface ParentProblem {
  id: number;
  source: ProblemItem;
}

export function useProblemTransform() {
  const [parentProblems, setParentProblems] = useState<ParentProblem[]>([]);
  const [transformPrompts, setTransformPrompts] = useState<Record<number, string>>({});
  const [variantsMap, setVariantsMap] = useState<Record<number, VariantItem[]>>({});
  const [variantCountMap, setVariantCountMap] = useState<Record<number, number>>({});

  const addParentProblem = useCallback((createdId: number, source: ProblemItem) => {
    setParentProblems((prev) => [...prev, { id: createdId, source }]);
    setVariantsMap((prev) => ({ ...prev, [createdId]: prev[createdId] || [] }));
    setVariantCountMap((prev) => ({ ...prev, [createdId]: prev[createdId] || 0 }));
    setTransformPrompts((prev) => ({ ...prev, [createdId]: prev[createdId] || '' }));
  }, []);

  const setPrompt = useCallback((parentId: number, prompt: string) => {
    setTransformPrompts((prev) => ({ ...prev, [parentId]: prompt }));
  }, []);

  const deleteVariant = useCallback((parentId: number, variantKey: string) => {
    setVariantsMap((prev) => ({
      ...prev,
      [parentId]: (prev[parentId] || []).filter((v) => v.key !== variantKey),
    }));
  }, []);

  const handleGenerateVariant = useCallback(async (parentId: number) => {
    const prompt = transformPrompts[parentId] || '';
    if (!prompt) {
      // message 在组件层处理更合适，这里直接抛出，由调用处提示
      throw new Error('EMPTY_PROMPT');
    }

    const count = variantCountMap[parentId] || 0;
    if (count >= BUSINESS_CONSTANTS.MAX_VARIANTS_PER_PROBLEM) {
      throw new Error('MAX_VARIANTS_REACHED');
    }

    console.log('🔵 [DEBUG] 开始生成变体, parentProblemId:', parentId);
    const variantResult = await problemApi.generateVariant(parentId, prompt);
    console.log('✅ [DEBUG] 变体生成成功:', variantResult);

    if (!variantResult || variantResult.success === false) {
      throw new Error(variantResult?.error || '生成变体失败');
    }

    console.log('🔵 [DEBUG] 开始创建变体题目到数据库...');
    const createdVariant = await problemApi.createProblem({
      title: `变体-${Date.now()}`,
      content:
        typeof variantResult.new_problem === 'string'
          ? { text: variantResult.new_problem }
          : variantResult.new_problem,
      explanation: variantResult.new_explanation,
      answer: variantResult.new_answer,
      category: 'high_school_comprehensive',
      source_type: 'ai_variant',
      parent_problem_id: parentId,
    });
    console.log('✅ [DEBUG] 变体题目创建成功:', createdVariant);

    setVariantsMap((prev) => ({
      ...prev,
      [parentId]: [
        ...(prev[parentId] || []),
        {
          ...createdVariant,
          key: `variant-${Date.now()}`,
          qualityCheckStatus: 'pending' as const,
        },
      ],
    }));
    setVariantCountMap((prev) => ({ ...prev, [parentId]: count + 1 }));
    setTransformPrompts((prev) => ({ ...prev, [parentId]: '' }));
  }, [transformPrompts, variantCountMap]);

  const resetTransformState = useCallback(() => {
    setParentProblems([]);
    setTransformPrompts({});
    setVariantsMap({});
    setVariantCountMap({});
  }, []);

  return {
    parentProblems,
    transformPrompts,
    variantsMap,
    variantCountMap,
    setVariantsMap,
    addParentProblem,
    setPrompt,
    deleteVariant,
    handleGenerateVariant,
    resetTransformState,
  };
}



