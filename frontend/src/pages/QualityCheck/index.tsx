/**
 * 数学题目三重质检工具
 * 纯质检功能：难度、原创性、严谨性检测
 */

import { useState, useRef, useCallback } from 'react';
import {
  Card,
  Button,
  Space,
  Typography,
  Input,
  Form,
  message,
  Tag,
  Modal,
  Alert,
  Upload,
  Progress,
  List,
  Descriptions,
  Table,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
  PlusOutlined,
  SyncOutlined,
  SafetyCertificateOutlined,
  ExperimentOutlined,
  EyeOutlined,
  RadarChartOutlined,
  PictureOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  TranslationOutlined,
} from '@ant-design/icons';
import { problemApi } from '../../api';
import MathRenderer from '../../components/MathRenderer';
import { 
  useValidationStore,
  type ProblemQueueItem,
  type CheckTaskStatus,
} from '../../store/useValidationStore';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

/**
 * 还原 JSON 转义字符
 */
function unescapeText(text: string | undefined | null): string {
  if (!text) return '';
  
  return text
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    .replace(/\\n/g, '\n')
    .replace(/\\t/g, '\t')
    .replace(/\\r/g, '\r')
    .replace(/\\\{/g, '{')
    .replace(/\\\}/g, '}')
    .replace(/\\\\/g, '\\');
}

// 创建初始检测状态
const createInitialCheckState = () => ({
  status: 'idle' as const,
  progress: 0,
  result: null,
  passed: null,
});

export default function QualityCheckPage() {
  const [form] = Form.useForm();
  
  // 使用全局store
  const {
    problemQueue,
    addToProblemQueue,
    updateProblemCheck,
    updateProblemInQueue,
    removeFromProblemQueue,
    clearProblemQueue,
  } = useValidationStore();

  // AbortController引用（用于取消HTTP请求）
  const abortControllersRef = useRef<Map<string, AbortController>>(new Map());

  // Modal状态
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [viewModalContent, setViewModalContent] = useState<{
    title: string;
    data: any;
  } | null>(null);

  // 查看题目详情的Modal状态
  const [viewProblemDetailsModalVisible, setViewProblemDetailsModalVisible] = useState(false);
  const [selectedProblemForView, setSelectedProblemForView] = useState<ProblemQueueItem | null>(null);

  // 翻译状态
  const [translating, setTranslating] = useState<{
    problem: boolean;
    explanation: boolean;
  }>({ problem: false, explanation: false });

  // SSE连接引用（按题目ID存储）
  const sseConnectionsRef = useRef<Map<string, EventSource>>(new Map());
  
  // 标记难度检测是否已完成
  const difficultyCompletedRef = useRef<Map<string, boolean>>(new Map());

  // 图片识别状态
  const [recognizing, setRecognizing] = useState(false);

  // 计算队列中有多少题目完成了所有检测
  const completedCount = problemQueue.filter(item => item.allCompleted).length;

  // 清理单个题目的SSE连接
  const cleanupSSE = useCallback((problemId: string) => {
    const eventSource = sseConnectionsRef.current.get(problemId);
    if (eventSource) {
      eventSource.close();
      sseConnectionsRef.current.delete(problemId);
    }
  }, []);

  // 验证难度（使用SSE实时推送进度）
  const runDifficultyCheck = useCallback(async (problemId: string, problem: string, answer: string, explanation: string) => {
    const controllerKey = `${problemId}-difficulty`;
    
    try {
      cleanupSSE(problemId);
      difficultyCompletedRef.current.set(problemId, false);

      const controller = new AbortController();
      abortControllersRef.current.set(controllerKey, controller);

      updateProblemCheck(problemId, 'difficulty', { status: 'running', progress: 0, result: null, passed: null });
      
      const { task_id } = await problemApi.startDifficultyCheck(problem, answer, explanation);

      if (controller.signal.aborted) {
        return;
      }

      updateProblemCheck(problemId, 'difficulty', { taskId: task_id });

      const eventSource = problemApi.subscribeDifficultyProgress(task_id);
      sseConnectionsRef.current.set(problemId, eventSource);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.heartbeat) {
            const progress = data.progress || 0;
            updateProblemCheck(problemId, 'difficulty', { progress });
            return;
          }
          
          const progress = data.progress || 0;
          updateProblemCheck(problemId, 'difficulty', { progress });

          if (progress >= 100 && data.result) {
            const result = data.result;
            const hasError = result.attempts_details?.some((detail: any) => detail.error);
            const passed = hasError ? false : (result.is_passed || false);
            
            difficultyCompletedRef.current.set(problemId, true);
            
            updateProblemCheck(problemId, 'difficulty', { 
              status: 'completed', 
              progress: 100, 
              result: result,
              passed: passed
            });

            cleanupSSE(problemId);
            abortControllersRef.current.delete(controllerKey);
          }
        } catch (parseError) {
          console.error('解析SSE数据失败:', parseError);
        }
      };

      eventSource.onerror = async (error) => {
        if (difficultyCompletedRef.current.get(problemId)) {
          return;
        }
        
        console.warn('SSE连接断开，尝试轮询获取最终结果...', error);
        
        if (controller.signal.aborted) {
          return;
        }
        
        cleanupSSE(problemId);
        
        let pollCount = 0;
        const maxPolls = 30;
        const pollInterval = 2000;
        
        const pollResult = setInterval(async () => {
          pollCount++;
          
          try {
            const progressData = await problemApi.getDifficultyProgress(task_id);
            
            if (progressData && progressData.progress !== undefined) {
              const { progress, result } = progressData;
              
              updateProblemCheck(problemId, 'difficulty', { progress });
              
              if (progress >= 100 && result) {
                clearInterval(pollResult);
                
                const passed = result.is_passed || false;
                difficultyCompletedRef.current.set(problemId, true);
                
                updateProblemCheck(problemId, 'difficulty', { 
                  status: 'completed', 
                  progress: 100, 
                  result: result,
                  passed: passed
                });
                
                abortControllersRef.current.delete(controllerKey);
                message.success('难度检测完成（轮询恢复）');
                return;
              }
            }
            
            if (pollCount >= maxPolls) {
              clearInterval(pollResult);
              console.error('轮询超时，检测失败');
              updateProblemCheck(problemId, 'difficulty', { status: 'error', progress: 0 });
              abortControllersRef.current.delete(controllerKey);
              message.error('难度检测失败：连接超时');
            }
          } catch (pollError) {
            console.error('轮询失败:', pollError);
          }
        }, pollInterval);
        
        abortControllersRef.current.set(`${controllerKey}-poll`, { 
          abort: () => clearInterval(pollResult) 
        } as any);
      };

    } catch (error: any) {
      console.error('难度检测失败:', error);
      updateProblemCheck(problemId, 'difficulty', { status: 'error', progress: 0 });
      abortControllersRef.current.delete(controllerKey);
    }
  }, [cleanupSSE, updateProblemCheck]);

  // 检测原创性
  const runOriginalityCheck = useCallback(async (problemId: string, problem: string, answer: string, explanation: string) => {
    const controllerKey = `${problemId}-originality`;
    
    try {
      const controller = new AbortController();
      abortControllersRef.current.set(controllerKey, controller);

      updateProblemCheck(problemId, 'originality', { status: 'running', progress: 0, result: null, passed: null });
      
      const result = await problemApi.checkOriginality(problem, answer, explanation);

      if (controller.signal.aborted) {
        return;
      }

      const hasError = !result.success || result.originality?.error;
      const passed = hasError ? false : (result.originality?.is_original || false);

      updateProblemCheck(problemId, 'originality', { 
        status: hasError ? 'error' : 'completed', 
        progress: 100, 
        result: result.originality,
        passed: passed
      });

      abortControllersRef.current.delete(controllerKey);
    } catch (error: any) {
      console.error('原创性检测失败:', error);
      updateProblemCheck(problemId, 'originality', { status: 'error', progress: 0 });
      abortControllersRef.current.delete(controllerKey);
    }
  }, [updateProblemCheck]);

  // 检测严谨性
  const runRigorCheck = useCallback(async (problemId: string, problem: string, answer: string, explanation: string) => {
    const controllerKey = `${problemId}-rigor`;
    
    try {
      const controller = new AbortController();
      abortControllersRef.current.set(controllerKey, controller);

      updateProblemCheck(problemId, 'rigor', { status: 'running', progress: 0, result: null, passed: null });
      
      const result = await problemApi.checkRigor(problem, answer, explanation);

      if (controller.signal.aborted) {
        return;
      }

      const hasError = !result.success || result.rigor?.error;
      const passed = hasError ? false : (result.rigor?.is_rigorous || false);

      updateProblemCheck(problemId, 'rigor', { 
        status: hasError ? 'error' : 'completed', 
        progress: 100, 
        result: result.rigor,
        passed: passed
      });

      abortControllersRef.current.delete(controllerKey);
    } catch (error: any) {
      console.error('严谨性检测失败:', error);
      updateProblemCheck(problemId, 'rigor', { status: 'error', progress: 0 });
      abortControllersRef.current.delete(controllerKey);
    }
  }, [updateProblemCheck]);

  // 启动单个题目的所有检测（并行执行）
  const startAllChecksForProblem = useCallback((item: ProblemQueueItem) => {
    runDifficultyCheck(item.id, item.problem, item.answer, item.explanation);
    runOriginalityCheck(item.id, item.problem, item.answer, item.explanation);
    runRigorCheck(item.id, item.problem, item.answer, item.explanation);
  }, [runDifficultyCheck, runOriginalityCheck, runRigorCheck]);

  // 重试单项检测
  const retryCheck = useCallback((problemId: string, checkType: 'difficulty' | 'originality' | 'rigor') => {
    const item = problemQueue.find(p => p.id === problemId);
    if (!item) {
      message.warning('题目不存在');
      return;
    }

    switch (checkType) {
      case 'difficulty':
        runDifficultyCheck(item.id, item.problem, item.answer, item.explanation);
        break;
      case 'originality':
        runOriginalityCheck(item.id, item.problem, item.answer, item.explanation);
        break;
      case 'rigor':
        runRigorCheck(item.id, item.problem, item.answer, item.explanation);
        break;
    }
  }, [problemQueue, runDifficultyCheck, runOriginalityCheck, runRigorCheck]);

  // 添加题目到队列并立即开始检测
  const handleAddToQueue = async () => {
    try {
      await form.validateFields(['problem', 'answer', 'explanation']);
      const values = form.getFieldsValue();

      const problemId = `problem-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

      const newItem: ProblemQueueItem = {
        id: problemId,
        problem: values.problem,
        answer: values.answer,
        explanation: values.explanation || '',
        checks: {
          difficulty: createInitialCheckState(),
          originality: createInitialCheckState(),
          rigor: createInitialCheckState(),
        },
        allCompleted: false,
        saved: false,
      };

      addToProblemQueue(newItem);
      form.resetFields();
      message.success('✅ 题目已添加到检测队列');
      startAllChecksForProblem(newItem);
    } catch (error: any) {
      if (!error.errorFields) {
        message.error('添加失败，请检查输入');
      }
    }
  };

  // 查看检测报告
  const handleViewReport = (problemId: string, type: 'difficulty' | 'originality' | 'rigor') => {
    const item = problemQueue.find(p => p.id === problemId);
    if (!item) {
      message.warning('题目不存在');
      return;
    }

    let title = '';
    let data = null;

    switch (type) {
      case 'difficulty':
        title = '难度检测报告';
        data = {
          ...item.checks.difficulty.result,
          user_answer: item.answer,
        };
        break;
      case 'originality':
        title = '原创性检测报告';
        data = item.checks.originality.result;
        break;
      case 'rigor':
        title = '严谨性检测报告';
        data = item.checks.rigor.result;
        break;
    }

    if (!data) {
      message.warning('暂无检测结果');
      return;
    }

    setViewModalContent({ title, data });
    setViewModalVisible(true);
  };

  // 查看题目完整信息
  const handleViewProblemDetails = (item: ProblemQueueItem) => {
    setSelectedProblemForView(item);
    setViewProblemDetailsModalVisible(true);
  };

  // 翻译处理函数
  const handleTranslate = async (field: 'problem' | 'explanation', text: string) => {
    if (!selectedProblemForView) return;
    
    const problemId = selectedProblemForView.id;
    setTranslating(prev => ({ ...prev, [field]: true }));
    
    try {
      const result = await problemApi.translate(text);
      
      if (result.success) {
        // 使用函数式更新，获取最新的 state 值避免竞态条件
        setSelectedProblemForView(prev => {
          if (!prev || prev.id !== problemId) return prev;
          
          const newTranslations = {
            ...prev.translations,
            [field]: result.translated
          };
          
          // 同时更新 store
          updateProblemInQueue(problemId, {
            translations: newTranslations
          });
          
          return {
            ...prev,
            translations: newTranslations
          };
        });
        
        message.success(`${field === 'problem' ? '题目内容' : '题目解析'}翻译成功`);
      } else {
        message.error(result.error || '翻译失败');
      }
    } catch (error: any) {
      console.error('翻译失败:', error);
      message.error('翻译失败，请重试');
    } finally {
      setTranslating(prev => ({ ...prev, [field]: false }));
    }
  };

  // 关闭Modal
  const handleCloseProblemDetailsModal = () => {
    setViewProblemDetailsModalVisible(false);
    // 翻译结果已保存在 store 中，下次打开会从 store 读取
  };

  // 从队列中移除题目
  const handleRemoveFromQueue = (problemId: string) => {
    ['difficulty', 'originality', 'rigor'].forEach(type => {
      const controllerKey = `${problemId}-${type}`;
      const controller = abortControllersRef.current.get(controllerKey);
      if (controller) {
        controller.abort();
        abortControllersRef.current.delete(controllerKey);
      }
    });
    
    cleanupSSE(problemId);
    difficultyCompletedRef.current.delete(problemId);
    removeFromProblemQueue(problemId);
  };

  // 清空整个检测队列
  const handleClearQueue = () => {
    if (problemQueue.length === 0) {
      message.info('队列已经是空的');
      return;
    }

    Modal.confirm({
      title: '确认清空队列',
      content: `确定要清空检测队列吗？共 ${problemQueue.length} 个题目将被移除。`,
      okText: '确认',
      cancelText: '取消',
      okType: 'danger',
      onOk: () => {
        abortControllersRef.current.forEach(controller => controller.abort());
        abortControllersRef.current.clear();
        sseConnectionsRef.current.forEach((eventSource) => eventSource.close());
        sseConnectionsRef.current.clear();
        difficultyCompletedRef.current.clear();
        clearProblemQueue();
        message.success('队列已清空');
      },
    });
  };

  // 图片识别处理
  const handleImageRecognize = async (file: File) => {
    const isImage = file.type.startsWith('image/');
    if (!isImage) {
      message.error('只能上传图片文件！');
      return false;
    }

    const isLt5M = file.size / 1024 / 1024 < 5;
    if (!isLt5M) {
      message.error('图片大小不能超过 5MB！');
      return false;
    }

    try {
      setRecognizing(true);
      message.loading('正在识别图片...', 0);
      
      const result = await problemApi.ocrImage(file);
      
      message.destroy();
      
      if (result.success) {
        const formData: any = {};
        
        if (result.problem) {
          formData.problem = result.problem;
        }
        
        if (result.answer) {
          formData.answer = result.answer;
        }
        
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
    
    return false;
  };

  // 获取检测状态图标
  const getCheckStatusIcon = (status: CheckTaskStatus, passed: boolean | null) => {
    switch (status) {
      case 'idle':
        return <ClockCircleOutlined style={{ color: '#999' }} />;
      case 'running':
        return <LoadingOutlined style={{ color: '#1890ff' }} spin />;
      case 'completed':
        return passed 
          ? <CheckCircleOutlined style={{ color: '#52c41a' }} />
          : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return null;
    }
  };

  // 获取检测状态标签
  const getCheckStatusTag = (status: CheckTaskStatus, passed: boolean | null) => {
    switch (status) {
      case 'idle':
        return <Tag color="default">未开始</Tag>;
      case 'running':
        return <Tag color="processing">检测中</Tag>;
      case 'completed':
        return passed 
          ? <Tag color="success">通过</Tag>
          : <Tag color="error">未通过</Tag>;
      case 'error':
        return <Tag color="error">出错</Tag>;
      default:
        return null;
    }
  };

  // 获取进度条状态
  const getProgressStatus = (status: CheckTaskStatus, passed: boolean | null) => {
    switch (status) {
      case 'running':
        return 'active' as const;
      case 'completed':
        return passed ? 'success' as const : 'exception' as const;
      case 'error':
        return 'exception' as const;
      default:
        return 'normal' as const;
    }
  };

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      {/* 顶部标题 */}
      <Card style={{ marginBottom: 24 }}>
        <Title level={2}>
          🔬 数学题目三重质检工具（使用过程请勿刷新页面）
        </Title>
        <Paragraph type="secondary">
          提供难度检测、原创性检测、严谨性检测三项AI质检服务，不保存任何数据
        </Paragraph>
        <Alert
          message="纯质检工具"
          description="本工具仅提供质检功能，所有检测结果仅在浏览器中展示，不会保存到服务器。"
          type="info"
          showIcon
          style={{ marginTop: 16 }}
        />
      </Card>

      {/* 题目输入区 */}
      <Card title="添加题目到检测队列" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical">
          <Form.Item
            label="题目内容"
            name="problem"
            rules={[{ required: true, message: '请输入题目内容' }]}
          >
            <TextArea
              rows={6}
              placeholder="请输入题目内容（支持LaTeX公式，如 $x^2$）"
            />
          </Form.Item>

          <Form.Item
            label="标准答案"
            name="answer"
            rules={[{ required: true, message: '请输入标准答案' }]}
          >
            <Input placeholder="请输入标准答案" />
          </Form.Item>

          <Form.Item
            label="题目解析"
            name="explanation"
            rules={[{ required: true, message: '请输入题目解析' }]}
          >
            <TextArea
              rows={4}
              placeholder="请输入题目解析"
            />
          </Form.Item>
        </Form>

        <Space style={{ marginTop: 16 }}>
          <Button 
            type="primary"
            icon={<PlusOutlined />} 
            onClick={handleAddToQueue}
            size="large"
          >
            添加到检测队列
          </Button>
          
          <Upload
            accept="image/*"
            showUploadList={false}
            beforeUpload={handleImageRecognize}
          >
            <Button 
              icon={<PictureOutlined />}
              loading={recognizing}
            >
              {recognizing ? '识别中...' : '图片识别'}
            </Button>
          </Upload>
        </Space>
      </Card>

      {/* 检测任务队列 */}
      <Card 
        title={
          <Space>
            <ClockCircleOutlined />
            检测任务队列
          </Space>
        }
        style={{ marginBottom: 24 }}
        extra={
          <Space>
            <Text type="secondary">
              {completedCount}/{problemQueue.length} 题完成
            </Text>
            {problemQueue.length > 0 && (
              <Button 
                danger 
                size="small" 
                icon={<DeleteOutlined />}
                onClick={handleClearQueue}
              >
                清空队列
              </Button>
            )}
          </Space>
        }
      >
        {problemQueue.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            <ClockCircleOutlined style={{ fontSize: 48, marginBottom: 16 }} />
            <div>暂无检测任务，请在上方添加题目</div>
          </div>
        ) : (
          <List
            dataSource={problemQueue}
            renderItem={(problemItem, index) => {
              const checks = [
                { key: 'difficulty' as const, name: '难度检测', icon: <ExperimentOutlined />, ...problemItem.checks.difficulty },
                { key: 'originality' as const, name: '原创性检测', icon: <SafetyCertificateOutlined />, ...problemItem.checks.originality },
                { key: 'rigor' as const, name: '严谨性检测', icon: <RadarChartOutlined />, ...problemItem.checks.rigor },
              ];

              return (
                <Card 
                  key={problemItem.id}
                  size="small" 
                  style={{ marginBottom: 16 }}
                  title={
                    <Space>
                      <Text strong>题目 {index + 1}</Text>
                      {problemItem.allCompleted ? (
                        <Tag color="blue" icon={<CheckCircleOutlined />}>检测完成</Tag>
                      ) : (
                        <Tag color="processing" icon={<LoadingOutlined />}>检测中</Tag>
                      )}
                    </Space>
                  }
                  extra={
                    <Space>
                      <Button 
                        size="small" 
                        type="default"
                        onClick={() => handleViewProblemDetails(problemItem)}
                      >
                        查看
                      </Button>
                      <Button 
                        danger 
                        size="small" 
                        icon={<DeleteOutlined />}
                        onClick={() => handleRemoveFromQueue(problemItem.id)}
                      >
                        移除
                      </Button>
                    </Space>
                  }
                >
                  {/* 题目内容预览 */}
                  <div style={{ marginBottom: 12 }}>
                    <Text type="secondary">题目：</Text>
                    <Text ellipsis={{ tooltip: problemItem.problem }} style={{ maxWidth: 600 }}>
                      {problemItem.problem.length > 80 ? `${problemItem.problem.slice(0, 80)}...` : problemItem.problem}
                    </Text>
                  </div>

                  {/* 三项检测状态 */}
                  <Space direction="vertical" style={{ width: '100%' }} size={12}>
                    {checks.map((check) => (
                      <Card key={check.key} size="small" bordered={false} style={{ background: '#fafafa' }}>
                        <Space direction="vertical" style={{ width: '100%' }} size={4}>
                          <Space>
                            {getCheckStatusIcon(check.status, check.passed)}
                            {check.icon}
                            <Text strong>{check.name}</Text>
                          </Space>
                          <Progress
                            percent={check.progress}
                            size="small"
                            status={getProgressStatus(check.status, check.passed)}
                            format={(percent) => `${percent}%`}
                          />
                          <Space>
                            {getCheckStatusTag(check.status, check.passed)}
                            {check.status === 'completed' && check.result && (
                              <Button 
                                type="link" 
                                size="small" 
                                icon={<EyeOutlined />}
                                onClick={() => handleViewReport(problemItem.id, check.key)}
                                style={{ padding: 0 }}
                              >
                                查看报告
                              </Button>
                            )}
                            {check.status === 'error' && (
                              <Button 
                                type="link" 
                                size="small" 
                                icon={<SyncOutlined />}
                                onClick={() => retryCheck(problemItem.id, check.key)}
                                style={{ padding: 0, color: '#ff4d4f' }}
                              >
                                重试
                              </Button>
                            )}
                          </Space>
                        </Space>
                      </Card>
                    ))}
                  </Space>
                </Card>
              );
            }}
          />
        )}
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
              viewModalContent.data ? (
                <>
                  <Descriptions bordered column={1}>
                    <Descriptions.Item label="检测结果">
                      {(() => {
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
                    <Descriptions.Item label="正确次数">
                      {viewModalContent.data.correct_count || 0} /{' '}
                      {viewModalContent.data.total_attempts || viewModalContent.data.attempts || 8}
                    </Descriptions.Item>
                    <Descriptions.Item label="结论">
                      <MathRenderer content={viewModalContent.data.verdict || '未知'} />
                    </Descriptions.Item>
                    {viewModalContent.data.user_answer && (
                      <Descriptions.Item label="用户答案">
                        <MathRenderer content={viewModalContent.data.user_answer} />
                      </Descriptions.Item>
                    )}
                  </Descriptions>
                  
                  {/* 每次尝试详情表格 */}
                  {viewModalContent.data.attempts_details && viewModalContent.data.attempts_details.length > 0 && (
                    <div style={{ marginTop: 16 }}>
                      <Title level={5}>每次尝试详情</Title>
                      <Table
                        dataSource={viewModalContent.data.attempts_details}
                        rowKey="attempt"
                        size="small"
                        pagination={false}
                        columns={[
                          {
                            title: '序号',
                            dataIndex: 'attempt',
                            key: 'attempt',
                            width: 60,
                          },
                          {
                            title: 'AI回答',
                            dataIndex: 'ai_answer',
                            key: 'ai_answer',
                            render: (text: string, record: any) => {
                              if (record.error) {
                                return <MathRenderer content={record.error} style={{ color: '#ff4d4f' }} />;
                              }
                              return <MathRenderer content={text || '-'} />;
                            },
                          },
                          {
                            title: '结果',
                            dataIndex: 'is_correct',
                            key: 'is_correct',
                            width: 80,
                            render: (isCorrect: boolean, record: any) => {
                              if (record.error) {
                                return <Tag color="error">出错</Tag>;
                              }
                              return isCorrect ? (
                                <Tag icon={<CheckCircleOutlined />} color="success">正确</Tag>
                              ) : (
                                <Tag icon={<CloseCircleOutlined />} color="error">错误</Tag>
                              );
                            },
                          },
                        ]}
                      />
                    </div>
                  )}
                </>
              ) : (
                <Alert type="info" message="无结果可查，请先进行检测" />
              )
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
                      description={unescapeText(viewModalContent.data.error)}
                    />
                  </Descriptions.Item>
                )}
                <Descriptions.Item label="结论">
                  {unescapeText(viewModalContent.data.verdict) || '未知'}
                </Descriptions.Item>
                <Descriptions.Item label="AI评价">
                  <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
                    {unescapeText(viewModalContent.data.details || viewModalContent.data.reason) || '无'}
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
                      description={unescapeText(viewModalContent.data.error)}
                    />
                  </Descriptions.Item>
                )}
                <Descriptions.Item label="结论">
                  {unescapeText(viewModalContent.data.verdict) || '未知'}
                </Descriptions.Item>
                <Descriptions.Item label="AI评价">
                  <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
                    {unescapeText(viewModalContent.data.details || viewModalContent.data.reason) || '无'}
                  </Paragraph>
                </Descriptions.Item>
              </Descriptions>
            )}
          </div>
        )}
      </Modal>

      {/* 查看题目详情Modal */}
      <Modal
        title="题目详情"
        open={viewProblemDetailsModalVisible}
        onCancel={handleCloseProblemDetailsModal}
        footer={[
          <Button key="close" onClick={handleCloseProblemDetailsModal}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {selectedProblemForView && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {/* 题目内容 */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <Text strong style={{ fontSize: 16, color: '#1890ff' }}>题目内容</Text>
                <Button
                  size="small"
                  icon={<TranslationOutlined />}
                  loading={translating.problem}
                  onClick={() => handleTranslate('problem', selectedProblemForView.problem)}
                >
                  {selectedProblemForView.translations?.problem ? '重新翻译' : '翻译'}
                </Button>
              </div>
              
              {/* 原文 */}
              <div
                style={{
                  padding: '16px',
                  background: '#f5f5f5',
                  borderRadius: '8px',
                  border: '1px solid #d9d9d9',
                }}
              >
                <MathRenderer content={selectedProblemForView.problem} />
              </div>
              
              {/* 翻译结果 */}
              {selectedProblemForView.translations?.problem && (
                <div
                  style={{
                    padding: '16px',
                    background: '#e6f7ff',
                    borderRadius: '8px',
                    marginTop: '8px',
                    border: '1px solid #91d5ff',
                  }}
                >
                  <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                    📝 翻译：
                  </Text>
                  <MathRenderer content={selectedProblemForView.translations.problem} />
                </div>
              )}
            </div>

            {/* 标准答案 */}
            <div>
              <Text strong style={{ fontSize: 16, color: '#52c41a' }}>标准答案</Text>
              <div
                style={{
                  padding: '16px',
                  background: '#f6ffed',
                  borderRadius: '8px',
                  marginTop: '8px',
                  border: '1px solid #b7eb8f',
                }}
              >
                <MathRenderer content={selectedProblemForView.answer} />
              </div>
            </div>

            {/* 题目解析 */}
            {selectedProblemForView.explanation && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <Text strong style={{ fontSize: 16, color: '#faad14' }}>题目解析</Text>
                  <Button
                    size="small"
                    icon={<TranslationOutlined />}
                    loading={translating.explanation}
                    onClick={() => handleTranslate('explanation', selectedProblemForView.explanation)}
                  >
                    {selectedProblemForView.translations?.explanation ? '重新翻译' : '翻译'}
                  </Button>
                </div>
                
                {/* 原文 */}
                <div
                  style={{
                    padding: '16px',
                    background: '#fffbe6',
                    borderRadius: '8px',
                    border: '1px solid #ffe58f',
                  }}
                >
                  <MathRenderer content={selectedProblemForView.explanation} />
                </div>
                
                {/* 翻译结果 */}
                {selectedProblemForView.translations?.explanation && (
                  <div
                    style={{
                      padding: '16px',
                      background: '#e6f7ff',
                      borderRadius: '8px',
                      marginTop: '8px',
                      border: '1px solid #91d5ff',
                    }}
                  >
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                      📝 翻译：
                    </Text>
                    <MathRenderer content={selectedProblemForView.translations.explanation} />
                  </div>
                )}
              </div>
            )}
          </Space>
        )}
      </Modal>
    </div>
  );
}
