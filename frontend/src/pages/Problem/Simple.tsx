/**
 * 出题流程页面（简化版）
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
  Alert,
  Divider,
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
import { apiClient, problemApi } from '../../api';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface ProblemItem {
  key: string;
  id?: number;
  content: string;
  answer: string;
  explanation?: string;
  validationStatus?: 'pending' | 'validating' | 'passed' | 'failed';
  validationResult?: any; // 保存后端返回的完整验证结果
}

interface VariantItem {
  key: string;
  id?: number;
  content: string;
  answer: string;
  explanation?: string;
  qualityCheckStatus?: 'pending' | 'checking' | 'passed' | 'failed';
  quality_check?: any;
}

export default function ProblemSimple() {
  const [currentStep, setCurrentStep] = useState(0);

  // 步骤1：母题验证
  const [problems, setProblems] = useState<ProblemItem[]>([]);
  const [ocrLoading, setOcrLoading] = useState(false);

  // 步骤2：题目变形
  const [parentProblem, setParentProblem] = useState<ProblemItem | null>(null);
  const [transformPrompt, setTransformPrompt] = useState('');
  const [variants, setVariants] = useState<VariantItem[]>([]);
  const [variantCount, setVariantCount] = useState(0);

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
      // 将文件转为 base64
      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const result = reader.result as string;
          resolve(result.split(',')[1]);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
      
      // 调用后端OCR API
      const response = await apiClient.post('/problems/ocr', {
        image_base64: base64,
        extract_answer: true
      });
      
      const result = response.data;
      
      // 添加识别结果到问题列表
      setProblems([
        ...problems,
        {
          key: `problem-${Date.now()}`,
          content: result.problem || '',
          answer: result.answer || '',
          explanation: result.explanation || '',
          validationStatus: 'pending',
        },
      ]);
      message.success('OCR识别成功');
    } catch (error: any) {
      message.error(`OCR识别失败：${error.response?.data?.detail || error.message}`);
      console.error('OCR错误：', error);
    } finally {
      setOcrLoading(false);
    }
    return false;
  };

  const handleValidateSingle = async (problem: ProblemItem) => {
    if (!problem.content || !problem.answer) {
      message.warning('请填写完整的题目和答案');
      return;
    }

    // 设置验证中状态
    setProblems(
      problems.map((p) =>
        p.key === problem.key ? { ...p, validationStatus: 'validating' } : p
      )
    );
//
    try {
      // 调用真实后端API
      const response = await apiClient.post('/problems/validate', {
        problem: problem.content,
        answer: problem.answer,
        explanation: problem.explanation,
      });

      const result = response.data;

      // 更新状态
      setProblems(
        problems.map((p) =>
          p.key === problem.key
            ? { 
                ...p, 
                validationStatus: result.is_passed ? 'passed' : 'failed',
                validationResult: result
              }
            : p
        )
      );

      // 显示详细结果
      if (result.is_passed) {
        message.success(
          `验证通过！难度合格 - 正确率：${(result.correct_rate * 100).toFixed(1)}% (${result.correct_count}/${result.attempts}次)`
        );
      } else {
        message.warning(
          `${result.verdict} - 正确率：${(result.correct_rate * 100).toFixed(1)}% (${result.correct_count}/${result.attempts}次)`
        );
      }
    } catch (error: any) {
      setProblems(
        problems.map((p) =>
          p.key === problem.key ? { ...p, validationStatus: 'pending' } : p
        )
      );
      message.error(`验证失败：${error.response?.data?.detail || error.message}`);
      console.error('验证错误：', error);
    }
  };

  const handleValidateBatch = async () => {
    const validProblems = problems.filter((p) => p.content && p.answer);

    if (validProblems.length === 0) {
      message.warning('没有可验证的题目');
      return;
    }

    if (validProblems.length > 10) {
      message.warning('批量验证最多支持 10 个题目');
      return;
    }

    // 设置验证中
    const validKeys = validProblems.map((p) => p.key);
    setProblems(
      problems.map((p) =>
        validKeys.includes(p.key) ? { ...p, validationStatus: 'validating' } : p
      )
    );

    try {
      // 调用真实后端API
      const response = await apiClient.post('/problems/validate-batch', {
        problems: validProblems.map(p => ({
          problem: p.content,
          answer: p.answer,
          explanation: p.explanation,
        }))
      });

      const result = response.data;

      // 创建一个映射，key是题目内容，value是验证结果
      const resultMap = new Map();
      result.problems?.forEach((r: any, index: number) => {
        const originalProblem = validProblems[index];
        if (originalProblem) {
          resultMap.set(originalProblem.key, r);
        }
      });

      // 更新每个题目的结果
      setProblems(
        problems.map((p) => {
          const resultItem = resultMap.get(p.key);
          if (resultItem) {
            return {
              ...p,
              validationStatus: resultItem.is_passed ? 'passed' : 'failed',
              validationResult: resultItem,
            };
          }
          return p;
        })
      );

      message.success(
        `批量验证完成：${result.passed_count || 0}/${result.total_count || validProblems.length} 通过`
      );
    } catch (error: any) {
      setProblems(
        problems.map((p) =>
          validKeys.includes(p.key) ? { ...p, validationStatus: 'pending' } : p
        )
      );
      message.error(`批量验证失败：${error.response?.data?.detail || error.message}`);
      console.error('批量验证错误：', error);
    }
  };

  const problemColumns = [
    {
      title: '题目内容',
      dataIndex: 'content',
      key: 'content',
      width: '25%',
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
      width: '15%',
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
      title: '解析',
      dataIndex: 'explanation',
      key: 'explanation',
      width: '25%',
      render: (text: string, record: ProblemItem) => (
        <TextArea
          value={text || ''}
          onChange={(e) =>
            handleProblemChange(record.key, 'explanation', e.target.value)
          }
          placeholder="请输入解题步骤..."
          rows={3}
        />
      ),
    },
    {
      title: '验证状态',
      dataIndex: 'validationStatus',
      key: 'validationStatus',
      width: '10%',
      render: (status: string, record: ProblemItem) => {
        if (status === 'validating') {
          return <Tag icon={<SyncOutlined spin />} color="processing">验证中</Tag>;
        }
        if (status === 'passed') {
          return (
            <Space direction="vertical" size={0}>
              <Tag icon={<CheckCircleOutlined />} color="success">通过</Tag>
              {record.validationResult && (
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {record.validationResult.correct_count}/{record.validationResult.attempts}次正确
                </Text>
              )}
            </Space>
          );
        }
        if (status === 'failed') {
          return (
            <Space direction="vertical" size={0}>
              <Tag color="error">未通过</Tag>
              {record.validationResult && (
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {record.validationResult.correct_count}/{record.validationResult.attempts}次正确
                </Text>
              )}
            </Space>
          );
        }
        return <Tag color="default">待验证</Tag>;
      },
    },
    {
      title: '验证详情',
      key: 'details',
      width: '12%',
      render: (_: any, record: ProblemItem) => {
        if (record.validationResult) {
          const result = record.validationResult;
          return (
            <Space direction="vertical" size={0}>
              <Text style={{ fontSize: '12px' }}>
                正确率: {(result.correct_rate * 100).toFixed(1)}%
              </Text>
              <Text type={result.is_passed ? 'success' : 'warning'} style={{ fontSize: '12px' }}>
                {result.verdict || (result.is_passed ? '难度合格' : '题目太简单')}
              </Text>
            </Space>
          );
        }
        return <Text type="secondary" style={{ fontSize: '12px' }}>-</Text>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: '13%',
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
            onClick={async () => {
              if (!record.content || !record.answer || !record.explanation) {
                message.error('题目内容、答案或解析缺失，请填写完整');
                return;
              }
              try {
                message.loading('正在创建母题...', 0);
                const createdProblem = await problemApi.createProblem({
                  title: record.content.substring(0, 50) + '...',
                  content: { problem: record.content },
                  explanation: record.explanation,
                  answer: record.answer,
                  category: 'high_school_algebra',
                  source_type: 'manual',
                });
                message.destroy();
                message.success('母题创建成功');
                setParentProblem({ ...record, id: createdProblem.id });
                setCurrentStep(1);
              } catch (error: any) {
                message.destroy();
                message.error(`创建母题失败：${error.response?.data?.detail || error.message}`);
              }
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
    if (!parentProblem || !parentProblem.id) {
      message.error('母题信息缺失');
      return;
    }

    if (!transformPrompt) {
      message.warning('请填写变形提示词');
      return;
    }

    if (variantCount >= 10) {
      message.warning('每个母题最多可以变形 10 次');
      return;
    }

    try {
      message.loading('正在生成变体...', 0);
      const result = await problemApi.generateVariant(
        parentProblem.id,
        transformPrompt
      );

      if (result.success) {
        // 生成成功后，立即创建到数据库以便后续质检
        message.loading('正在保存变体...', 0);
        const createdVariant = await problemApi.createProblem({
          title: result.new_problem.substring(0, 50) + '...',
          content: { problem: result.new_problem },
          explanation: result.new_explanation,
          answer: result.new_answer,
          category: 'high_school_algebra',
          source_type: 'ai_variant',
          parent_problem_id: parentProblem.id,
        });
        
        message.destroy();
        
        const variant: VariantItem = {
          key: `variant-${Date.now()}`,
          id: createdVariant.id,
          content: result.new_problem,
          answer: result.new_answer,
          explanation: result.new_explanation,
          qualityCheckStatus: 'pending',
        };
        
        setVariants([...variants, variant]);
        setVariantCount(result.variant_count);
        message.success('题目变形成功！');
        setTransformPrompt('');
      } else {
        message.destroy();
        message.error('题目变形失败');
      }
    } catch (error: any) {
      message.destroy();
      message.error(`题目变形失败：${error.response?.data?.detail || error.message}`);
    }
  };

  const handleQualityCheck = async (variant: VariantItem) => {
    if (!variant.id) {
      message.error('变体信息缺失，无法进行质检');
      return;
    }

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
    } catch (error: any) {
      setVariants(
        variants.map((v) =>
          v.key === variant.key ? { ...v, qualityCheckStatus: 'failed' } : v
        )
      );
      message.error(`质量检查失败：${error.response?.data?.detail || error.message}`);
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
              <Space size="small">
                <Tag color="blue">难度✓</Tag>
                <Tag color="green">原创✓</Tag>
                <Tag color="purple">严谨✓</Tag>
              </Space>
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
          <Steps.Step title="母题验证" icon={<CheckCircleOutlined />} />
          <Steps.Step title="题目变形" icon={<ExperimentOutlined />} />
          <Steps.Step title="质量检查" icon={<SafetyCertificateOutlined />} />
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
                批量验证（最多10个）
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
                description="系统会使用AI模型测试8次，如果正确次数不超过4次，则认为题目难度合适。"
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
                  <p><strong>解析：</strong>{parentProblem.explanation}</p>
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
                    disabled={!transformPrompt || variantCount >= 10}
                  >
                    生成变体
                  </Button>
                  <Text type="secondary">
                    已生成 {variantCount}/10
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
                  setProblems([]);
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

