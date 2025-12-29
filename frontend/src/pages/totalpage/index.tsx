/**
 * 题目验证与导出页面
 * 单页面设计：所有功能在一个界面
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Card,
  Button,
  Space,
  Typography,
  Input,
  Form,
  message,
  Table,
  Tag,
  Modal,
  Statistic,
  Row,
  Col,
  Descriptions,
  Alert,
  Upload,
  Progress,
  List,
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
  SaveOutlined,
  RadarChartOutlined,
  PictureOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { problemApi } from '../../api';
import MathRenderer from '../../components/MathRenderer';
import { useTask } from '../../hooks/useTask';
import { TaskType } from '../../config/constants';
import { useAuthStore } from '../../store/useAuthStore';
import { useValidationStore } from '../../store/useValidationStore';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

/**
 * 还原 JSON 转义字符
 * 处理后端传输过程中被 JSON 序列化转义的字符
 */
function unescapeText(text: string | undefined | null): string {
  if (!text) return '';
  
  return text
    // 引号
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    // 空白字符
    .replace(/\\n/g, '\n')
    .replace(/\\t/g, '\t')
    .replace(/\\r/g, '\r')
    // 括号
    .replace(/\\\(/g, '(')
    .replace(/\\\)/g, ')')
    .replace(/\\\[/g, '[')
    .replace(/\\\]/g, ']')
    .replace(/\\\{/g, '{')
    .replace(/\\\}/g, '}')
    // 反斜杠（必须放在最后）
    .replace(/\\\\/g, '\\');
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

// 检测任务状态类型
type CheckTaskStatus = 'idle' | 'running' | 'completed' | 'error';

// 单项检测任务状态
interface CheckTaskState {
  status: CheckTaskStatus;
  progress: number;              // 0-100
  result: any | null;
  passed: boolean | null;
  taskId?: string;               // SSE任务ID（仅难度检测）
}

// 多题目队列项类型
interface ProblemQueueItem {
  id: string;                    // UUID
  problem: string;               // 题目内容
  answer: string;                // 答案
  explanation: string;           // 解析
  checks: {
    difficulty: CheckTaskState;
    originality: CheckTaskState;
    rigor: CheckTaskState;
  };
  allCompleted: boolean;         // 三项检测是否全部完成
  saved: boolean;                // 是否已保存到导出列表
}

// 创建初始检测状态
const createInitialCheckState = (): CheckTaskState => ({
  status: 'idle',
  progress: 0,
  result: null,
  passed: null,
});

export default function TotalPage() {
  const [form] = Form.useForm<ProblemFormData>();
  
  // 任务管理Hook
  const { tasks, refreshTasks } = useTask();
  
  // 用户信息刷新
  const fetchCurrentUser = useAuthStore((state) => state.fetchCurrentUser);

  // 使用全局store替代本地state
  const {
    difficultyCheck,
    originalityCheck,
    rigorCheck,
    formData,
    setDifficultyCheck,
    setOriginalityCheck,
    setRigorCheck,
    setFormData,
    clearAllChecks,
  } = useValidationStore();

  // 题目检测队列（本地状态，用于多题目并行检测）
  const [problemQueue, setProblemQueue] = useState<ProblemQueueItem[]>([]);

  // AbortController引用（用于取消HTTP请求）
  const abortControllersRef = useRef<Map<string, AbortController>>(new Map());

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

  // SSE连接引用（按题目ID存储）
  const sseConnectionsRef = useRef<Map<string, EventSource>>(new Map());
  
  // 标记难度检测是否已完成（按题目ID存储，用于区分 SSE 正常关闭和真正的错误）
  const difficultyCompletedRef = useRef<Map<string, boolean>>(new Map());

  // 更新单个题目的单项检测状态
  const updateProblemCheck = useCallback((
    problemId: string,
    checkType: 'difficulty' | 'originality' | 'rigor',
    updates: Partial<CheckTaskState>
  ) => {
    setProblemQueue(prev => prev.map(item => {
      if (item.id !== problemId) return item;
      
      const newChecks = {
        ...item.checks,
        [checkType]: { ...item.checks[checkType], ...updates }
      };
      
      // 计算是否所有检测都完成
      const allCompleted = 
        (newChecks.difficulty.status === 'completed' || newChecks.difficulty.status === 'error') &&
        (newChecks.originality.status === 'completed' || newChecks.originality.status === 'error') &&
        (newChecks.rigor.status === 'completed' || newChecks.rigor.status === 'error');
      
      return { ...item, checks: newChecks, allCompleted };
    }));
  }, []);

  // 清理单个题目的SSE连接
  const cleanupSSE = useCallback((problemId: string) => {
    const eventSource = sseConnectionsRef.current.get(problemId);
    if (eventSource) {
      eventSource.close();
      sseConnectionsRef.current.delete(problemId);
    }
  }, []);

  // 清理所有SSE连接
  const cleanupAllSSE = useCallback(() => {
    sseConnectionsRef.current.forEach((eventSource) => {
      eventSource.close();
    });
    sseConnectionsRef.current.clear();
  }, []);

  // 组件卸载时清理所有SSE连接和AbortController
  useEffect(() => {
    return () => {
      cleanupAllSSE();
      abortControllersRef.current.forEach(controller => controller.abort());
      abortControllersRef.current.clear();
    };
  }, [cleanupAllSSE]);

  // 计算队列中有多少题目完成了所有检测
  const completedCount = problemQueue.filter(item => item.allCompleted).length;
  
  // 计算队列中有多少题目已保存
  const savedCount = problemQueue.filter(item => item.saved).length;

  // 验证难度（使用SSE实时推送进度）- 针对特定题目
  const runDifficultyCheck = useCallback(async (problemId: string, problem: string, answer: string, explanation: string) => {
    const controllerKey = `${problemId}-difficulty`;
    
    try {
      // 清理之前的SSE连接
      cleanupSSE(problemId);
      
      // 重置完成标记
      difficultyCompletedRef.current.set(problemId, false);

      // 创建 AbortController
      const controller = new AbortController();
      abortControllersRef.current.set(controllerKey, controller);

      // 更新状态：开始检测
      updateProblemCheck(problemId, 'difficulty', { status: 'running', progress: 0, result: null, passed: null });
      
      // 1. 启动异步难度检测
      const { task_id } = await problemApi.startDifficultyCheck(problem, answer, explanation);

      // 检查是否已被取消
      if (controller.signal.aborted) {
        return;
      }

      // 更新任务ID
      updateProblemCheck(problemId, 'difficulty', { taskId: task_id });

      // 2. 建立SSE连接订阅进度
      const eventSource = problemApi.subscribeDifficultyProgress(task_id);
      sseConnectionsRef.current.set(problemId, eventSource);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // 忽略心跳消息（仅用于保持连接活跃）
          if (data.heartbeat) {
            console.log('收到心跳，连接正常');
            return;
          }
          
          const progress = data.progress || 0;
          
          // 更新进度
          updateProblemCheck(problemId, 'difficulty', { progress });

          // 如果任务完成（进度100%且有结果）
          if (progress >= 100 && data.result) {
            const result = data.result;
            
            // 检查attempts_details中是否有error
            const hasError = result.attempts_details?.some((detail: any) => detail.error);
            const passed = hasError ? false : (result.is_passed || false);
            
            // 1. 首先标记任务已完成（防止 SSE 关闭时 onerror 误报，必须在其他操作之前）
            difficultyCompletedRef.current.set(problemId, true);
            
            // 2. 更新状态
            updateProblemCheck(problemId, 'difficulty', { 
              status: 'completed', 
              progress: 100, 
              result: result,
              passed: passed
            });

            // 3. 关闭SSE连接
            cleanupSSE(problemId);
            abortControllersRef.current.delete(controllerKey);
          }
        } catch (parseError) {
          console.error('解析SSE数据失败:', parseError);
        }
      };

      eventSource.onerror = (error) => {
        // 如果任务已完成，忽略这个错误（SSE 正常关闭触发的）
        if (difficultyCompletedRef.current.get(problemId)) {
          console.log('SSE 正常关闭（任务已完成）');
          return;
        }
        
        console.error('SSE连接错误:', error);
        
        // 如果是取消操作，不显示错误
        if (controller.signal.aborted) {
          return;
        }
        
        // 更新状态为错误
        updateProblemCheck(problemId, 'difficulty', { status: 'error', progress: 0 });
        
        // 关闭SSE连接
        cleanupSSE(problemId);
        abortControllersRef.current.delete(controllerKey);
      };

    } catch (error: any) {
      console.error('难度检测失败:', error);
      updateProblemCheck(problemId, 'difficulty', { status: 'error', progress: 0 });
      abortControllersRef.current.delete(controllerKey);
    }
  }, [cleanupSSE, updateProblemCheck]);

  // 检测原创性 - 针对特定题目
  const runOriginalityCheck = useCallback(async (problemId: string, problem: string, answer: string, explanation: string) => {
    const controllerKey = `${problemId}-originality`;
    
    try {
      // 创建 AbortController
      const controller = new AbortController();
      abortControllersRef.current.set(controllerKey, controller);

      // 更新状态：开始检测
      updateProblemCheck(problemId, 'originality', { status: 'running', progress: 0, result: null, passed: null });
      
      const result = await problemApi.checkOriginality(problem, answer, explanation);

      // 检查是否已被取消
      if (controller.signal.aborted) {
        return;
      }

      // 检查是否有error
      const hasError = !result.success || result.originality?.error;
      const passed = hasError ? false : (result.originality?.is_original || false);

      // 更新状态
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

  // 检测严谨性 - 针对特定题目
  const runRigorCheck = useCallback(async (problemId: string, problem: string, answer: string, explanation: string) => {
    const controllerKey = `${problemId}-rigor`;
    
    try {
      // 创建 AbortController
      const controller = new AbortController();
      abortControllersRef.current.set(controllerKey, controller);

      // 更新状态：开始检测
      updateProblemCheck(problemId, 'rigor', { status: 'running', progress: 0, result: null, passed: null });
      
      const result = await problemApi.checkRigor(problem, answer, explanation);

      // 检查是否已被取消
      if (controller.signal.aborted) {
        return;
      }

      // 检查是否有error
      const hasError = !result.success || result.rigor?.error;
      const passed = hasError ? false : (result.rigor?.is_rigorous || false);

      // 更新状态
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
    // 并行启动三项检测
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

      // 生成唯一ID
      const problemId = `problem-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

      // 创建新的队列项
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

      // 添加到队列
      setProblemQueue(prev => [...prev, newItem]);

      // 清空表单，允许继续输入
      form.resetFields();

      message.success('✅ 题目已添加到检测队列');

      // 立即启动检测
      startAllChecksForProblem(newItem);
    } catch (error: any) {
      if (!error.errorFields) {
        message.error('添加失败，请检查输入');
      }
    }
  };

  // 查看检测报告 - 针对特定题目
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
        data = item.checks.difficulty.result;
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

  // 保存单个题目到列表
  const handleSaveProblem = async (problemId: string) => {
    const item = problemQueue.find(p => p.id === problemId);
    if (!item) {
      message.warning('题目不存在');
      return;
    }

    // 检查三个检测是否都已执行过（不能有idle状态）
    const hasIdleCheck = 
      item.checks.difficulty.status === 'idle' ||
      item.checks.originality.status === 'idle' ||
      item.checks.rigor.status === 'idle';
    
    if (hasIdleCheck) {
      message.warning('请确保三项检测都已执行');
      return;
    }

    // 检查是否有正在进行的检测
    const hasRunningCheck = 
      item.checks.difficulty.status === 'running' ||
      item.checks.originality.status === 'running' ||
      item.checks.rigor.status === 'running';
    
    if (hasRunningCheck) {
      message.warning('请等待所有检测完成');
      return;
    }

    // 检查是否有出错的检测
    const hasErrorCheck = 
      item.checks.difficulty.status === 'error' ||
      item.checks.originality.status === 'error' ||
      item.checks.rigor.status === 'error';
    
    if (hasErrorCheck) {
      message.warning('存在检测出错，请点击重试按钮重新检测');
      return;
    }

    if (item.saved) {
      message.warning('该题目已保存');
      return;
    }

    try {
      setSavingToList(true);

      const result = await problemApi.validateAndSave({
        problem: item.problem,
        answer: item.answer,
        explanation: item.explanation,
        include_difficulty: false,
        difficulty_result: item.checks.difficulty.result || undefined,
        originality_result: item.checks.originality.result || undefined,
        rigor_result: item.checks.rigor.result || undefined,
      });

      const taskProgress = result.task_progress;
      const progressMsg = taskProgress 
        ? `（进度：${taskProgress.completed}/${taskProgress.total}，剩余：${taskProgress.remaining}）`
        : '';
      
      message.success(`✅ 题目已保存到导出列表${progressMsg}`);
      
      // 标记为已保存
      setProblemQueue(prev => prev.map(p => 
        p.id === problemId ? { ...p, saved: true } : p
      ));
      
      // 刷新列表、任务和用户信息
      await loadExportList();
      await refreshTasks();
      await fetchCurrentUser();
    } catch (error: any) {
      console.error('保存失败:', error);
      const errorMsg = error.response?.data?.detail || error.message || '保存失败，请重试';
      message.error(errorMsg);
    } finally {
      setSavingToList(false);
    }
  };

  // 从队列中移除题目
  const handleRemoveFromQueue = (problemId: string) => {
    // 取消该题目的所有进行中的请求
    ['difficulty', 'originality', 'rigor'].forEach(type => {
      const controllerKey = `${problemId}-${type}`;
      const controller = abortControllersRef.current.get(controllerKey);
      if (controller) {
        controller.abort();
        abortControllersRef.current.delete(controllerKey);
      }
    });
    
    // 清理SSE连接
    cleanupSSE(problemId);
    
    // 从队列中移除
    setProblemQueue(prev => prev.filter(p => p.id !== problemId));
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
        // 取消所有正在进行的请求
        abortControllersRef.current.forEach(controller => controller.abort());
        abortControllersRef.current.clear();
        
        // 清理所有SSE连接
        cleanupAllSSE();
        
        // 清空队列
        setProblemQueue([]);
        
        message.success('队列已清空');
      },
    });
  };

  // 重置表单和状态
  const handleReset = () => {
    form.resetFields();
    clearAllChecks();
  };

  // 修改题目（增强版：停止检测并清除报告）
  const handleModify = () => {
    // 取消所有正在进行的请求
    Object.values(abortControllers).forEach(controller => {
      if (controller) {
        controller.abort();
      }
    });

    // 重置所有检测状态和报告（使用全局store）
    clearAllChecks();
    
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

  // 恢复表单数据（从全局store）
  useEffect(() => {
    if (formData) {
      form.setFieldsValue(formData);
    }
  }, [formData, form]);

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

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="标准答案"
                name="answer"
                rules={[{ required: true, message: '请输入标准答案' }]}
              >
                <Input placeholder="请输入标准答案" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="题目解析"
                name="explanation"
                rules={[{ required: true, message: '请输入题目解析' }]}
              >
                <Input placeholder="请输入题目解析" />
              </Form.Item>
            </Col>
          </Row>
        </Form>

        {/* 操作按钮 */}
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
              {completedCount}/{problemQueue.length} 题完成 | {savedCount} 已保存
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
                        problemItem.saved ? (
                          <Tag color="success" icon={<CheckCircleOutlined />}>已保存</Tag>
                        ) : (
                          <Tag color="blue" icon={<CheckCircleOutlined />}>检测完成</Tag>
                        )
                      ) : (
                        <Tag color="processing" icon={<LoadingOutlined />}>检测中</Tag>
                      )}
                    </Space>
                  }
                  extra={
                    <Space>
                      {problemItem.allCompleted && !problemItem.saved && (
                        <Button 
                          type="primary" 
                          size="small" 
                          icon={<SaveOutlined />}
                          loading={savingToList}
                          onClick={() => handleSaveProblem(problemItem.id)}
                        >
                          保存
                        </Button>
                      )}
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
                    <Text ellipsis={{ tooltip: problemItem.problem }} style={{ maxWidth: 400 }}>
                      {problemItem.problem.length > 50 ? `${problemItem.problem.slice(0, 50)}...` : problemItem.problem}
                    </Text>
                  </div>

                  {/* 三项检测状态 */}
                  <Row gutter={[16, 8]}>
                    {checks.map((check) => (
                      <Col span={8} key={check.key}>
                        <Card size="small" bordered={false} style={{ background: '#fafafa' }}>
                          <Space direction="vertical" style={{ width: '100%' }} size={4}>
                            <Space>
                              {getCheckStatusIcon(check.status, check.passed)}
                              {check.icon}
                              <Text strong style={{ fontSize: 12 }}>{check.name}</Text>
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
                      </Col>
                    ))}
                  </Row>
                </Card>
              );
            }}
          />
        )}
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
              viewModalContent.data ? (
                <>
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
                                    <li key={index}><MathRenderer content={detail.error} /></li>
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
                      <MathRenderer content={viewModalContent.data.verdict || '未知'} />
                    </Descriptions.Item>
                    {viewModalContent.data.recommendation && (
                      <Descriptions.Item label="建议">
                        <MathRenderer content={viewModalContent.data.recommendation} />
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
                {viewModalContent.data.originality_score && (
                  <Descriptions.Item label="原创性分数">
                    {viewModalContent.data.originality_score}
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
                {viewModalContent.data.rigor_score && (
                  <Descriptions.Item label="严谨性分数">
                    {viewModalContent.data.rigor_score}
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
