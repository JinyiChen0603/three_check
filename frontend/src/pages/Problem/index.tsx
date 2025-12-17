/**
 * 出题流程页面
 */

import { useState } from 'react';
import {
  Card,
  Steps,
  Button,
  Space,
  Typography,
  Input,
  Upload,
  message,
  Table,
  Tag,
  Progress,
  Alert,
  Divider,
  Modal,
  Form,
  Tabs,
} from 'antd';
import {
  UploadOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  ExperimentOutlined,
  SafetyCertificateOutlined,
  FileTextOutlined,
  PlusOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { problemApi } from '../../api';
import { Problem, QualityCheck } from '../../types';
import { BUSINESS_CONSTANTS } from '../../config/constants';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Step } = Steps;
const { TabPane } = Tabs;

interface ProblemItem {
  key: string;
  content: string;
  answer: string;
  explanation?: string;
  validationStatus?: 'pending' | 'validating' | 'passed' | 'failed';
  validationResult?: any;
}

interface VariantItem extends Problem {
  key: string;
  qualityCheckStatus?: 'pending' | 'checking' | 'passed' | 'failed';
}

export default function ProblemCreation() {
  const [currentStep, setCurrentStep] = useState(0);
  const [form] = Form.useForm();

  // 步骤1：母题验证
  const [problems, setProblems] = useState<ProblemItem[]>([]);
  const [ocrLoading, setOcrLoading] = useState(false);

  // 步骤2：题目变形
  const [parentProblem, setParentProblem] = useState<ProblemItem | null>(null);
  const [transformPrompt, setTransformPrompt] = useState('');
  const [variants, setVariants] = useState<VariantItem[]>([]);
  const [variantCount, setVariantCount] = useState(0);

  // 步骤3：质量检查
  const [selectedVariants, setSelectedVariants] = useState<number[]>([]);

  // ==================== 步骤1：母题验证 ====================

  const handleAddProblem = () => {
    setProblems([
      ...problems,
      {
        key: `problem-${Date.now()}`,
        content: '',
        answer: '',
        validationStatus: 'pending',
      },
    ]);
  };

  const handleRemoveProblem = (key: string) => {
    setProblems(problems.filter((p) => p.key !== key));
  };

  const handleProblemChange = (
    key: string,
    field: keyof ProblemItem,
    value: string
  ) => {
    setProblems(
      problems.map((p) =>
        p.key === key ? { ...p, [field]: value } : p
      )
    );
  };

  const handleOCR = async (file: File) => {
    setOcrLoading(true);
    try {
      const result = await problemApi.ocrImage(file);
      message.success('OCR识别成功');
      
      // 添加识别结果到问题列表
      setProblems([
        ...problems,
        {
          key: `problem-${Date.now()}`,
          content: result.content || '',
          answer: result.answer || '',
          validationStatus: 'pending',
        },
      ]);
    } catch (error) {
      message.error('OCR识别失败');
    } finally {
      setOcrLoading(false);
    }
    return false; // 阻止自动上传
  };

  const handleValidateSingle = async (problem: ProblemItem) => {
    if (!problem.content || !problem.answer) {
      message.warning('请填写完整的题目和答案');
      return;
    }

    // 更新状态为验证中
    setProblems(
      problems.map((p) =>
        p.key === problem.key ? { ...p, validationStatus: 'validating' } : p
      )
    );

    try {
      const result = await problemApi.validateSingle(problem.content, problem.answer);
      
      const passed = result.correct_count <= BUSINESS_CONSTANTS.VALIDATION_THRESHOLD;
      
      setProblems(
        problems.map((p) =>
          p.key === problem.key
            ? {
                ...p,
                validationStatus: passed ? 'passed' : 'failed',
                validationResult: result,
              }
            : p
        )
      );

      message.success(
        passed
          ? '验证通过！这个题目难度合适'
          : '验证未通过，题目可能过于简单'
      );
    } catch (error) {
      setProblems(
        problems.map((p) =>
          p.key === problem.key ? { ...p, validationStatus: 'failed' } : p
        )
      );
      message.error('验证失败');
    }
  };

  const handleValidateBatch = async () => {
    const validProblems = problems.filter(
      (p) => p.content && p.answer
    );

    if (validProblems.length === 0) {
      message.warning('没有可验证的题目');
      return;
    }

    if (validProblems.length > BUSINESS_CONSTANTS.MAX_BATCH_VALIDATION) {
      message.warning(
        `批量验证最多支持 ${BUSINESS_CONSTANTS.MAX_BATCH_VALIDATION} 个题目`
      );
      return;
    }

    // 更新状态为验证中
    const validKeys = validProblems.map((p) => p.key);
    setProblems(
      problems.map((p) =>
        validKeys.includes(p.key) ? { ...p, validationStatus: 'validating' } : p
      )
    );

    try {
      const result = await problemApi.validateBatch(
        validProblems.map((p) => ({ content: p.content, answer: p.answer }))
      );

      // 更新验证结果
      setProblems(
        problems.map((p, index) => {
          if (!validKeys.includes(p.key)) return p;
          
          const resultIndex = validKeys.indexOf(p.key);
          const itemResult = result[resultIndex];
          const passed = itemResult.correct_count <= BUSINESS_CONSTANTS.VALIDATION_THRESHOLD;
          
          return {
            ...p,
            validationStatus: passed ? 'passed' : 'failed',
            validationResult: itemResult,
          };
        })
      );

      message.success('批量验证完成');
    } catch (error) {
      message.error('批量验证失败');
      setProblems(
        problems.map((p) =>
          validKeys.includes(p.key) ? { ...p, validationStatus: 'failed' } : p
        )
      );
    }
  };

  const problemColumns = [
    {
      title: '题目内容',
      dataIndex: 'content',
      key: 'content',
      width: '40%',
      render: (text: string, record: ProblemItem) => (
        <TextArea
          value={text}
          onChange={(e) =>
            handleProblemChange(record.key, 'content', e.target.value)
          }
          placeholder="请输入题目内容..."
          rows={3}
        />
      ),
    },
    {
      title: '答案',
      dataIndex: 'answer',
      key: 'answer',
      width: '25%',
      render: (text: string, record: ProblemItem) => (
        <Input
          value={text}
          onChange={(e) =>
            handleProblemChange(record.key, 'answer', e.target.value)
          }
          placeholder="请输入答案..."
        />
      ),
    },
    {
      title: '验证状态',
      dataIndex: 'validationStatus',
      key: 'validationStatus',
      width: '15%',
      render: (status: string, record: ProblemItem) => {
        if (status === 'validating') {
          return <Tag icon={<SyncOutlined spin />} color="processing">验证中</Tag>;
        }
        if (status === 'passed') {
          return (
            <div>
              <Tag icon={<CheckCircleOutlined />} color="success">通过</Tag>
              {record.validationResult && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {record.validationResult.correct_count}/{BUSINESS_CONSTANTS.VALIDATION_ATTEMPTS}
                </Text>
              )}
            </div>
          );
        }
        if (status === 'failed') {
          return <Tag color="error">未通过</Tag>;
        }
        return <Tag color="default">待验证</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: '20%',
      render: (_: any, record: ProblemItem) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => handleValidateSingle(record)}
            loading={record.validationStatus === 'validating'}
          >
            验证
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => {
              setParentProblem(record);
              setCurrentStep(1);
            }}
            disabled={record.validationStatus !== 'passed'}
          >
            使用
          </Button>
          <Button
            type="link"
            danger
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => handleRemoveProblem(record.key)}
          />
        </Space>
      ),
    },
  ];

  // ==================== 步骤2：题目变形 ====================

  const handleGenerateVariant = async () => {
    if (!parentProblem || !transformPrompt) {
      message.warning('请填写变形提示词');
      return;
    }

    if (variantCount >= BUSINESS_CONSTANTS.MAX_VARIANTS_PER_PROBLEM) {
      message.warning(
        `每个母题最多可以变形 ${BUSINESS_CONSTANTS.MAX_VARIANTS_PER_PROBLEM} 次`
      );
      return;
    }

    try {
      const variant = await problemApi.generateVariant(
        0, // parentProblemId，这里暂时用0
        parentProblem.content,
        parentProblem.explanation || '',
        parentProblem.answer,
        transformPrompt
      );

      setVariants([...variants, { ...variant, key: `variant-${Date.now()}` }]);
      setVariantCount(variantCount + 1);
      message.success('题目变形成功！');
      setTransformPrompt(''); // 清空提示词
    } catch (error) {
      message.error('题目变形失败');
    }
  };

  const handleQualityCheck = async (variant: VariantItem) => {
    setVariants(
      variants.map((v) =>
        v.key === variant.key ? { ...v, qualityCheckStatus: 'checking' } : v
      )
    );

    try {
      const result = await problemApi.qualityCheck(variant.id);
      
      const allPassed =
        result.difficulty?.status === 'passed' &&
        result.originality?.status === 'passed' &&
        result.rigor?.status === 'passed';

      setVariants(
        variants.map((v) =>
          v.key === variant.key
            ? {
                ...v,
                qualityCheckStatus: allPassed ? 'passed' : 'failed',
                quality_check: result,
              }
            : v
        )
      );

      message.success('质量检查完成');
    } catch (error) {
      setVariants(
        variants.map((v) =>
          v.key === variant.key ? { ...v, qualityCheckStatus: 'failed' } : v
        )
      );
      message.error('质量检查失败');
    }
  };

  const variantColumns = [
    {
      title: '题目内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
    },
    {
      title: '质量检查',
      key: 'quality',
      render: (_: any, record: VariantItem) => {
        if (record.qualityCheckStatus === 'checking') {
          return <Tag icon={<SyncOutlined spin />} color="processing">检查中</Tag>;
        }
        if (record.qualityCheckStatus === 'passed') {
          return (
            <Space direction="vertical" size="small">
              <Tag color="success">全部通过</Tag>
              {record.quality_check && (
                <Space size="small">
                  <Tag color="blue">难度✓</Tag>
                  <Tag color="green">原创✓</Tag>
                  <Tag color="purple">严谨✓</Tag>
                </Space>
              )}
            </Space>
          );
        }
        if (record.qualityCheckStatus === 'failed') {
          return <Tag color="error">未通过</Tag>;
        }
        return <Tag color="default">待检查</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: VariantItem) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => handleQualityCheck(record)}
            loading={record.qualityCheckStatus === 'checking'}
          >
            质检
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => {
              Modal.info({
                title: '题目详情',
                width: 800,
                content: (
                  <div>
                    <p><strong>内容：</strong>{record.content}</p>
                    <p><strong>答案：</strong>{record.answer}</p>
                    {record.explanation && (
                      <p><strong>解析：</strong>{record.explanation}</p>
                    )}
                  </div>
                ),
              });
            }}
          >
            查看
          </Button>
          <Button
            type="link"
            danger
            size="small"
            onClick={() => setVariants(variants.filter((v) => v.key !== record.key))}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  // ==================== 渲染 ====================

  return (
    <div>
      <Title level={2}>
        <FileTextOutlined /> 出题流程
      </Title>

      {/* 进度步骤 */}
      <Card style={{ marginBottom: 24 }}>
        <Steps current={currentStep}>
          <Step title="母题验证" icon={<CheckCircleOutlined />} />
          <Step title="题目变形" icon={<ExperimentOutlined />} />
          <Step title="质量检查" icon={<SafetyCertificateOutlined />} />
        </Steps>
      </Card>

      {/* 步骤1：母题验证 */}
      {currentStep === 0 && (
        <Card title="步骤1：母题验证">
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Alert
              message="准备母题"
              description={
                <div>
                  <p>您可以：</p>
                  <ul style={{ paddingLeft: 20 }}>
                    <li>手动输入题目和答案</li>
                    <li>使用OCR识别图片中的题目</li>
                    <li>从资料库下载题目后输入</li>
                  </ul>
                  <p style={{ marginTop: 8, color: '#ff4d4f' }}>
                    ⚠️ 注意：只需要有明确答案的解答题，不要证明题、判断题或选择题
                  </p>
                </div>
              }
              type="info"
              showIcon
            />

            {/* 工具栏 */}
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleAddProblem}
              >
                添加题目
              </Button>
              <Upload
                beforeUpload={handleOCR}
                showUploadList={false}
                accept="image/*"
              >
                <Button icon={<UploadOutlined />} loading={ocrLoading}>
                  OCR识别图片
                </Button>
              </Upload>
              <Button
                onClick={handleValidateBatch}
                disabled={problems.length === 0}
              >
                批量验证（最多{BUSINESS_CONSTANTS.MAX_BATCH_VALIDATION}个）
              </Button>
            </Space>

            {/* 题目列表 */}
            <Table
              columns={problemColumns}
              dataSource={problems}
              rowKey="key"
              pagination={false}
            />

            {problems.length > 0 && (
              <Alert
                message="验证说明"
                description={`系统会使用AI模型测试${BUSINESS_CONSTANTS.VALIDATION_ATTEMPTS}次，如果正确次数不超过${BUSINESS_CONSTANTS.VALIDATION_THRESHOLD}次，则认为题目难度合适。`}
                type="info"
                showIcon
              />
            )}
          </Space>
        </Card>
      )}

      {/* 步骤2：题目变形 */}
      {currentStep === 1 && parentProblem && (
        <Card title="步骤2：题目变形">
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {/* 母题显示 */}
            <Alert
              message="母题信息"
              description={
                <div>
                  <p><strong>内容：</strong>{parentProblem.content}</p>
                  <p><strong>答案：</strong>{parentProblem.answer}</p>
                </div>
              }
              type="success"
              showIcon
            />

            {/* 变形提示 */}
            <Card size="small">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text strong>变形提示词：</Text>
                <TextArea
                  value={transformPrompt}
                  onChange={(e) => setTransformPrompt(e.target.value)}
                  placeholder="请输入如何变形这道题目的提示，例如：将题目中的数字改为其他值，或改变题目的表述方式..."
                  rows={3}
                />
                <Space>
                  <Button
                    type="primary"
                    onClick={handleGenerateVariant}
                    disabled={!transformPrompt || variantCount >= BUSINESS_CONSTANTS.MAX_VARIANTS_PER_PROBLEM}
                  >
                    生成变体
                  </Button>
                  <Text type="secondary">
                    已生成 {variantCount}/{BUSINESS_CONSTANTS.MAX_VARIANTS_PER_PROBLEM}
                  </Text>
                </Space>
              </Space>
            </Card>

            {/* 变体列表 */}
            {variants.length > 0 && (
              <>
                <Divider>生成的变体</Divider>
                <Table
                  columns={variantColumns}
                  dataSource={variants}
                  rowKey="key"
                  pagination={false}
                />
              </>
            )}

            <Space>
              <Button onClick={() => setCurrentStep(0)}>返回上一步</Button>
              <Button
                type="primary"
                onClick={() => setCurrentStep(2)}
                disabled={variants.filter((v) => v.qualityCheckStatus === 'passed').length === 0}
              >
                下一步：提交合格题目
              </Button>
            </Space>
          </Space>
        </Card>
      )}

      {/* 步骤3：完成 */}
      {currentStep === 2 && (
        <Card title="步骤3：提交题目">
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Alert
              message="恭喜！"
              description={`您已完成 ${variants.filter((v) => v.qualityCheckStatus === 'passed').length} 个合格题目的创建。这些题目将进入人工质检流程。`}
              type="success"
              showIcon
            />

            <Table
              columns={variantColumns.slice(0, 2)}
              dataSource={variants.filter((v) => v.qualityCheckStatus === 'passed')}
              rowKey="key"
              pagination={false}
            />

            <Space>
              <Button onClick={() => setCurrentStep(1)}>返回上一步</Button>
              <Button
                type="primary"
                onClick={() => {
                  message.success('题目已提交！');
                  // 重置状态
                  setCurrentStep(0);
                  setParentProblem(null);
                  setVariants([]);
                  setVariantCount(0);
                }}
              >
                提交所有合格题目
              </Button>
            </Space>
          </Space>
        </Card>
      )}
    </div>
  );
}

