/**
 * 题目验证与导出页面
 * 单页面设计：所有功能在一个界面
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Space,
  Typography,
  Input,
  Select,
  Form,
  message,
  Table,
  Tag,
  Divider,
  Modal,
  Spin,
  Statistic,
  Row,
  Col,
  Descriptions,
  Alert,
  Upload,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DownloadOutlined,
  DeleteOutlined,
  PlusOutlined,
  SyncOutlined,
  FileExcelOutlined,
  SafetyCertificateOutlined,
  ExperimentOutlined,
  EyeOutlined,
  EditOutlined,
  SaveOutlined,
  RadarChartOutlined,
  PictureOutlined,
} from '@ant-design/icons';
import { problemApi } from '../../api';
import { MATERIAL_CATEGORIES } from '../../config/constants';
import MathRenderer from '../../components/MathRenderer';
import { useTask } from '../../hooks/useTask';
import { TaskType } from '../../config/constants';
import { useAuthStore } from '../../store/useAuthStore';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface CheckStatus {
  loading: boolean;
  result: any | null;
  passed: boolean | null;
}

interface ProblemFormData {
  problem: string;
  answer: string;
  explanation: string;
}

interface ExportListItem {
  id: number;
  content?: string;  // 题目内容
  answer?: string;  // 答案
  explanation?: string;  // 解析
  difficulty_passed: boolean | null;
  originality_passed: boolean | null;
  rigor_passed: boolean | null;
  difficulty_validation?: any;  // 完整的难度检测结果
  originality_check?: any;  // 完整的原创性检测结果
  rigor_check?: any;  // 完整的严谨性检测结果
  created_at: string;
}

export default function TotalPage() {
  const [form] = Form.useForm<ProblemFormData>();
  
  // 任务管理Hook
  const { tasks, refreshTasks, problemCreationTotal, problemCreationCompleted } = useTask();
  
  // 用户信息刷新
  const fetchCurrentUser = useAuthStore((state) => state.fetchCurrentUser);

  // 三个检测状态
  const [difficultyCheck, setDifficultyCheck] = useState<CheckStatus>({
    loading: false,
    result: null,
    passed: null,
  });
  const [originalityCheck, setOriginalityCheck] = useState<CheckStatus>({
    loading: false,
    result: null,
    passed: null,
  });
  const [rigorCheck, setRigorCheck] = useState<CheckStatus>({
    loading: false,
    result: null,
    passed: null,
  });

  // 用于取消请求的控制器
  const [abortControllers, setAbortControllers] = useState<{
    difficulty?: AbortController;
    originality?: AbortController;
    rigor?: AbortController;
  }>({});

  // 导出列表
  const [exportList, setExportList] = useState<ExportListItem[]>([]);
  const [exportStats, setExportStats] = useState({ total: 0, passed: 0, failed: 0 });
  const [loadingList, setLoadingList] = useState(false);
  const [exporting, setExporting] = useState<'passed' | 'all' | null>(null);
  const [savingToList, setSavingToList] = useState(false);
  
  // 获取进行中的出题任务
  const inProgressTask = tasks.find(
    (t) => t.task_type === TaskType.PROBLEM_CREATION && t.status === 'in_progress'
  );

  // Modal状态
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [viewModalContent, setViewModalContent] = useState<{
    title: string;
    data: any;
  } | null>(null);
  
  // 查看题目Modal状态
  const [viewProblemModalVisible, setViewProblemModalVisible] = useState(false);
  const [viewProblemData, setViewProblemData] = useState<ExportListItem | null>(null);

  // 计算是否有任何检测正在进行
  const isAnyCheckRunning =
    difficultyCheck.loading || originalityCheck.loading || rigorCheck.loading;

  // 计算是否有任何检测已完成
  const hasAnyCheckCompleted =
    difficultyCheck.result !== null ||
    originalityCheck.result !== null ||
    rigorCheck.result !== null;

  // 表单字段是否应该被禁用（检测中或检测完成后）
  const formFieldsDisabled = isAnyCheckRunning || hasAnyCheckCompleted;

  // 是否可以保存到列表（三个检测都完成即可，无论是否通过）
  const canSaveToList =
    difficultyCheck.result !== null &&
    originalityCheck.result !== null &&
    rigorCheck.result !== null;

  // 验证难度
  const handleCheckDifficulty = async () => {
    try {
      await form.validateFields(['problem', 'answer']);
      const values = form.getFieldsValue();

      // 创建 AbortController
      const controller = new AbortController();
      setAbortControllers(prev => ({ ...prev, difficulty: controller }));

      setDifficultyCheck({ loading: true, result: null, passed: null });
      
      try {
        const result = await problemApi.validateSingle(
          values.problem,
          values.answer,
          values.explanation
        );

        // 检查是否已被取消
        if (controller.signal.aborted) {
          return;
        }

        // 检查attempts_details中是否有error
        const hasError = result.attempts_details?.some(
          (detail: any) => detail.error
        );
        
        setDifficultyCheck({
          loading: false,
          result: result,
          passed: hasError ? false : (result.is_passed || false),
        });

        if (hasError) {
          const errorMsg = result.attempts_details?.find((d: any) => d.error)?.error || '检测出错';
          message.error(`❌ 难度检测出错: ${errorMsg}`);
        } else if (result.is_passed) {
          message.success('✅ 难度检测通过');
        } else {
          message.warning('⚠️ 难度检测未通过');
        }
      } catch (error: any) {
        // 如果是取消操作，不显示错误
        if (controller.signal.aborted) {
          return;
        }
        throw error;
      } finally {
        setAbortControllers(prev => ({ ...prev, difficulty: undefined }));
      }
    } catch (error: any) {
      console.error('难度检测失败:', error);
      setDifficultyCheck({ loading: false, result: null, passed: false });
      if (!error.errorFields) {
        message.error('难度检测失败，请重试');
      }
    }
  };

  // 检测原创性
  const handleCheckOriginality = async () => {
    try {
      await form.validateFields(['problem', 'answer']);
      const values = form.getFieldsValue();

      // 创建 AbortController
      const controller = new AbortController();
      setAbortControllers(prev => ({ ...prev, originality: controller }));

      setOriginalityCheck({ loading: true, result: null, passed: null });
      
      try {
        const result = await problemApi.checkOriginality(
          values.problem,
          values.answer,
          values.explanation
        );

        // 检查是否已被取消
        if (controller.signal.aborted) {
          return;
        }

        // 检查是否有error
        const hasError = !result.success || result.originality?.error;
        
        const passed = hasError ? false : (result.originality?.is_original || false);
        setOriginalityCheck({
          loading: false,
          result: result.originality,
          passed: passed,
        });

        if (hasError) {
          const errorMsg = result.originality?.error || result.error || '检测出错';
          message.error(`❌ 原创性检测出错: ${errorMsg}`);
        } else if (passed) {
          message.success('✅ 原创性检测通过');
        } else {
          message.warning('⚠️ 原创性检测未通过');
        }
      } catch (error: any) {
        // 如果是取消操作，不显示错误
        if (controller.signal.aborted) {
          return;
        }
        throw error;
      } finally {
        setAbortControllers(prev => ({ ...prev, originality: undefined }));
      }
    } catch (error: any) {
      console.error('原创性检测失败:', error);
      setOriginalityCheck({ loading: false, result: null, passed: false });
      if (!error.errorFields) {
        message.error('原创性检测失败，请重试');
      }
    }
  };

  // 检测严谨性
  const handleCheckRigor = async () => {
    try {
      await form.validateFields(['problem', 'answer']);
      const values = form.getFieldsValue();

      // 创建 AbortController
      const controller = new AbortController();
      setAbortControllers(prev => ({ ...prev, rigor: controller }));

      setRigorCheck({ loading: true, result: null, passed: null });
      
      try {
        const result = await problemApi.checkRigor(
          values.problem,
          values.answer,
          values.explanation
        );

        // 检查是否已被取消
        if (controller.signal.aborted) {
          return;
        }

        // 检查是否有error
        const hasError = !result.success || result.rigor?.error;
        
        const passed = hasError ? false : (result.rigor?.is_rigorous || false);
        setRigorCheck({
          loading: false,
          result: result.rigor,
          passed: passed,
        });

        if (hasError) {
          const errorMsg = result.rigor?.error || result.error || '检测出错';
          message.error(`❌ 严谨性检测出错: ${errorMsg}`);
        } else if (passed) {
          message.success('✅ 严谨性检测通过');
        } else {
          message.warning('⚠️ 严谨性检测未通过');
        }
      } catch (error: any) {
        // 如果是取消操作，不显示错误
        if (controller.signal.aborted) {
          return;
        }
        throw error;
      } finally {
        setAbortControllers(prev => ({ ...prev, rigor: undefined }));
      }
    } catch (error: any) {
      console.error('严谨性检测失败:', error);
      setRigorCheck({ loading: false, result: null, passed: false });
      if (!error.errorFields) {
        message.error('严谨性检测失败，请重试');
      }
    }
  };

  // 查看检测报告
  const handleViewReport = (type: 'difficulty' | 'originality' | 'rigor') => {
    let title = '';
    let data = null;

    switch (type) {
      case 'difficulty':
        title = '难度检测报告';
        data = difficultyCheck.result;
        break;
      case 'originality':
        title = '原创性检测报告';
        data = originalityCheck.result;
        break;
      case 'rigor':
        title = '严谨性检测报告';
        data = rigorCheck.result;
        break;
    }

    if (!data) {
      message.warning('请先进行检测');
      return;
    }

    setViewModalContent({ title, data });
    setViewModalVisible(true);
  };

  // 保存到列表
  const handleSaveToList = async () => {
    if (!canSaveToList || savingToList) {
      if (!canSaveToList) {
        message.warning('请先完成所有检测');
      }
      return;
    }

    try {
      setSavingToList(true);
      await form.validateFields();
      const values = form.getFieldsValue();

      const result = await problemApi.validateAndSave({
        problem: values.problem,
        answer: values.answer,
        explanation: values.explanation,
        include_difficulty: false,
      });

      const taskProgress = result.task_progress;
      const progressMsg = taskProgress 
        ? `（进度：${taskProgress.completed}/${taskProgress.total}，剩余：${taskProgress.remaining}）`
        : '';
      
          message.success(`✅ 题目已保存到导出列表${progressMsg}`);
          
          // 刷新列表、任务和用户信息（用于更新仪表盘）
          await loadExportList();
          await refreshTasks();
          await fetchCurrentUser();
          
          // 重置表单和检测状态
          handleReset();
    } catch (error: any) {
      console.error('保存失败:', error);
      const errorMsg = error.response?.data?.detail || error.message || '保存失败，请重试';
      message.error(errorMsg);
    } finally {
      setSavingToList(false);
    }
  };

  // 删除题目（重置）
  const handleDelete = () => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除当前题目吗？所有检测结果将被清空。',
      okText: '确认',
      cancelText: '取消',
      okType: 'danger',
      onOk: handleReset,
    });
  };

  // 重置表单和状态
  const handleReset = () => {
    form.resetFields();
    setDifficultyCheck({ loading: false, result: null, passed: null });
    setOriginalityCheck({ loading: false, result: null, passed: null });
    setRigorCheck({ loading: false, result: null, passed: null });
  };

  // 修改题目（增强版：停止检测并清除报告）
  const handleModify = () => {
    // 如果有检测正在进行，取消所有检测
    if (isAnyCheckRunning) {
      // 取消所有正在进行的请求
      Object.values(abortControllers).forEach(controller => {
        if (controller) {
          controller.abort();
        }
      });
      
      message.warning('已停止所有正在进行的检测');
    }

    // 重置所有检测状态和报告
    setDifficultyCheck({ loading: false, result: null, passed: null });
    setOriginalityCheck({ loading: false, result: null, passed: null });
    setRigorCheck({ loading: false, result: null, passed: null });
    
    // 清空 AbortController
    setAbortControllers({});
    
    message.info('已清除所有检测结果，可以修改题目');
  };

  // 图片识别处理
  const [recognizing, setRecognizing] = useState(false);

  const handleImageRecognize = async (file: File) => {
    // 检查文件类型
    const isImage = file.type.startsWith('image/');
    if (!isImage) {
      message.error('只能上传图片文件！');
      return false;
    }

    // 检查文件大小（限制为5MB）
    const isLt5M = file.size / 1024 / 1024 < 5;
    if (!isLt5M) {
      message.error('图片大小不能超过 5MB！');
      return false;
    }

    try {
      setRecognizing(true);
      message.loading('正在识别图片...', 0);
      
      const result = await problemApi.ocrImage(file);
      
      message.destroy(); // 清除loading消息
      
      if (result.success) {
        // 填充表单
        const formData: any = {};
        
        if (result.problem) {
          formData.problem = result.problem;
        }
        
        if (result.answer) {
          formData.answer = result.answer;
        }
        
        // 如果有解析也填充（根据OCR服务返回的字段调整）
        if (result.explanation) {
          formData.explanation = result.explanation;
        }
        
        form.setFieldsValue(formData);
        
        message.success('✅ 图片识别成功！已自动填充表单');
      } else {
        message.error(result.error || '识别失败，请重试');
      }
    } catch (error: any) {
      console.error('图片识别失败:', error);
      message.destroy();
      message.error('图片识别失败，请重试');
    } finally {
      setRecognizing(false);
    }
    
    return false; // 阻止默认上传行为
  };

  // 加载导出列表
  const loadExportList = async () => {
    setLoadingList(true);
    try {
      const data = await problemApi.getExportList();
      setExportList(data.problems || []);
      setExportStats({
        total: data.total || 0,
        passed: data.passed || 0,
        failed: data.failed || 0,
      });
    } catch (error) {
      console.error('加载列表失败:', error);
      message.error('加载导出列表失败');
    } finally {
      setLoadingList(false);
    }
  };

  // 导出Excel
  const handleExport = async (onlyPassed: boolean = true) => {
    setExporting(onlyPassed ? 'passed' : 'all');
    try {
      const blob = await problemApi.exportValidated(onlyPassed);

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `验证题目_${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      message.success('✅ 导出成功！');
      await loadExportList();
    } catch (error) {
      console.error('导出失败:', error);
      message.error('导出失败，请重试');
    } finally {
      setExporting(null);
    }
  };

  // 清空列表
  const handleClearList = () => {
    Modal.confirm({
      title: '确认清空',
      content: '确定要清空待导出列表吗？清空后任务进度会重置，可以重新出题。',
      okText: '确认',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await problemApi.clearExportList();
          message.success('✅ 列表已清空，任务进度已重置');
          // 刷新列表、任务和用户信息（用于更新仪表盘）
          await loadExportList();
          await refreshTasks();
          await fetchCurrentUser();
        } catch (error: any) {
          console.error('清空失败:', error);
          const errorMsg = error.response?.data?.detail || error.message || '清空失败，请重试';
          message.error(errorMsg);
        }
      },
    });
  };

  // 初始化加载列表和任务
  useEffect(() => {
    loadExportList();
    refreshTasks();
  }, []);

  // 查看题目详情
  const handleViewProblem = (record: ExportListItem) => {
    setViewProblemData(record);
    setViewProblemModalVisible(true);
  };

  // 删除单个题目
  const handleDeleteProblem = async (problemId: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这道题目吗？删除后可以继续出题。',
      okText: '确认',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          const result = await problemApi.deleteValidatedProblem(problemId);
          const taskProgress = result.task_progress;
          const progressMsg = taskProgress 
            ? `（进度：${taskProgress.completed}/${taskProgress.total}，剩余：${taskProgress.remaining}）`
            : '';
          
          message.success(`✅ 题目已删除${progressMsg}`);
          
          // 刷新列表、任务和用户信息（用于更新仪表盘）
          await loadExportList();
          await refreshTasks();
          await fetchCurrentUser();
        } catch (error: any) {
          console.error('删除失败:', error);
          const errorMsg = error.response?.data?.detail || error.message || '删除失败，请重试';
          message.error(errorMsg);
        }
      },
    });
  };

  // 表格列定义
  const columns = [
    {
      title: '序号',
      key: 'index',
      width: 80,
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: '题目内容',
      dataIndex: 'content',
      key: 'content',
      width: 300,
      ellipsis: true,
      render: (text: string) => (
        <Text ellipsis={{ tooltip: text }} style={{ maxWidth: 300 }}>
          {text || '-'}
        </Text>
      ),
    },
    {
      title: '标准答案',
      dataIndex: 'answer',
      key: 'answer',
      width: 200,
      ellipsis: true,
      render: (text: string) => (
        <Text ellipsis={{ tooltip: text }} style={{ maxWidth: 200 }}>
          {text || '-'}
        </Text>
      ),
    },
    {
      title: '难度',
      dataIndex: 'difficulty_passed',
      key: 'difficulty_passed',
      width: 100,
      render: (passed: boolean | null) =>
        passed === null ? (
          <Tag color="default">未检测</Tag>
        ) : passed ? (
          <Tag icon={<CheckCircleOutlined />} color="success">
            通过
          </Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="error">
            未通过
          </Tag>
        ),
    },
    {
      title: '原创性',
      dataIndex: 'originality_passed',
      key: 'originality_passed',
      width: 100,
      render: (passed: boolean | null) =>
        passed === null ? (
          <Tag color="default">未检测</Tag>
        ) : passed ? (
          <Tag icon={<CheckCircleOutlined />} color="success">
            通过
          </Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="error">
            未通过
          </Tag>
        ),
    },
    {
      title: '严谨性',
      dataIndex: 'rigor_passed',
      key: 'rigor_passed',
      width: 100,
      render: (passed: boolean | null) =>
        passed === null ? (
          <Tag color="default">未检测</Tag>
        ) : passed ? (
          <Tag icon={<CheckCircleOutlined />} color="success">
            通过
          </Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="error">
            未通过
          </Tag>
        ),
    },
    {
      title: '综合结果',
      key: 'result',
      width: 100,
      render: (_: any, record: ExportListItem) => {
        // 只有当两个检测都完成且都通过时，才显示合格
        const originalityPassed = record.originality_passed === true;
        const rigorPassed = record.rigor_passed === true;
        const allPassed = originalityPassed && rigorPassed;
        
        // 如果任一检测未完成（null），显示未完成
        if (record.originality_passed === null || record.rigor_passed === null) {
          return (
            <Tag color="default">未完成</Tag>
          );
        }
        
        return allPassed ? (
          <Tag icon={<CheckCircleOutlined />} color="success">
            合格
          </Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="warning">
            不合格
          </Tag>
        );
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: ExportListItem) => (
        <Space>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewProblem(record)}
          >
            查看
          </Button>
          <Button
            danger
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteProblem(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  // 渲染检测按钮
  const renderCheckButton = (
    label: string,
    icon: React.ReactNode,
    check: CheckStatus,
    onCheck: () => void,
    onView: () => void
  ) => {
    return (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Button
          type={check.passed === true ? 'primary' : 'default'}
          danger={check.passed === false}
          icon={icon}
          loading={check.loading}
          onClick={onCheck}
          block
          size="large"
          style={{ height: 48 }}
        >
          {check.loading
            ? '检测中...'
            : check.passed === null
            ? label
            : check.result?.error || (check.result?.attempts_details?.some((d: any) => d.error))
            ? `${label}出错`
            : check.passed
            ? `${label}通过`
            : `${label}未通过`}
        </Button>
        <Button
          icon={<EyeOutlined />}
          onClick={onView}
          disabled={!check.result}
          block
        >
          查看报告
        </Button>
      </Space>
    );
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 顶部标题 */}
      <Card style={{ marginBottom: 24 }}>
        <Title level={2}>
          <FileExcelOutlined /> 题目验证与导出
        </Title>
        <Paragraph type="secondary">
          填写题目信息 → 三重检测（难度+原创性+严谨性）→ 保存到列表 → 批量导出Excel
        </Paragraph>
        
        {/* 任务状态提示 */}
        {inProgressTask ? (
          <Alert
            message={`出题任务进度：${inProgressTask.completed_count || 0} / ${inProgressTask.total_count || 0}`}
            description={`您已领取 ${inProgressTask.total_count || 0} 道出题任务，已保存 ${inProgressTask.completed_count || 0} 道题目，还可保存 ${(inProgressTask.total_count || 0) - (inProgressTask.completed_count || 0)} 道题目。`}
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        ) : (
          <Alert
            message="请先在任务管理中领取出题任务"
            description="您需要先领取出题任务才能保存题目。请前往任务管理页面领取任务。"
            type="warning"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Card>

      {/* 题目输入区 */}
      <Card title="题目信息" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical">
          <Form.Item
            label="题目内容"
            name="problem"
            rules={[{ required: true, message: '请输入题目内容' }]}
          >
            <TextArea
              rows={6}
              placeholder="请输入题目内容（支持LaTeX公式，如 $x^2$）"
              disabled={formFieldsDisabled}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="标准答案"
                name="answer"
                rules={[{ required: true, message: '请输入标准答案' }]}
              >
                <Input placeholder="请输入标准答案" disabled={formFieldsDisabled} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="题目解析"
                name="explanation"
                rules={[{ required: true, message: '请输入题目解析' }]}
              >
                <Input placeholder="请输入题目解析" disabled={formFieldsDisabled} />
              </Form.Item>
            </Col>
          </Row>
        </Form>

        {/* 操作按钮 */}
        <Space style={{ marginTop: 16 }}>
          <Button 
            icon={<EditOutlined />} 
            onClick={handleModify}
            disabled={!formFieldsDisabled}
            type={isAnyCheckRunning ? 'primary' : 'default'}
            danger={isAnyCheckRunning}
          >
            {isAnyCheckRunning ? '停止检测并修改' : '修改题目'}
          </Button>
          
          <Upload
            accept="image/*"
            showUploadList={false}
            beforeUpload={handleImageRecognize}
            disabled={formFieldsDisabled}
          >
            <Button 
              icon={<PictureOutlined />}
              loading={recognizing}
              disabled={formFieldsDisabled}
            >
              {recognizing ? '识别中...' : '图片识别'}
            </Button>
          </Upload>
        </Space>
      </Card>

      {/* 三重检测区 */}
      <Card title="三重检测" style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={8}>
            {renderCheckButton(
              '难度检测',
              <ExperimentOutlined />,
              difficultyCheck,
              handleCheckDifficulty,
              () => handleViewReport('difficulty')
            )}
          </Col>
          <Col span={8}>
            {renderCheckButton(
              '原创性检测',
              <SafetyCertificateOutlined />,
              originalityCheck,
              handleCheckOriginality,
              () => handleViewReport('originality')
            )}
          </Col>
          <Col span={8}>
            {renderCheckButton(
              '严谨性检测',
              <RadarChartOutlined />,
              rigorCheck,
              handleCheckRigor,
              () => handleViewReport('rigor')
            )}
          </Col>
        </Row>

        {/* 检测状态提示 */}
        {canSaveToList && (
          <Alert
            message="✅ 所有检测已完成！"
            description={`难度检测：${difficultyCheck.passed ? '通过' : '未通过'} | 原创性检测：${originalityCheck.passed ? '通过' : '未通过'} | 严谨性检测：${rigorCheck.passed ? '通过' : '未通过'} - 非最终采纳结果`}
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}

        {/* 保存按钮 */}
        <Divider />
        <Button
          type="primary"
          size="large"
          icon={<SaveOutlined />}
          onClick={handleSaveToList}
          disabled={!canSaveToList || savingToList}
          loading={savingToList}
          block
          style={{ height: 56, fontSize: 16 }}
        >
          {savingToList ? '保存中...' : canSaveToList ? '保存到导出列表' : '请完成所有检测后保存'}
        </Button>
      </Card>

      {/* 导出列表区 */}
      <Card title="导出列表" style={{ marginBottom: 24 }}>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={8}>
            <Statistic
              title="总题目数"
              value={exportStats.total}
              prefix={<FileExcelOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="通过质检"
              value={exportStats.passed}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="未通过"
              value={exportStats.failed}
              valueStyle={{ color: '#cf1322' }}
              prefix={<CloseCircleOutlined />}
            />
          </Col>
        </Row>

        <Space style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            loading={exporting === 'passed'}
            onClick={() => handleExport(true)}
            disabled={exportStats.passed === 0 || exporting !== null}
          >
            导出通过的题目
          </Button>
          <Button
            icon={<DownloadOutlined />}
            loading={exporting === 'all'}
            onClick={() => handleExport(false)}
            disabled={exportStats.total === 0 || exporting !== null}
          >
            导出全部题目
          </Button>
          <Button icon={<SyncOutlined />} onClick={loadExportList}>
            刷新列表
          </Button>
          <Button
            danger
            icon={<DeleteOutlined />}
            onClick={handleClearList}
            disabled={exportStats.total === 0}
          >
            清空列表
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={exportList}
          rowKey="id"
          loading={loadingList}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* 查看报告Modal */}
      <Modal
        title={viewModalContent?.title}
        open={viewModalVisible}
        onCancel={() => setViewModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setViewModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={700}
      >
        {viewModalContent && (
          <div>
            {viewModalContent.title === '难度检测报告' && (
              <Descriptions bordered column={1}>
                <Descriptions.Item label="检测结果">
                  {(() => {
                    // 检查attempts_details中是否有error
                    const hasError = viewModalContent.data.attempts_details?.some(
                      (detail: any) => detail.error
                    );
                    
                    if (hasError) {
                      return <Tag color="error">检测出错</Tag>;
                    }
                    
                    return viewModalContent.data.is_passed ? (
                      <Tag color="success">通过</Tag>
                    ) : (
                      <Tag color="error">未通过</Tag>
                    );
                  })()}
                </Descriptions.Item>
                {(() => {
                  // 检查是否有错误详情
                  const errorDetails = viewModalContent.data.attempts_details?.filter(
                    (detail: any) => detail.error
                  );
                  
                  if (errorDetails && errorDetails.length > 0) {
                    return (
                      <Descriptions.Item label="错误信息">
                        <Alert
                          type="error"
                          message="检测过程中出现错误"
                          description={
                            <ul style={{ margin: 0, paddingLeft: 20 }}>
                              {errorDetails.map((detail: any, index: number) => (
                                <li key={index}>{detail.error}</li>
                              ))}
                            </ul>
                          }
                        />
                      </Descriptions.Item>
                    );
                  }
                  return null;
                })()}
                <Descriptions.Item label="正确次数">
                  {viewModalContent.data.correct_count || 0} /{' '}
                  {viewModalContent.data.total_attempts || viewModalContent.data.attempts || 8}
                </Descriptions.Item>
                <Descriptions.Item label="结论">
                  {viewModalContent.data.verdict || '未知'}
                </Descriptions.Item>
                {viewModalContent.data.recommendation && (
                  <Descriptions.Item label="建议">
                    {viewModalContent.data.recommendation}
                  </Descriptions.Item>
                )}
              </Descriptions>
            )}

            {viewModalContent.title === '原创性检测报告' && (
              <Descriptions bordered column={1}>
                <Descriptions.Item label="检测结果">
                  {viewModalContent.data.error ? (
                    <Tag color="error">检测出错</Tag>
                  ) : viewModalContent.data.is_original ? (
                    <Tag color="success">原创</Tag>
                  ) : (
                    <Tag color="error">非原创</Tag>
                  )}
                </Descriptions.Item>
                {viewModalContent.data.error && (
                  <Descriptions.Item label="错误信息">
                    <Alert
                      type="error"
                      message="检测过程中出现错误"
                      description={viewModalContent.data.error}
                    />
                  </Descriptions.Item>
                )}
                {viewModalContent.data.originality_score && (
                  <Descriptions.Item label="原创性分数">
                    {viewModalContent.data.originality_score}
                  </Descriptions.Item>
                )}
                <Descriptions.Item label="结论">
                  {viewModalContent.data.verdict || '未知'}
                </Descriptions.Item>
                <Descriptions.Item label="AI评价">
                  <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
                    {viewModalContent.data.details || viewModalContent.data.reason || '无'}
                  </Paragraph>
                </Descriptions.Item>
              </Descriptions>
            )}

            {viewModalContent.title === '严谨性检测报告' && (
              <Descriptions bordered column={1}>
                <Descriptions.Item label="检测结果">
                  {viewModalContent.data.error ? (
                    <Tag color="error">检测出错</Tag>
                  ) : viewModalContent.data.is_rigorous ? (
                    <Tag color="success">严谨</Tag>
                  ) : (
                    <Tag color="error">不严谨</Tag>
                  )}
                </Descriptions.Item>
                {viewModalContent.data.error && (
                  <Descriptions.Item label="错误信息">
                    <Alert
                      type="error"
                      message="检测过程中出现错误"
                      description={viewModalContent.data.error}
                    />
                  </Descriptions.Item>
                )}
                {viewModalContent.data.rigor_score && (
                  <Descriptions.Item label="严谨性分数">
                    {viewModalContent.data.rigor_score}
                  </Descriptions.Item>
                )}
                <Descriptions.Item label="结论">
                  {viewModalContent.data.verdict || '未知'}
                </Descriptions.Item>
                <Descriptions.Item label="AI评价">
                  <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
                    {viewModalContent.data.details || viewModalContent.data.reason || '无'}
                  </Paragraph>
                </Descriptions.Item>
              </Descriptions>
            )}
          </div>
        )}
      </Modal>

      {/* 查看题目Modal */}
      <Modal
        title="题目详情"
        open={viewProblemModalVisible}
        onCancel={() => setViewProblemModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setViewProblemModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {viewProblemData && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="题目内容">
              <MathRenderer content={viewProblemData.content || ''} />
            </Descriptions.Item>
            <Descriptions.Item label="标准答案">
              <MathRenderer content={viewProblemData.answer || ''} />
            </Descriptions.Item>
            <Descriptions.Item label="题目解析">
              <MathRenderer content={viewProblemData.explanation || ''} />
            </Descriptions.Item>
            <Descriptions.Item label="难度检测">
              {(() => {
                const data = viewProblemData.difficulty_validation;
                if (!data) {
                  return <Tag color="default">未检测</Tag>;
                }
                
                const hasError = data.attempts_details?.some((detail: any) => detail.error);
                if (hasError) {
                  return <Tag color="error">检测出错</Tag>;
                }
                
                return data.is_passed ? (
                  <Tag color="success">通过</Tag>
                ) : (
                  <Tag color="error">未通过</Tag>
                );
              })()}
              {viewProblemData.difficulty_validation && (
                <div style={{ marginTop: 8 }}>
                  {viewProblemData.difficulty_validation.attempts_details?.some((detail: any) => detail.error) && (
                    <Alert
                      type="error"
                      message="检测过程中出现错误"
                      description={
                        <ul style={{ margin: 0, paddingLeft: 20 }}>
                          {viewProblemData.difficulty_validation.attempts_details
                            ?.filter((detail: any) => detail.error)
                            .map((detail: any, index: number) => (
                              <li key={index}>{detail.error}</li>
                            ))}
                        </ul>
                      }
                      style={{ marginTop: 8 }}
                    />
                  )}
                  <div style={{ marginTop: 8 }}>
                    <Text strong>正确次数：</Text>
                    {viewProblemData.difficulty_validation.correct_count || 0} /{' '}
                    {viewProblemData.difficulty_validation.attempts || 8}
                  </div>
                  {viewProblemData.difficulty_validation.verdict && (
                    <div style={{ marginTop: 4 }}>
                      <Text strong>结论：</Text> {viewProblemData.difficulty_validation.verdict}
                    </div>
                  )}
                  {viewProblemData.difficulty_validation.recommendation && (
                    <div style={{ marginTop: 4 }}>
                      <Text strong>建议：</Text> {viewProblemData.difficulty_validation.recommendation}
                    </div>
                  )}
                </div>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="原创性检测">
              {(() => {
                const data = viewProblemData.originality_check;
                if (!data) {
                  return <Tag color="default">未检测</Tag>;
                }
                
                if (data.error) {
                  return <Tag color="error">检测出错</Tag>;
                }
                
                return data.is_original ? (
                  <Tag color="success">原创</Tag>
                ) : (
                  <Tag color="error">非原创</Tag>
                );
              })()}
              {viewProblemData.originality_check && (
                <div style={{ marginTop: 8 }}>
                  {viewProblemData.originality_check.error && (
                    <Alert
                      type="error"
                      message="检测过程中出现错误"
                      description={viewProblemData.originality_check.error}
                      style={{ marginTop: 8 }}
                    />
                  )}
                  {viewProblemData.originality_check.originality_score && (
                    <div style={{ marginTop: 8 }}>
                      <Text strong>原创性分数：</Text> {viewProblemData.originality_check.originality_score}
                    </div>
                  )}
                  {viewProblemData.originality_check.verdict && (
                    <div style={{ marginTop: 4 }}>
                      <Text strong>结论：</Text> {viewProblemData.originality_check.verdict}
                    </div>
                  )}
                  {(viewProblemData.originality_check.details || viewProblemData.originality_check.reason) && (
                    <div style={{ marginTop: 4 }}>
                      <Text strong>AI评价：</Text>
                      <Paragraph style={{ whiteSpace: 'pre-wrap', marginTop: 4 }}>
                        {viewProblemData.originality_check.details || viewProblemData.originality_check.reason || '无'}
                      </Paragraph>
                    </div>
                  )}
                </div>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="严谨性检测">
              {(() => {
                const data = viewProblemData.rigor_check;
                if (!data) {
                  return <Tag color="default">未检测</Tag>;
                }
                
                if (data.error) {
                  return <Tag color="error">检测出错</Tag>;
                }
                
                return data.is_rigorous ? (
                  <Tag color="success">严谨</Tag>
                ) : (
                  <Tag color="error">不严谨</Tag>
                );
              })()}
              {viewProblemData.rigor_check && (
                <div style={{ marginTop: 8 }}>
                  {viewProblemData.rigor_check.error && (
                    <Alert
                      type="error"
                      message="检测过程中出现错误"
                      description={viewProblemData.rigor_check.error}
                      style={{ marginTop: 8 }}
                    />
                  )}
                  {viewProblemData.rigor_check.rigor_score && (
                    <div style={{ marginTop: 8 }}>
                      <Text strong>严谨性分数：</Text> {viewProblemData.rigor_check.rigor_score}
                    </div>
                  )}
                  {viewProblemData.rigor_check.verdict && (
                    <div style={{ marginTop: 4 }}>
                      <Text strong>结论：</Text> {viewProblemData.rigor_check.verdict}
                    </div>
                  )}
                  {(viewProblemData.rigor_check.details || viewProblemData.rigor_check.reason) && (
                    <div style={{ marginTop: 4 }}>
                      <Text strong>AI评价：</Text>
                      <Paragraph style={{ whiteSpace: 'pre-wrap', marginTop: 4 }}>
                        {viewProblemData.rigor_check.details || viewProblemData.rigor_check.reason || '无'}
                      </Paragraph>
                    </div>
                  )}
                </div>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(viewProblemData.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
}
