/**
 * 评分流程页面（任务驱动版）
 * - 从“我的任务”获取评分任务（review_problem）
 * - 依次完成正确性验证和评分，自动推进任务进度
 */

import { useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Empty,
  Input,
  InputNumber,
  message,
  Radio,
  Space,
  Spin,
  Steps,
  Tag,
  Typography,
} from 'antd';
import { CheckCircleOutlined, StarOutlined } from '@ant-design/icons';
import { reviewApi, taskApi } from '../../api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface ReviewChoiceResponse {
  problem_id: number;
  problem_title?: string;
  problem_content: any;
  problem_explanation?: string;
  choices: string[];
  correct_index?: number;
  instruction?: string;
}

interface TaskItem {
  task_id: number;
  problem_id: number;
}

interface TaskBatch {
  batch_id: string;
  task_type: string;
  status: string;
  total_count: number;
  completed_count: number;
  claimed_at?: string;
  expires_at?: string;
  tasks: TaskItem[];
}

export default function Review() {
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [currentStep, setCurrentStep] = useState(0); // 0: 正确性，1: 评分

  const [currentTask, setCurrentTask] = useState<TaskItem | null>(null);
  const [currentBatch, setCurrentBatch] = useState<TaskBatch | null>(null);
  const [problemData, setProblemData] = useState<ReviewChoiceResponse | null>(null);
  const [options, setOptions] = useState<string[]>([]);
  const [userChoiceIndex, setUserChoiceIndex] = useState<number | null>(null);
  const [reviewId, setReviewId] = useState<number | null>(null);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [showSolution, setShowSolution] = useState(false);

  const [innovationScore, setInnovationScore] = useState<number>(5);
  const [rigorScore, setRigorScore] = useState<number>(5);
  const [isVeto, setIsVeto] = useState(false);
  const [vetoReason, setVetoReason] = useState('');

  useEffect(() => {
    loadNextTask();
  }, []);

  const resetStatesForProblem = () => {
    setCurrentStep(0);
    setUserChoiceIndex(null);
    setReviewId(null);
    setIsCorrect(null);
    setShowSolution(false);
    setInnovationScore(5);
    setRigorScore(5);
    setIsVeto(false);
    setVetoReason('');
  };

  const loadNextTask = async () => {
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
        setCurrentTask(null);
        setCurrentBatch(null);
        setProblemData(null);
        setOptions([]);
        resetStatesForProblem();
        return;
      }
      const task = targetBatch.tasks.find((t) => t.problem_id);
      if (!task) {
        setCurrentTask(null);
        setCurrentBatch(targetBatch);
        setProblemData(null);
        setOptions([]);
        resetStatesForProblem();
        return;
      }
      setCurrentTask(task);
      setCurrentBatch(targetBatch);
      await loadProblem(task.problem_id);
    } catch (error) {
      message.error('加载任务失败');
      setCurrentTask(null);
      setCurrentBatch(null);
      setProblemData(null);
      setOptions([]);
      resetStatesForProblem();
    } finally {
      setLoading(false);
    }
  };

  const loadProblem = async (problemId: number) => {
    setLoading(true);
    try {
      const res: ReviewChoiceResponse = await reviewApi.getProblemChoices(problemId);
      setProblemData(res);
      setOptions(res.choices || []);
      resetStatesForProblem();
    } catch (error: any) {
      if (error.response?.status === 404) {
        message.info('题目不存在，尝试下一题');
        await loadNextTask();
      } else {
        message.error('加载题目失败');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitCorrectness = async () => {
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
  };

  const handleSubmitScore = async () => {
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
      await reviewApi.submitScores(
        reviewId,
        innovationScore,
        rigorScore,
        undefined,
        isVeto,
        vetoReason || undefined
      );
      message.success(isVeto ? '已提交否决意见' : '评分完成，已计入任务进度');
      await loadNextTask();
    } catch (error) {
      message.error('提交评分失败');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!currentTask || !problemData) {
    return (
      <div>
        <Title level={2}>评分流程</Title>
        <Card>
          <Empty
            description="暂无进行中的评分任务，请先领取任务后刷新"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={loadNextTask}>
              刷新任务
            </Button>
          </Empty>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <Title level={2}>评分流程</Title>

      <Card style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Steps
            current={currentStep}
            items={[
              { title: '正确性验证', icon: <CheckCircleOutlined /> },
              { title: '质量评分', icon: <StarOutlined /> },
            ]}
          />
          {currentBatch && (
            <Space size="small">
              <Tag color="blue">批次: {currentBatch.batch_id}</Tag>
              <Tag color="green">
                进度: {currentBatch.completed_count}/{currentBatch.total_count}
              </Tag>
            </Space>
          )}
        </Space>
      </Card>

      <Card title={problemData.problem_title || '题目信息'} style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Text strong>题目内容：</Text>
            <Paragraph style={{ marginTop: 8, fontSize: 16 }}>
              {typeof problemData.problem_content === 'string'
                ? problemData.problem_content
                : JSON.stringify(problemData.problem_content, null, 2)}
            </Paragraph>
          </div>

          {showSolution && problemData.problem_explanation && (
            <div>
              <Text strong>解题过程：</Text>
              <Paragraph style={{ marginTop: 8 }}>
                {problemData.problem_explanation}
              </Paragraph>
            </div>
          )}
        </Space>
      </Card>

      {currentStep === 0 && (
        <Card title="步骤1：正确性验证">
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Alert
              message="请选择正确答案"
              description={problemData.instruction || '从以下选项中选择您认为正确的答案。'}
              type="info"
              showIcon
            />

            <Radio.Group
              value={userChoiceIndex}
              onChange={(e) => setUserChoiceIndex(e.target.value)}
              style={{ width: '100%' }}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                {options.map((option, index) => (
                  <Radio
                    key={index}
                    value={index}
                    style={{
                      fontSize: 16,
                      padding: '12px',
                      border: '1px solid #d9d9d9',
                      borderRadius: '4px',
                      width: '100%',
                    }}
                  >
                    选项 {String.fromCharCode(65 + index)}: {option}
                  </Radio>
                ))}
              </Space>
            </Radio.Group>

            <Button type="primary" onClick={handleSubmitCorrectness} loading={submitting}>
              提交答案
            </Button>
          </Space>
        </Card>
      )}

      {currentStep === 1 && (
        <Card title="步骤2：质量评分">
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {isCorrect === false && (
              <Alert
                message="答案不正确"
                description="请参考解析，必要时可一票否决或给出较低评分。"
                type="warning"
                showIcon
              />
            )}

            <div>
              <Text strong>创新性评分：</Text>
              <div style={{ marginTop: 12 }}>
                <InputNumber
                  min={0}
                  max={10}
                  value={innovationScore}
                  onChange={(value) => setInnovationScore(value || 0)}
                  style={{ width: 200 }}
                />
                <Text type="secondary" style={{ marginLeft: 12 }}>
                  分（0-10）
                </Text>
              </div>
            </div>

            <div>
              <Text strong>数学严谨性评分：</Text>
              <div style={{ marginTop: 12 }}>
                <InputNumber
                  min={0}
                  max={10}
                  value={rigorScore}
                  onChange={(value) => setRigorScore(value || 0)}
                  style={{ width: 200 }}
                />
                <Text type="secondary" style={{ marginLeft: 12 }}>
                  分（0-10）
                </Text>
              </div>
            </div>

            <div>
              <Text strong>一票否决：</Text>
              <Radio.Group
                value={isVeto}
                onChange={(e) => setIsVeto(e.target.value)}
              >
                <Radio value={false}>否</Radio>
                <Radio value={true}>是</Radio>
              </Radio.Group>
              {isVeto && (
                <TextArea
                  value={vetoReason}
                  onChange={(e) => setVetoReason(e.target.value)}
                  placeholder="请输入否决理由"
                  rows={3}
                  style={{ marginTop: 8 }}
                />
              )}
            </div>

            <Space>
              <Button
                type="primary"
                icon={<StarOutlined />}
                onClick={handleSubmitScore}
                loading={submitting}
              >
                提交评分
              </Button>
              <Button onClick={loadNextTask}>跳过/下一题</Button>
            </Space>
          </Space>
        </Card>
      )}
    </div>
  );
}

