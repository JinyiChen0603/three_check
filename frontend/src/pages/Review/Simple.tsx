/**
 * 评分流程页面（简化版）
 */

import { useState } from 'react';
import {
  Card,
  Steps,
  Button,
  Space,
  Typography,
  Radio,
  InputNumber,
  Input,
  message,
  Alert,
  Divider,
} from 'antd';
import {
  CheckCircleOutlined,
  StarOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

// 模拟题目数据
const mockProblem = {
  id: 1,
  content: '求解方程：x² + 5x + 6 = 0',
  explanation: '使用因式分解法：x² + 5x + 6 = (x + 2)(x + 3) = 0，所以 x = -2 或 x = -3',
  answer: 'x = -2 或 x = -3',
};

// 模拟4个选项
const mockOptions = [
  'x = -2 或 x = -3',  // 正确答案
  'x = 2 或 x = 3',
  'x = -1 或 x = -6',
  'x = 1 或 x = 6',
];

export default function ReviewSimple() {
  const [currentStep, setCurrentStep] = useState(0);
  const [currentProblem] = useState(mockProblem);
  
  // 步骤1：正确性验证
  const [userChoice, setUserChoice] = useState<string>('');
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [showSolution, setShowSolution] = useState(false);
  const [judgement, setJudgement] = useState<string>('');

  // 步骤2：评分
  const [innovationScore, setInnovationScore] = useState<number>(5);
  const [rigorScore, setRigorScore] = useState<number>(5);
  const [vetoReason, setVetoReason] = useState<string>('');
  const [isVeto, setIsVeto] = useState(false);

  const handleSubmitCorrectness = () => {
    if (!userChoice) {
      message.warning('请选择一个答案');
      return;
    }

    // 检查答案是否正确
    const correct = userChoice === currentProblem.answer;
    setIsCorrect(correct);

    if (correct) {
      message.success('答案正确，请继续评分');
      setCurrentStep(1);
    } else {
      setShowSolution(true);
    }
  };

  const handleSubmitJudgement = () => {
    if (!judgement) {
      message.warning('请判断题目的正确性');
      return;
    }

    if (judgement === 'correct') {
      message.success('题目确认正确，请继续评分');
      setCurrentStep(1);
    } else {
      message.info('题目已标记为不正确，将返回给出题者修改');
      // 重置状态，加载下一题
      setTimeout(() => {
        setCurrentStep(0);
        setUserChoice('');
        setIsCorrect(null);
        setShowSolution(false);
        setJudgement('');
      }, 1500);
    }
  };

  const handleSubmitScore = () => {
    if (isVeto && !vetoReason) {
      message.warning('一票否决需要填写理由');
      return;
    }

    message.success(isVeto ? '已提交否决意见' : '评分完成！');
    
    // 重置状态，模拟加载下一题
    setTimeout(() => {
      setCurrentStep(0);
      setUserChoice('');
      setIsCorrect(null);
      setShowSolution(false);
      setJudgement('');
      setInnovationScore(5);
      setRigorScore(5);
      setVetoReason('');
      setIsVeto(false);
    }, 1500);
  };

  return (
    <div>
      <Title level={2}>评分流程</Title>

      {/* 进度步骤 */}
      <Card style={{ marginBottom: 24 }}>
        <Steps current={currentStep}>
          <Steps.Step title="正确性验证" icon={<CheckCircleOutlined />} />
          <Steps.Step title="质量评分" icon={<StarOutlined />} />
        </Steps>
      </Card>

      {/* 题目展示 */}
      <Card title="题目信息" style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Text strong>题目内容：</Text>
            <Paragraph style={{ marginTop: 8, fontSize: 16 }}>
              {currentProblem.content}
            </Paragraph>
          </div>

          {currentProblem.explanation && showSolution && (
            <div>
              <Text strong>解题过程：</Text>
              <Paragraph style={{ marginTop: 8 }}>
                {currentProblem.explanation}
              </Paragraph>
            </div>
          )}

          {showSolution && (
            <div>
              <Text strong>标准答案：</Text>
              <Paragraph style={{ marginTop: 8 }} copyable>
                {currentProblem.answer}
              </Paragraph>
            </div>
          )}
        </Space>
      </Card>

      {/* 步骤1：正确性验证 */}
      {currentStep === 0 && (
        <Card title="步骤1：正确性验证">
          {!showSolution ? (
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Alert
                message="请选择正确答案"
                description="从以下4个选项中选择您认为正确的答案。如果选错，系统会显示解题过程和标准答案供您判断。"
                type="info"
                showIcon
              />

              <Radio.Group
                value={userChoice}
                onChange={(e) => setUserChoice(e.target.value)}
                style={{ width: '100%' }}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  {mockOptions.map((option, index) => (
                    <Radio
                      key={index}
                      value={option}
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

              <Button
                type="primary"
                size="large"
                onClick={handleSubmitCorrectness}
                disabled={!userChoice}
              >
                提交答案
              </Button>
            </Space>
          ) : (
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Alert
                message="您的答案不正确"
                description="请查看解题过程和标准答案，判断题目本身是否正确。"
                type="warning"
                showIcon
              />

              <div>
                <Text strong>请判断：</Text>
                <Radio.Group
                  value={judgement}
                  onChange={(e) => setJudgement(e.target.value)}
                  style={{ marginTop: 12 }}
                >
                  <Space direction="vertical">
                    <Radio value="correct">题目和答案都是正确的（我选错了）</Radio>
                    <Radio value="incorrect">题目或答案有问题（需要修改）</Radio>
                  </Space>
                </Radio.Group>
              </div>

              <Button
                type="primary"
                size="large"
                onClick={handleSubmitJudgement}
                disabled={!judgement}
              >
                提交判断
              </Button>
            </Space>
          )}
        </Card>
      )}

      {/* 步骤2：质量评分 */}
      {currentStep === 1 && (
        <Card title="步骤2：质量评分">
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Alert
              message="请对题目进行评分"
              description="从创新性和数学严谨性两个维度评分，满分10分。如果题目存在严重问题，可以使用一票否决。"
              type="info"
              showIcon
            />

            {/* 创新性评分 */}
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
                  分（0-10分，10分为最高）
                </Text>
              </div>
              <Paragraph type="secondary" style={{ marginTop: 8 }}>
                评价标准：题目的新颖程度、思路独特性、与常规题目的差异度
              </Paragraph>
            </div>

            <Divider />

            {/* 数学严谨性评分 */}
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
                  分（0-10分，10分为最高）
                </Text>
              </div>
              <Paragraph type="secondary" style={{ marginTop: 8 }}>
                评价标准：数学表述的准确性、逻辑的严密性、条件的完备性
              </Paragraph>
            </div>

            <Divider />

            {/* 一票否决 */}
            <div>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Radio.Group
                  value={isVeto}
                  onChange={(e) => setIsVeto(e.target.value)}
                >
                  <Space direction="vertical">
                    <Radio value={false}>通过评分</Radio>
                    <Radio value={true}>
                      <Space>
                        <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                        <Text type="danger">一票否决</Text>
                      </Space>
                    </Radio>
                  </Space>
                </Radio.Group>

                {isVeto && (
                  <TextArea
                    value={vetoReason}
                    onChange={(e) => setVetoReason(e.target.value)}
                    placeholder="请详细说明否决理由..."
                    rows={4}
                    style={{ marginTop: 12 }}
                  />
                )}
              </Space>
            </div>

            <Space>
              <Button
                type="primary"
                size="large"
                onClick={handleSubmitScore}
                disabled={isVeto && !vetoReason}
              >
                {isVeto ? '提交否决' : '提交评分'}
              </Button>
              <Button size="large" onClick={() => setCurrentStep(0)}>
                返回上一步
              </Button>
            </Space>
          </Space>
        </Card>
      )}
    </div>
  );
}

