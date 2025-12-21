import { useCallback, useMemo } from 'react';

import { message } from 'antd';

import { problemApi } from '../../../api';
import type { VariantItem } from '../types';

export function useQualityCheck({
  variantsMap,
  setVariantsMap,
}: {
  variantsMap: Record<number, VariantItem[]>;
  setVariantsMap: React.Dispatch<React.SetStateAction<Record<number, VariantItem[]>>>;
}) {
  const allVariants = useMemo(() => Object.values(variantsMap).flat(), [variantsMap]);
  const passedVariants = useMemo(
    () => allVariants.filter((v) => v.qualityCheckStatus === 'passed'),
    [allVariants]
  );

  const handleQualityCheck = useCallback(async (parentId: number, variant: VariantItem) => {
    if (!variant.id) {
      message.error('题目ID不存在，无法进行质检');
      return;
    }

    setVariantsMap((prev) => ({
      ...prev,
      [parentId]: (prev[parentId] || []).map((v) =>
        v.key === variant.key ? { ...v, qualityCheckStatus: 'checking' } : v
      ),
    }));

    try {
      const result = await problemApi.qualityCheck(variant.id);

      const allPassed =
        result.all_passed === true ||
        (result.difficulty?.status === 'passed' &&
          result.originality?.status === 'passed' &&
          result.rigor?.status === 'passed');

      setVariantsMap((prev) => ({
        ...prev,
        [parentId]: (prev[parentId] || []).map((v) =>
          v.key === variant.key
            ? {
                ...v,
                qualityCheckStatus: allPassed ? 'passed' : 'failed',
                quality_check: result,
              }
            : v
        ),
      }));

      // 显示详细结果
      if (allPassed) {
        message.success('✅ 质量检查全部通过！');
      } else {
        const failedChecks = [];
        if (!result.difficulty?.is_passed) failedChecks.push('难度');
        if (!result.originality?.is_original) failedChecks.push('原创性');
        if (!result.rigor?.is_rigorous) failedChecks.push('严谨性');
        message.warning(`⚠️ 质检未通过：${failedChecks.join('、')} 不合格。点击"查看"按钮查看详情`);
      }
    } catch (error) {
      setVariantsMap((prev) => ({
        ...prev,
        [parentId]: (prev[parentId] || []).map((v) =>
          v.key === variant.key ? { ...v, qualityCheckStatus: 'failed' } : v
        ),
      }));
      message.error('质量检查失败');
    }
  }, [setVariantsMap]);

  const handleSubmitForReview = useCallback(async (parentId: number, variant: VariantItem) => {
    if (!variant.id) {
      message.error('题目ID不存在，无法提交审核');
      return;
    }
    if (variant.qualityCheckStatus !== 'passed') {
      message.warning('请先通过质量检查，再提交审核');
      return;
    }
    try {
      await problemApi.submitForReview(variant.id);
      message.success('已提交审核，状态已更新为待审核');
      setVariantsMap((prev) => ({
        ...prev,
        [parentId]: (prev[parentId] || []).map((v) =>
          v.key === variant.key ? { ...v, status: 'pending_review' } : v
        ),
      }));
    } catch (error: any) {
      message.error('提交审核失败: ' + (error.response?.data?.detail || error.message));
    }
  }, [setVariantsMap]);

  return {
    allVariants,
    passedVariants,
    handleQualityCheck,
    handleSubmitForReview,
  };
}



