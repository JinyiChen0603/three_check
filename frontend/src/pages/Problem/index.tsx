/**
 * 出题流程页面
 */

import { useEffect, useRef, useState } from 'react';
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
  Modal,
} from 'antd';
import ReactMarkdown from 'react-markdown';
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
import { BUSINESS_CONSTANTS } from '../../config/constants';
import type { ProblemItem, VariantItem, ValidationStatus } from './types';

const { Title, Text } = Typography;
const { TextArea } = Input;

// 模型名称映射（将后端模型ID转换为友好名称）
const getModelDisplayName = (modelId?: string): string => {
  if (!modelId) return 'AI';
  
  const modelLower = modelId.toLowerCase();
  
  if (modelLower.includes('doubao') || modelLower.includes('seed')) {
    return '豆包';
  }
  if (modelLower.includes('gpt') || modelLower.includes('chatgpt') || modelLower.includes('openai')) {
    return 'ChatGPT';
  }
  if (modelLower.includes('zhipu') || modelLower.includes('glm')) {
    return '智谱GLM';
  }
  if (modelLower.includes('deepseek')) {
    return 'DeepSeek';
  }
  if (modelLower.includes('gemini')) {
    return 'Gemini';
  }
  
  // 如果无法识别，返回原始名称（去掉版本号等）
  return modelId.split('/').pop()?.split('-').slice(0, 2).join(' ') || modelId;
};

export default function ProblemCreation() {
  const [currentStep, setCurrentStep] = useState(0);

  // 步骤1：母题验证
  const [problems, setProblems] = useState<ProblemItem[]>([]);
  const problemsRef = useRef<ProblemItem[]>([]);
  const [ocrLoading, setOcrLoading] = useState(false);

  // 步骤2：题目变形（多母题）
  const [parentProblems, setParentProblems] = useState<Array<{ id: number; source: ProblemItem }>>([]);
  const [transformPrompts, setTransformPrompts] = useState<Record<number, string>>({});
  const [variantsMap, setVariantsMap] = useState<Record<number, VariantItem[]>>({});
  const [variantCountMap, setVariantCountMap] = useState<Record<number, number>>({});
  const [generatingVariants, setGeneratingVariants] = useState<Record<number, boolean>>({});

  const addParentProblem = (createdId: number, source: ProblemItem) => {
    setParentProblems((prev) => [...prev, { id: createdId, source }]);
    setVariantsMap((prev) => ({ ...prev, [createdId]: prev[createdId] || [] }));
    setVariantCountMap((prev) => ({ ...prev, [createdId]: prev[createdId] || 0 }));
    setTransformPrompts((prev) => ({ ...prev, [createdId]: prev[createdId] || '' }));
  };

  // ==================== 步骤1：母题验证 ====================

  const validationQueueRef = useRef<string[]>([]);
  const isProcessingRef = useRef(false);

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

  useEffect(() => {
    problemsRef.current = problems;
  }, [problems]);

  const handleRemoveProblem = (key: string) => {
    setProblems(problems.filter((p) => p.key !== key));
    validationQueueRef.current = validationQueueRef.current.filter((k) => k !== key);
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
    return false; // 阻止自动上传
  };

  const enqueueProblems = (keys: string[]) => {
    // 标记为排队中（仅对未通过/待验证状态更新）
    setProblems((prev) =>
      prev.map((p) =>
        keys.includes(p.key)
          ? {
              ...p,
              validationStatus:
                p.validationStatus === 'validating' || p.validationStatus === 'queued'
                  ? p.validationStatus
                  : ('queued' as ValidationStatus),
            }
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
    // 如果当前未在处理，则启动；若之前可能卡住，强制重启处理
    if (!isProcessingRef.current) {
      processQueue();
    } else if (validationQueueRef.current.length > 0) {
      isProcessingRef.current = false;
      processQueue();
    }
  };

  const processQueue = async () => {
    if (isProcessingRef.current) return;
    isProcessingRef.current = true;
    try {
      while (true) {
        const nextKey = validationQueueRef.current.shift();
        if (!nextKey) break;

        const current = problemsRef.current.find((p) => p.key === nextKey);
        if (!current) {
          continue;
        }

        setProblems((prev) => {
          const updated = prev.map((p) => {
            if (p.key === nextKey) {
              return { ...p, validationStatus: 'validating' as ValidationStatus };
            }
            // 保证同一时间只有一个“验证中”，其他非终态的保持排队
            if (p.validationStatus === 'validating') {
              return { ...p, validationStatus: 'queued' as ValidationStatus };
            }
            return p;
          });
          return updated;
        });

        try {
          const result = await problemApi.validateSingle(
            current.content,
            current.answer,
            current.explanation
          );
          // 直接使用后端返回的 is_passed 结果，而不是前端重新计算
          const passed = result.is_passed ?? false;
          setProblems((prev) =>
            prev.map((p) =>
              p.key === current!.key
                ? {
                    ...p,
                    validationStatus: (passed ? 'passed' : 'failed') as ValidationStatus,
                    validationResult: result,
                  }
                : p
            )
          );
        } catch (err) {
          setProblems((prev) =>
            prev.map((p) =>
              p.key === current!.key
                ? { ...p, validationStatus: 'failed' as ValidationStatus }
                : p
            )
          );
        }
      }
    } finally {
      isProcessingRef.current = false;
      // 如果运行过程中又有新任务入队，继续处理
      if (validationQueueRef.current.length > 0) {
        processQueue();
      }
    }
  };

  const handleValidateSingle = (problem: ProblemItem) => {
    if (!problem.content || !problem.answer) {
      message.warning('请填写完整的题目和答案');
      return;
    }
    enqueueProblems([problem.key]);
  };

  const handleValidateBatch = async () => {
    const validProblems = problems.filter(
      (p) => p.content && p.answer
    );

    if (validProblems.length === 0) {
      message.warning('没有可验证的题目');
      return;
    }

    // 并发上限（前端侧队列），避免一个卡住拖住全部
    const validKeys = validProblems.map((p) => p.key);

    // 标记排队
    setProblems(
      problems.map((p) =>
        validKeys.includes(p.key) ? { ...p, validationStatus: 'queued' } : p
      )
    );

    enqueueProblems(validProblems.map((p) => p.key));
    message.success('已加入验证队列');
  };

  const handleBatchUse = async () => {
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
        addParentProblem(created.id, item);
      }
      if (createdList.length > 0) {
        setCurrentStep(1);
        message.success(`批量使用成功，已创建 ${createdList.length} 个母题`);
      }
    } catch (error: any) {
      message.error('批量使用失败: ' + (error.response?.data?.detail || error.message));
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
          disabled={record.validationStatus === 'validating' || record.validationStatus === 'queued' || record.validationStatus === 'passed'}
          style={{
            fontWeight:
              record.validationStatus === 'passed' || record.validationStatus === 'failed'
                ? 600
                : undefined,
          }}
          onChange={(e) =>
            handleProblemChange(record.key, 'content', e.target.value)
          }
          placeholder="请输入题目内容..."
          rows={3}
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
          value={text}
          disabled={
            record.validationStatus === 'validating' ||
            record.validationStatus === 'queued' ||
            record.validationStatus === 'passed'
          }
          style={{
            fontWeight:
              record.validationStatus === 'passed' || record.validationStatus === 'failed'
                ? 600
                : undefined,
          }}
          onChange={(e) =>
            handleProblemChange(record.key, 'explanation', e.target.value)
          }
          placeholder="请输入解析（可选）..."
          rows={2}
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
          disabled={record.validationStatus === 'validating' || record.validationStatus === 'queued' || record.validationStatus === 'passed'}
          style={{
            fontWeight:
              record.validationStatus === 'passed' || record.validationStatus === 'failed'
                ? 600
                : undefined,
          }}
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
      width: '20%',
      render: (status: string, record: ProblemItem) => {
        if (status === 'queued') {
          return <Tag color="default">排队中</Tag>;
        }
        if (status === 'validating') {
          return <Tag icon={<SyncOutlined spin />} color="processing">验证中</Tag>;
        }
        if (status === 'passed' || status === 'failed') {
          const result = record.validationResult;
          const isPassed = status === 'passed';
          
          // 提取每个模型的结果
          const modelResults: Array<{ name: string; correct: number; total: number; passed: boolean }> = [];
          
          if (result?.chatgpt_result) {
            modelResults.push({
              name: 'ChatGPT',
              correct: result.chatgpt_result.correct_count ?? 0,
              total: result.chatgpt_result.attempts ?? BUSINESS_CONSTANTS.VALIDATION_ATTEMPTS,
              passed: result.chatgpt_result.is_passed ?? false,
            });
          }
          if (result?.zhipu_result) {
            modelResults.push({
              name: '智谱GLM',
              correct: result.zhipu_result.correct_count ?? 0,
              total: result.zhipu_result.attempts ?? BUSINESS_CONSTANTS.VALIDATION_ATTEMPTS,
              passed: result.zhipu_result.is_passed ?? false,
            });
          }
          
          // 如果没有分模型结果，使用旧的 correct_count（兼容豆包等单模型）
          if (modelResults.length === 0 && result?.correct_count !== undefined) {
            modelResults.push({
              name: getModelDisplayName(result.ai_model),
              correct: result.correct_count,
              total: result.attempts ?? BUSINESS_CONSTANTS.VALIDATION_ATTEMPTS,
              passed: isPassed,
            });
          }
          
          return (
            <div>
              <Tag icon={isPassed ? <CheckCircleOutlined /> : undefined} color={isPassed ? 'success' : 'error'}>
                {isPassed ? '通过' : '未通过'}
              </Tag>
              {modelResults.length > 0 && (
                <div style={{ marginTop: 4 }}>
                  {modelResults.map((m, idx) => (
                    <div key={idx} style={{ fontSize: 12, color: m.passed ? '#52c41a' : '#ff4d4f' }}>
                      {m.name}: {m.correct}/{m.total}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
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
            disabled={record.validationStatus !== 'passed'}
            onClick={async () => {
              if (record.validationStatus !== 'passed') {
                message.warning('请先验证题目并通过验证');
                return;
              }
              
              // 先创建母题到数据库
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
                
                addParentProblem(created.id, record);
                setCurrentStep(1);
                message.success('母题已保存到数据库，ID: ' + created.id);
              } catch (error: any) {
                console.error('保存母题失败:', error);
                message.error('保存母题失败: ' + (error.response?.data?.detail || error.message));
              }
            }}
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

  const handleGenerateVariant = async (parentId: number) => {
    const prompt = transformPrompts[parentId] || '';
    if (!prompt) {
      message.warning('请填写变形提示词');
      return;
    }

    const count = variantCountMap[parentId] || 0;
    if (count >= BUSINESS_CONSTANTS.MAX_VARIANTS_PER_PROBLEM) {
      message.warning(
        `每个母题最多可以变形 ${BUSINESS_CONSTANTS.MAX_VARIANTS_PER_PROBLEM} 次`
      );
      return;
    }

    // 设置 loading 状态
    setGeneratingVariants((prev) => ({ ...prev, [parentId]: true }));

    try {
      const variantResult = await problemApi.generateVariant(parentId, prompt);

      if (!variantResult || variantResult.success === false) {
        message.error(variantResult?.error || '生成变体失败');
        return;
      }

      const createdVariant = await problemApi.createProblem({
        title: `变体-${Date.now()}`,
        content: typeof variantResult.new_problem === 'string'
          ? { text: variantResult.new_problem }
          : variantResult.new_problem,
        explanation: variantResult.new_explanation,
        answer: variantResult.new_answer,
        category: 'high_school_comprehensive', // 默认分类
        source_type: 'ai_variant',
        parent_problem_id: parentId,
      });

      const newVariant = {
        ...createdVariant,
        key: `variant-${Date.now()}`,
        qualityCheckStatus: 'pending' as const,
      };

      setVariantsMap((prev) => ({
        ...prev,
        [parentId]: [
          ...(prev[parentId] || []),
          newVariant,
        ],
      }));
      setVariantCountMap((prev) => ({ ...prev, [parentId]: count + 1 }));
      message.success('题目变形成功并已保存到数据库！');
      setTransformPrompts((prev) => ({ ...prev, [parentId]: '' }));
    } catch (error: any) {
      console.error('❌ [DEBUG] 题目变形失败:', error);
      console.error('❌ [DEBUG] 错误详情:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
      });
      message.error('题目变形失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      // 清除 loading 状态
      setGeneratingVariants((prev) => ({ ...prev, [parentId]: false }));
    }
  };

  const handleQualityCheck = async (parentId: number, variant: VariantItem) => {
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
  };

  const handleSubmitForReview = async (parentId: number, variant: VariantItem) => {
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
          v.key === variant.key ? { ...v, human_review_status: 'pending_review' } : v
        ),
      }));
    } catch (error: any) {
      message.error('提交审核失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // ==================== 渲染 ====================

  return (
    <div>
      <Title level={2}>
        <FileTextOutlined /> 出题流程
      </Title>

      {/* 进度步骤 */}
      <Card style={{ marginBottom: 24 }}>
        <Steps
          current={currentStep}
          items={[
            { title: '母题验证', icon: <CheckCircleOutlined /> },
            { title: '题目变形', icon: <ExperimentOutlined /> },
            { title: '质量检查', icon: <SafetyCertificateOutlined /> },
          ]}
        />
      </Card>

      {/* 步骤1：母题验证 */}
      {currentStep === 0 && (
        <Card title="步骤1：母题验证">
          <Space orientation="vertical" style={{ width: '100%' }} size="large">
            <Alert
              title="准备母题"
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
                批量验证
              </Button>
              <Button
                onClick={handleBatchUse}
                disabled={problems.filter((p) => p.validationStatus === 'passed').length === 0}
              >
                批量使用
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
                description={`系统会使用 ChatGPT 和 智谱GLM 两个模型各测试${BUSINESS_CONSTANTS.VALIDATION_ATTEMPTS}次，每个模型正确次数不超过${BUSINESS_CONSTANTS.VALIDATION_THRESHOLD}次才算通过（两个都要通过）。`}
                type="info"
                showIcon
              />
            )}
          </Space>
        </Card>
      )}

      {/* 步骤2：题目变形（多母题列表） */}
      {currentStep === 1 && parentProblems.length > 0 && (
        <Card title="步骤2：题目变形">
          <Space orientation="vertical" style={{ width: '100%' }} size="large">
            {parentProblems.map((p, idx) => {
              const parentId = p.id;
              const promptValue = transformPrompts[parentId] || '';
              const variants = variantsMap[parentId] || [];
              const variantCount = variantCountMap[parentId] || 0;
              const columns = [
                {
                  title: '题目内容',
                  dataIndex: 'content',
                  key: 'content',
                  ellipsis: true,
                  render: (_: any, record: VariantItem) => {
                    // 处理 content 字段，可能是字符串或对象 {text: '...'}
                    const content = record.content;
                    
                    if (typeof content === 'string') {
                      return content;
                    }
                    
                    if (content && typeof content === 'object') {
                      const textValue = (content as any).text;
                      if (typeof textValue === 'string' && textValue.trim()) {
                        return textValue;
                      }
                      return JSON.stringify(content);
                    }
                    
                    return '';
                  },
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
                        <Space orientation="vertical" size="small">
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
                        onClick={() => handleQualityCheck(parentId, record)}
                        loading={record.qualityCheckStatus === 'checking'}
                      >
                        质检
                      </Button>
                      <Button
                        type="link"
                        size="small"
                        disabled={record.qualityCheckStatus !== 'passed'}
                        onClick={() => handleSubmitForReview(parentId, record)}
                      >
                        提交审核
                      </Button>
                      <Button
                        type="link"
                        size="small"
                        onClick={() => {
                          const contentText = typeof record.content === 'string'
                            ? record.content
                            : (record.content as any)?.text ?? String(record.content ?? '');
                          
                          // 获取质检结果（quality_check）
                          const qualityCheck = record.quality_check as any; // 使用 any 避免类型检查过于严格
                          const difficultyResult = qualityCheck?.difficulty;
                          
                          Modal.info({
                            title: '题目详情',
                            width: 900,
                            content: (
                              <div style={{ maxHeight: '70vh', overflow: 'auto' }}>
                                <div style={{ marginBottom: 16 }}>
                                  <strong style={{ fontSize: 14 }}>题目内容：</strong>
                                  <div style={{ 
                                    marginTop: 8, 
                                    padding: 12, 
                                    background: '#f5f5f5', 
                                    borderRadius: 6,
                                    lineHeight: 1.8
                                  }}>
                                    <ReactMarkdown>{contentText}</ReactMarkdown>
                                  </div>
                                </div>
                                <div style={{ marginBottom: 16 }}>
                                  <strong style={{ fontSize: 14 }}>答案：</strong>
                                  <div style={{ 
                                    marginTop: 8, 
                                    padding: 12, 
                                    background: '#e6f7ff', 
                                    borderRadius: 6,
                                    lineHeight: 1.8
                                  }}>
                                    <ReactMarkdown>{record.answer || ''}</ReactMarkdown>
                                  </div>
                                </div>
                                {record.explanation && (
                                  <div style={{ marginBottom: 16 }}>
                                    <strong style={{ fontSize: 14 }}>解析：</strong>
                                    <div style={{ 
                                      marginTop: 8, 
                                      padding: 12, 
                                      background: '#f6ffed', 
                                      borderRadius: 6,
                                      lineHeight: 1.8
                                    }}>
                                      <ReactMarkdown>{record.explanation}</ReactMarkdown>
                                    </div>
                                  </div>
                                )}
                                
                                {/* 显示质检结果中的AI模型评价 */}
                                {difficultyResult && (
                                  <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid #e8e8e8' }}>
                                    <strong style={{ fontSize: 14, color: '#1890ff' }}>AI模型评价：</strong>
                                    <div style={{ marginTop: 12 }}>
                                      {/* 双模型评价（从 difficulty 结果中提取） */}
                                      {difficultyResult.chatgpt_result?.evaluation && (
                                        <div style={{ marginBottom: 16 }}>
                                          <div style={{ 
                                            fontWeight: 600, 
                                            marginBottom: 8, 
                                            color: '#52c41a' 
                                          }}>
                                            ChatGPT：
                                          </div>
                                          <div style={{ 
                                            padding: 12, 
                                            background: '#f0f9ff', 
                                            borderRadius: 6,
                                            lineHeight: 1.8,
                                            fontSize: 13
                                          }}>
                                            {difficultyResult.chatgpt_result.evaluation}
                                          </div>
                                        </div>
                                      )}
                                      {difficultyResult.zhipu_result?.evaluation && (
                                        <div style={{ marginBottom: 16 }}>
                                          <div style={{ 
                                            fontWeight: 600, 
                                            marginBottom: 8, 
                                            color: '#722ed1' 
                                          }}>
                                            智谱GLM：
                                          </div>
                                          <div style={{ 
                                            padding: 12, 
                                            background: '#f9f0ff', 
                                            borderRadius: 6,
                                            lineHeight: 1.8,
                                            fontSize: 13
                                          }}>
                                            {difficultyResult.zhipu_result.evaluation}
                                          </div>
                                        </div>
                                      )}
                                      
                                      {/* 单模型评价（兼容旧格式） */}
                                      {!difficultyResult.chatgpt_result?.evaluation && 
                                       !difficultyResult.zhipu_result?.evaluation && 
                                       difficultyResult.evaluation && (
                                        <div>
                                          <div style={{ 
                                            fontWeight: 600, 
                                            marginBottom: 8, 
                                            color: '#1890ff' 
                                          }}>
                                            {getModelDisplayName(difficultyResult.ai_model)}：
                                          </div>
                                          <div style={{ 
                                            padding: 12, 
                                            background: '#f0f2f5', 
                                            borderRadius: 6,
                                            lineHeight: 1.8,
                                            fontSize: 13
                                          }}>
                                            {difficultyResult.evaluation}
                                          </div>
                                        </div>
                                      )}
                                      
                                      {/* 如果没有评价，显示提示 */}
                                      {!difficultyResult.chatgpt_result?.evaluation && 
                                       !difficultyResult.zhipu_result?.evaluation && 
                                       !difficultyResult.evaluation && (
                                        <Text type="secondary" style={{ fontSize: 12 }}>
                                          暂无AI评价（请先进行质检）
                                        </Text>
                                      )}
                                    </div>
                                  </div>
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
                        onClick={() =>
                          setVariantsMap((prev) => ({
                            ...prev,
                            [parentId]: (prev[parentId] || []).filter((v) => v.key !== record.key),
                          }))
                        }
                      >
                        删除
                      </Button>
                    </Space>
                  ),
                },
              ];

              return (
                <Card
                  key={parentId}
                  type="inner"
                  title={`母题 ${idx + 1}（ID: ${parentId}）`}
                  style={{ borderColor: '#f0f0f0' }}
                >
                  <Space orientation="vertical" style={{ width: '100%' }} size="middle">
                    <Alert
                      message="母题信息"
                      description={
                        <div>
                          <p><strong>内容：</strong>{p.source.content}</p>
                          <p><strong>答案：</strong>{p.source.answer}</p>
                        </div>
                      }
                      type="success"
                      showIcon
                    />

                    <Card size="small">
                      <Space orientation="vertical" style={{ width: '100%' }}>
                        <Text strong>变形提示词：</Text>
                        <TextArea
                          value={promptValue}
                          onChange={(e) =>
                            setTransformPrompts((prev) => ({ ...prev, [parentId]: e.target.value }))
                          }
                          placeholder="请输入如何变形这道题目的提示，例如：将题目中的数字改为其他值，或改变题目的表述方式..."
                          rows={3}
                        />
                        <Space>
                          <Button
                            type="primary"
                            onClick={() => handleGenerateVariant(parentId)}
                            loading={generatingVariants[parentId] || false}
                            disabled={
                              generatingVariants[parentId] ||
                              !promptValue ||
                              variantCount >= BUSINESS_CONSTANTS.MAX_VARIANTS_PER_PROBLEM
                            }
                          >
                            生成变体
                          </Button>
                          <Text type="secondary">
                            已生成 {variantCount}/{BUSINESS_CONSTANTS.MAX_VARIANTS_PER_PROBLEM}
                          </Text>
                        </Space>
                      </Space>
                    </Card>

                    {variants.length > 0 && (
                      <>
                        <Divider>生成的变体</Divider>
                        <Table
                          columns={columns}
                          dataSource={variants}
                          rowKey="key"
                          pagination={false}
                        />
                      </>
                    )}
                  </Space>
                </Card>
              );
            })}

            <Space>
              <Button onClick={() => setCurrentStep(0)}>返回上一步</Button>
              <Button
                type="primary"
                onClick={() => setCurrentStep(2)}
                disabled={
                  Object.values(variantsMap)
                    .flat()
                    .filter((v) => v.qualityCheckStatus === 'passed' && v.human_review_status === 'pending_review').length === 0
                }
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
          <Space orientation="vertical" style={{ width: '100%' }} size="large">
            {(() => {
              const allVariants = Object.values(variantsMap).flat();
              const passedVariants = allVariants.filter((v) => v.qualityCheckStatus === 'passed' && v.human_review_status === 'pending_review');
              return (
                <>
                  <Alert
                    message="恭喜！"
                    description={`您已完成 ${passedVariants.length} 个合格题目的创建。这些题目将进入人工质检流程。`}
                    type="success"
                    showIcon
                  />

                  <Table
                    columns={[
                      { title: '题目内容', dataIndex: 'content', key: 'content', ellipsis: true },
                      { title: '答案', dataIndex: 'answer', key: 'answer', ellipsis: true },
                    ]}
                    dataSource={passedVariants}
                    rowKey="key"
                    pagination={false}
                  />

                  <Space>
                    <Button onClick={() => setCurrentStep(1)}>返回上一步</Button>
                    <Button
                      type="primary"
                      onClick={async () => {
                        try {
                          if (passedVariants.length === 0) {
                            message.warning('没有合格的题目可以提交');
                            return;
                          }
                          message.success(`已提交 ${passedVariants.length} 个合格题目到数据库！`);
                          // 重置状态
                          setCurrentStep(0);
                          setParentProblems([]);
                          setTransformPrompts({});
                          setVariantsMap({});
                          setVariantCountMap({});
                        } catch (error: any) {
                          message.error('提交失败: ' + (error.response?.data?.detail || error.message));
                        }
                      }}
                    >
                      提交所有合格题目
                    </Button>
                  </Space>
                </>
              );
            })()}
          </Space>
        </Card>
      )}
    </div>
  );
}

