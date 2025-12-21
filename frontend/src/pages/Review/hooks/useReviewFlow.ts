import { useCallback, useMemo, useState } from 'react';
import { message } from 'antd';

import { reviewApi } from '../../../api';
import { useAuthStore } from '../../../store/useAuthStore';
import type { ReviewChoiceResponse } from '../types';

export function useReviewFlow({
  problemData,
  options,
  onFinishOne,
}: {
  problemData: ReviewChoiceResponse | null;
  options: string[];
  onFinishOne: () => Promise<void>;
}) {
  const { user, updateUser } = useAuthStore();
  const [submitting, setSubmitting] = useState(false);
  const [currentStep, setCurrentStep] = useState(0); // 0: 正确性，1: 评分

  const [userChoiceIndex, setUserChoiceIndex] = useState<number | null>(null);
  const [reviewId, setReviewId] = useState<number | null>(null);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [showSolution, setShowSolution] = useState(false);

  const [innovationScore, setInnovationScore] = useState<number>(5);
  const [rigorScore, setRigorScore] = useState<number>(5);
  const [isVeto, setIsVeto] = useState(false);
  const [vetoReason, setVetoReason] = useState('');

  const resetStatesForProblem = useCallback(() => {
    setCurrentStep(0);
    setUserChoiceIndex(null);
    setReviewId(null);
    setIsCorrect(null);
    setShowSolution(false);
    setInnovationScore(5);
    setRigorScore(5);
    setIsVeto(false);
    setVetoReason('');
  }, []);

  // 当 problemData 变化时，外部调用 reset 更清晰；这里提供一个派生 key 方便判断
  const problemKey = useMemo(() => problemData?.problem_id ?? null, [problemData?.problem_id]);

  const handleSubmitCorrectness = useCallback(async () => {
    if (userChoiceIndex === null) {
      message.warning('请选择一个答案');
      return;
    }
    if (!problemData) return;
    setSubmitting(true);
    try {
      const resp = await reviewApi.submitCorrectness(
        problemData.problem_id,
        userChoiceIndex,
        options[userChoiceIndex],
        problemData.correct_index
      );
      setReviewId(resp.review_id);
      const correct = resp.is_correct === true;
      setIsCorrect(correct);
      setShowSolution(!correct);
      setCurrentStep(1);
      message.success(correct ? '答案正确，请继续评分' : '答案不正确，请参考解析并给出评分/否决');
    } catch (error) {
      message.error('提交正确性失败');
    } finally {
      setSubmitting(false);
    }
  }, [options, problemData, userChoiceIndex]);

  const handleSubmitScore = useCallback(async () => {
    if (isVeto && !vetoReason) {
      message.warning('一票否决需要填写理由');
      return;
    }
    if (!reviewId) {
      message.error('缺少评分记录，请先完成正确性验证');
      return;
    }
    setSubmitting(true);
    try {
      const response = await reviewApi.submitScores(
        reviewId,
        innovationScore,
        rigorScore,
        undefined,
        isVeto,
        vetoReason || undefined
      );
      
      // 更新用户余额和评分计数
      if (user && response.new_balance !== undefined) {
        updateUser({
          ...user,
          balance: response.new_balance,
          reviews_completed_count: user.reviews_completed_count + 1,
        });
      }
      
      const successMessage = isVeto 
        ? '已提交否决意见' 
        : `评分完成！已获得 ¥${response.reward?.toFixed(2)} 奖励`;
      message.success(successMessage);
      
      await onFinishOne();
      resetStatesForProblem();
    } catch (error) {
      message.error('提交评分失败');
    } finally {
      setSubmitting(false);
    }
  }, [innovationScore, isVeto, onFinishOne, resetStatesForProblem, reviewId, rigorScore, vetoReason, user, updateUser]);

  return {
    submitting,
    currentStep,
    setCurrentStep,
    userChoiceIndex,
    setUserChoiceIndex,
    reviewId,
    isCorrect,
    showSolution,
    innovationScore,
    setInnovationScore,
    rigorScore,
    setRigorScore,
    isVeto,
    setIsVeto,
    vetoReason,
    setVetoReason,
    resetStatesForProblem,
    problemKey,
    handleSubmitCorrectness,
    handleSubmitScore,
  };
}


