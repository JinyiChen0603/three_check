/**
 * API 统一导出
 */

import apiClient from './axios';
import type { Problem, Task, Review, Ranking, Transaction } from '../types';

export { authApi } from './auth';
export { apiClient };

// 配置相关 API
export const configApi = {
  // 获取前端配置
  getConfig: async () => {
    const response = await apiClient.get<{
      max_tasks_per_claim: number;
      task_timeout_hours: number;
      reward_per_problem: number;
      reward_per_review: number;
      max_problems_total: number;  // 用户总出题数上限
    }>('/config');
    return response.data;
  },
};

// 任务相关 API
export const taskApi = {
  // 获取可领取的任务列表
  getAvailableTasks: async (taskType: string) => {
    const response = await apiClient.get<Task[]>(`/tasks/available/${taskType}`);
    return response.data;
  },

  // 领取任务
  claimTasks: async (taskType: string, count: number) => {
    const response = await apiClient.post('/tasks/claim', {
      task_type: taskType,
      count: count,
    });
    return response.data;
  },

  // 获取我的任务
  getMyTasks: async (taskType?: string) => {
    const response = await apiClient.get('/tasks/my-tasks', {
      params: taskType ? { status: taskType } : undefined,
    });
    return response.data;
  },

  // 放弃任务
  abandonTask: async (taskId: number, confirmed: boolean = false) => {
    const response = await apiClient.post(`/tasks/${taskId}/abandon`, null, {
      params: { confirmed }
    });
    return response.data;
  },

  // 提交任务
  submitTask: async (taskId: number) => {
    const response = await apiClient.post(`/tasks/${taskId}/submit`);
    return response.data;
  },
};

// 题目相关 API
export const problemApi = {
  // OCR 识别
  ocrImage: async (image: File) => {
    // 将文件转为 base64
    const base64 = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        resolve(result.split(',')[1]);
      };
      reader.onerror = reject;
      reader.readAsDataURL(image);
    });
    
    const response = await apiClient.post('/problems/ocr', {
      image_base64: base64,
      extract_answer: true
    });
    return response.data;
  },

  // 单题验证
  validateSingle: async (content: string, answer: string, explanation?: string) => {
    const response = await apiClient.post('/problems/validate', {
      problem: content,
      answer,
      explanation,
    });
    return response.data;
  },

  // 批量验证
  validateBatch: async (problems: Array<{ content: string; answer: string; explanation?: string }>) => {
    const response = await apiClient.post('/problems/validate-batch', {
      problems: problems.map(p => ({
        problem: p.content,
        answer: p.answer,
        explanation: p.explanation,
      })),
    });
    return response.data;
  },

  // 创建题目
  createProblem: async (problemData: {
    title: string;
    content: any;
    explanation?: string;
    answer: string;
    category: string;
    source_type?: string;
    ocr_image_url?: string;
    parent_problem_id?: number;
  }) => {
    const response = await apiClient.post<Problem>('/problems/create', problemData);
    return response.data;
  },

  // 生成题目变体（保留同事新增的解析字段）
  generateVariant: async (
    parentProblemId: number,
    customPrompt?: string
  ) => {
    const response = await apiClient.post(`/problems/${parentProblemId}/generate-variant`, {
      custom_prompt: customPrompt,
    });
    return response.data;
  },

  // 质量检查（需要题目ID）
  qualityCheck: async (problemId: number) => {
    const response = await apiClient.post(`/problems/${problemId}/quality-check`);
    return response.data;
  },

  // 内容质检（无需题目ID，用于延迟写入场景）
  qualityCheckContent: async (content: any, answer: string, explanation?: string) => {
    const response = await apiClient.post('/problems/quality-check-content', {
      content: typeof content === 'string' ? content : JSON.stringify(content),
      answer,
      explanation,
    });
    return response.data;
  },

  // 单独检测难度（同步方式）
  checkDifficulty: async (content: any, answer: string, explanation?: string) => {
    const response = await apiClient.post('/problems/check-difficulty', {
      content: typeof content === 'string' ? content : JSON.stringify(content),
      answer,
      explanation,
    });
    return response.data;
  },

  // 启动异步难度检测，返回task_id
  startDifficultyCheck: async (content: any, answer: string, explanation?: string) => {
    const response = await apiClient.post('/problems/check-difficulty-start', {
      content: typeof content === 'string' ? content : JSON.stringify(content),
      answer,
      explanation,
    });
    return response.data as { task_id: string };
  },

  // 订阅难度检测进度（SSE方式）
  // 返回 EventSource 对象，调用方需要监听 onmessage 和 onerror 事件
  // 使用完毕后调用 close() 方法关闭连接
  subscribeDifficultyProgress: (taskId: string): EventSource => {
    // 获取 baseURL，处理相对路径的情况
    let baseUrl = apiClient.defaults.baseURL || '';
    
    // 如果是相对路径（如 /api），需要转换为完整 URL
    if (baseUrl.startsWith('/')) {
      const origin = window.location.origin;
      baseUrl = `${origin}${baseUrl}`;
    }
    
    const url = `${baseUrl}/problems/check-difficulty-stream/${taskId}`;
    return new EventSource(url);
  },

  // 查询难度检测当前进度（非SSE方式，用于恢复状态）
  getDifficultyProgress: async (taskId: string) => {
    const response = await apiClient.get(`/problems/check-difficulty-progress/${taskId}`);
    return response.data as { progress: number; result?: any };
  },

  // 单独检测原创性
  checkOriginality: async (content: any, answer: string, explanation?: string) => {
    const response = await apiClient.post('/problems/check-originality', {
      content: typeof content === 'string' ? content : JSON.stringify(content),
      answer,
      explanation,
    });
    return response.data;
  },

  // 单独检测严谨性
  checkRigor: async (content: any, answer: string, explanation?: string) => {
    const response = await apiClient.post('/problems/check-rigor', {
      content: typeof content === 'string' ? content : JSON.stringify(content),
      answer,
      explanation,
    });
    return response.data;
  },

  // 获取我的题目列表
  getMyProblems: async (status?: string) => {
    const response = await apiClient.get('/problems/my-problems', {
      params: status ? { status } : undefined,
    });
    return response.data;
  },

  // 优化题目
  optimizeProblem: async (problemId: number, optimizationNote: string) => {
    const response = await apiClient.post(`/problems/${problemId}/optimize`, {
      optimization_note: optimizationNote,
    });
    return response.data;
  },

  // 放弃题目
  abandonProblem: async (problemId: number) => {
    const response = await apiClient.post(`/problems/${problemId}/abandon`);
    return response.data;
  },

  // 提交审核
  submitForReview: async (problemId: number) => {
    const response = await apiClient.post(`/problems/${problemId}/submit-for-review`);
    return response.data;
  },

  // 获取我的变体题目列表（仅元数据）
  getMyVariants: async (skip = 0, limit = 20) => {
    const response = await apiClient.get('/problems/my-variants', {
      params: { skip, limit }
    });
    return response.data;
  },

  // 获取单个题目详情（包含完整内容）
  getProblemDetail: async (problemId: number) => {
    const response = await apiClient.get(`/problems/${problemId}`);
    return response.data;
  },

  // ==================== 新增：题目验证和导出相关API ====================
  
  // 验证并保存题目到导出列表
  validateAndSave: async (data: {
    problem: string;
    answer: string;
    explanation: string;
    include_difficulty?: boolean;
    difficulty_result?: any;  // 前端已完成的难度检测结果
    originality_result?: any;  // 前端已完成的原创性检测结果
    rigor_result?: any;  // 前端已完成的严谨性检测结果
  }) => {
    const formData = new FormData();
    formData.append('problem', data.problem);
    formData.append('answer', data.answer);
    formData.append('explanation', data.explanation);
    formData.append('include_difficulty', data.include_difficulty ? 'true' : 'false');
    // 如果前端已经进行了难度检测，传递检测结果
    if (data.difficulty_result) {
      formData.append('difficulty_result_json', JSON.stringify(data.difficulty_result));
    }
    // 如果前端已经进行了原创性检测，传递检测结果
    if (data.originality_result) {
      formData.append('originality_result_json', JSON.stringify(data.originality_result));
    }
    // 如果前端已经进行了严谨性检测，传递检测结果
    if (data.rigor_result) {
      formData.append('rigor_result_json', JSON.stringify(data.rigor_result));
    }
    
    const response = await apiClient.post('/problems/validate-and-save', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 获取待导出列表
  getExportList: async () => {
    const response = await apiClient.get('/problems/export-list');
    return response.data;
  },

  // 导出验证题目到Excel
  exportValidated: async (onlyPassed: boolean = true) => {
    const response = await apiClient.get('/problems/export-validated', {
      params: { only_passed: onlyPassed ? 1 : 0 }, // 将布尔值转换为整数
      responseType: 'blob',
    });
    return response.data;
  },

  // 清空导出列表
  clearExportList: async () => {
    const response = await apiClient.delete('/problems/clear-export-list');
    return response.data;
  },

  // 删除单个已验证题目
  deleteValidatedProblem: async (problemId: number) => {
    const response = await apiClient.delete(`/problems/export-list/${problemId}`);
    return response.data;
  },
};

// 深度变形相关 API（独立的变体生成，不依赖母题）
export const variantApi = {
  // 生成单个变体（不依赖母题）
  generateVariantDirect: async (data: {
    original_content: string;
    original_explanation: string;
    original_answer: string;
    modification_requirement?: string;
    max_tokens?: number;
    temperature?: number;
  }) => {
    const response = await apiClient.post('/deep-transform/generate-variant', {
      original_content: data.original_content,
      original_explanation: data.original_explanation,
      original_answer: data.original_answer,
      modification_requirement: data.modification_requirement || '',
      max_tokens: data.max_tokens || 10000,
      temperature: data.temperature || 1.5,
      use_stream: true,
    });
    return response.data;
  },

  // 批量生成变体
  generateMultipleVariants: async (data: {
    original_content: string;
    original_explanation: string;
    original_answer: string;
    modification_requirement?: string;
    count: number;
    max_tokens?: number;
    temperature?: number;
  }) => {
    const response = await apiClient.post('/deep-transform/generate-multiple-variants', {
      original_content: data.original_content,
      original_explanation: data.original_explanation,
      original_answer: data.original_answer,
      modification_requirement: data.modification_requirement || '',
      count: data.count,
      max_tokens: data.max_tokens || 10000,
      temperature: data.temperature || 1.5,
      use_stream: true,
    });
    return response.data;
  },
};

// 评分相关 API
export const reviewApi = {
  // 获取下一个待评分题目（新API）
  getNextProblem: async () => {
    const response = await apiClient.get('/reviews/next-problem');
    return response.data;
  },

  // 获取4选1选项（正确性验证）
  getProblemChoices: async (validatedProblemId: number) => {
    const response = await apiClient.get(`/reviews/problem/${validatedProblemId}/choices`);
    return response.data;
  },

  // 提交正确性验证
  submitCorrectness: async (
    validatedProblemId: number,
    selectedIndex: number,
    selectedAnswer?: string,
    correctIndex?: number,
    userAnswer?: string
  ) => {
    const response = await apiClient.post(`/reviews/problem/${validatedProblemId}/verify`, {
      selected_index: selectedIndex,
      selected_answer: selectedAnswer,
      correct_index: correctIndex,
      user_answer: userAnswer,
    });
    return response.data;
  },

  // 提交评分
  submitScores: async (
    reviewId: number,
    innovationScore: number,
    rigorScore: number,
    comment?: string,
    isVetoed?: boolean,
    vetoReason?: string
  ) => {
    const response = await apiClient.post('/reviews/score', {
      review_id: reviewId,
      innovation_score: innovationScore,
      rigor_score: rigorScore,
      comment,
      is_vetoed: isVetoed || false,
      veto_reason: vetoReason,
    });
    return response.data;
  },

  // 获取我的评分记录
  getMyReviews: async () => {
    const response = await apiClient.get<{ total: number; reviews: any[] }>('/reviews/my-reviews');
    // 转换后端返回的数据格式以匹配前端类型
    return response.data.reviews.map((r: any) => ({
      id: r.id,
      problem_id: r.validated_problem_id,
      reviewer_id: 0,
      is_answer_correct: r.is_answer_correct,
      correctness_verification: r.correctness_verification,
      innovation_score: r.innovation_score ?? undefined,
      rigor_score: r.rigor_score ?? undefined,
      veto_reason: r.veto_reason,
      status: r.status,
      created_at: r.created_at,
      updated_at: r.updated_at,
      problem: r.problem,
    })) as Review[];
  },
};

// 资料库类别汇总（后端返回的格式）
export interface CategorySummary {
  category: string;
  category_display: string;
  material_count: number;
  total_downloads: number;
}

// 资料详情（后端返回的格式）
export interface MaterialResponse {
  id: number;
  category: string;
  category_display: string;
  title: string;
  description: string | null;
  baidu_link: string;
  extract_code: string | null;
  download_count: number;
}

// 资料库相关 API
export const materialApi = {
  // 获取所有类别汇总
  getCategories: async (): Promise<CategorySummary[]> => {
    const response = await apiClient.get<CategorySummary[]>('/materials/categories');
    return response.data;
  },

  // 获取资料列表（可按类别筛选）
  getMaterials: async (category?: string, skip = 0, limit = 100): Promise<MaterialResponse[]> => {
    const params: Record<string, any> = { skip, limit };
    if (category) {
      params.category = category;
    }
    const response = await apiClient.get<MaterialResponse[]>('/materials/list', { params });
    return response.data;
  },

  // 获取资料详情
  getMaterial: async (materialId: number): Promise<MaterialResponse> => {
    const response = await apiClient.get<MaterialResponse>(`/materials/${materialId}`);
    return response.data;
  },

  // 记录下载
  recordDownload: async (materialId: number) => {
    const response = await apiClient.post(`/materials/${materialId}/download`);
    return response.data;
  },
};

// 用户相关 API
export const userApi = {
  // 获取用户余额
  getBalance: async () => {
    const response = await apiClient.get<{ balance: number }>('/users/balance');
    return response.data;
  },

  // 获取排名
  getRankings: async () => {
    const response = await apiClient.get<Ranking[]>('/users/leaderboard');
    return response.data;
  },

  // 获取交易记录
  getTransactions: async () => {
    const response = await apiClient.get<Transaction[]>('/users/me/transactions');
    return response.data;
  },

  // 获取统计信息
  getStats: async () => {
    const response = await apiClient.get('/users/me/stats');
    return response.data;
  },

  // 获取用户列表（管理员）
  getUserList: async (skip = 0, limit = 50) => {
    const response = await apiClient.get('/users/list', {
      params: { skip, limit }
    });
    return response.data;
  },
};

// 管理员相关 API
export const adminApi = {
  // 获取待审核题目列表
  getPendingReviewProblems: async (statusFilter?: string, skip = 0, limit = 50) => {
    const response = await apiClient.get('/admin/problems/pending-review', {
      params: { status_filter: statusFilter, skip, limit }
    });
    return response.data;
  },

  // 获取题目审核详情
  getProblemReviewDetail: async (problemId: number) => {
    const response = await apiClient.get(`/admin/problems/${problemId}/detail`);
    return response.data;
  },

  // 审核题目
  reviewProblem: async (problemId: number, approved: boolean, note?: string) => {
    const response = await apiClient.post('/admin/problems/review', {
      problem_id: problemId,
      approved,
      note,
    });
    return response.data;
  },

  // 导出题目（简化：只使用 status_filter）
  exportProblems: async (statusFilter?: string) => {
    const response = await apiClient.get('/admin/problems/export', {
      params: statusFilter ? { status_filter: statusFilter } : {},
      responseType: 'blob',
    });
    return response.data;
  },
};

