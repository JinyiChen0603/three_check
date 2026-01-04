/**
 * 评分流程页面（任务驱动版）
 * - 从“我的任务”获取评分任务（review_problem）
 * - 依次完成正确性验证和评分，自动推进任务进度
 */

import { useEffect } from 'react';
import { Card, Space, Steps, Tag, Typography } from 'antd';
import { CheckCircleOutlined, StarOutlined } from '@ant-design/icons';

import { useReviewTask } from './hooks/useReviewTask';
import { useReviewFlow } from './hooks/useReviewFlow';
import { ProblemDisplay } from './components/ProblemDisplay';
import { CorrectnessStep } from './components/CorrectnessStep';
import { ScoringStep } from './components/ScoringStep';
import { Loading } from '../../components/common/Loading';
import { EmptyState } from '../../components/common/EmptyState';

const { Title } = Typography;

export default function Review() {
  const task = useReviewTask();
  const flow = useReviewFlow({
    problemData: task.problemData,
    options: task.options,
    onFinishOne: task.loadNextTask,
  });

  // 题目变化时重置流程状态（与旧实现一致）
  useEffect(() => {
    if (task.problemData) {
      flow.resetStatesForProblem();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flow.problemKey, task.problemData]);

  if (task.loading) {
    return <Loading />;
  }

  if (!task.currentTask || !task.problemData) {
    return (
      <div>
        <Title level={2}>评分流程</Title>
        <Card>
          <EmptyState
            description={
              task.currentBatch 
                ? "当前批次的所有题目已完成，请前往任务管理页面查看或领取新任务"
                : "暂无进行中的评分任务，请先前往任务管理页面领取任务"
            }
            actionText="刷新任务"
            onAction={task.loadNextTask}
          />
        </Card>
      </div>
    );
  }

  return (
    <div>
      <Title level={2}>评分流程</Title>

      <Card style={{ marginBottom: 24 }}>
        <Space orientation="vertical" style={{ width: '100%' }}>
          <Steps
            current={flow.currentStep}
            items={[
              { title: '正确性验证', icon: <CheckCircleOutlined /> },
              { title: '质量评分', icon: <StarOutlined /> },
            ]}
          />
          {task.currentBatch && task.problemData?.progress && (
            <Space size="small">
              <Tag color="blue">批次: {task.currentBatch.batch_id}</Tag>
              <Tag color="green">
                进度: 第 {task.problemData.progress.current} 题/共 {task.problemData.progress.total} 题
              </Tag>
            </Space>
          )}
        </Space>
      </Card>

      <ProblemDisplay problemData={task.problemData} showSolution={flow.showSolution} />

      {flow.currentStep === 0 && (
        <CorrectnessStep
          problemData={task.problemData}
          options={task.options}
          userChoiceIndex={flow.userChoiceIndex}
          onChangeChoice={(idx) => flow.setUserChoiceIndex(idx)}
          onSubmit={flow.handleSubmitCorrectness}
          submitting={flow.submitting}
        />
      )}

      {flow.currentStep === 1 && (
        <ScoringStep
          isCorrect={flow.isCorrect}
          innovationScore={flow.innovationScore}
          setInnovationScore={flow.setInnovationScore}
          rigorScore={flow.rigorScore}
          setRigorScore={flow.setRigorScore}
          isVeto={flow.isVeto}
          setIsVeto={flow.setIsVeto}
          vetoReason={flow.vetoReason}
          setVetoReason={flow.setVetoReason}
          onSubmit={flow.handleSubmitScore}
          onSkip={task.loadNextTask}
          submitting={flow.submitting}
        />
      )}
    </div>
  );
}

