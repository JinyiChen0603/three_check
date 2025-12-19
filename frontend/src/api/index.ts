/**
 * API 统一导出
 */

import apiClient from './axios';
import type { Problem, Task, Review, Material, Ranking, Transaction } from '../types';

export { authApi } from './auth';
export { apiClient };

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
  abandonTask: async (taskId: number) => {
    const response = await apiClient.post(`/tasks/${taskId}/abandon`);
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
  validateSingle: async (content: string, answer: string) => {
    const response = await apiClient.post('/problems/validate/single', {
      content,
      answer,
    });
    return response.data;
  },

  // 批量验证
  validateBatch: async (problems: Array<{ content: string; answer: string }>) => {
    const response = await apiClient.post('/problems/validate/batch', {
      problems,
    });
    return response.data;
  },

  // 生成题目变体
  generateVariant: async (
    parentProblemId: number,
    content: string,
    explanation: string,
    answer: string,
    transformPrompt: string
  ) => {
    const response = await apiClient.post<Problem>('/problems/generate-variant', {
      parent_problem_id: parentProblemId,
      content,
      explanation,
      answer,
      transform_prompt: transformPrompt,
    });
    return response.data;
  },

  // 质量检查
  qualityCheck: async (problemId: number) => {
    const response = await apiClient.post(`/problems/${problemId}/quality-check`);
    return response.data;
  },

  // 获取我的题目列表
  getMyProblems: async () => {
    const response = await apiClient.get<Problem[]>('/problems/my');
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
};

// 评分相关 API
export const reviewApi = {
  // 获取待评分的题目
  getPendingReview: async () => {
    const response = await apiClient.get<Problem>('/reviews/pending');
    return response.data;
  },

  // 提交正确性验证
  submitCorrectness: async (problemId: number, userChoice: string, judgement?: string) => {
    const response = await apiClient.post(`/reviews/${problemId}/correctness`, {
      user_choice: userChoice,
      judgement,
    });
    return response.data;
  },

  // 提交评分
  submitScores: async (
    problemId: number,
    innovationScore: number,
    rigorScore: number,
    vetoReason?: string
  ) => {
    const response = await apiClient.post(`/reviews/${problemId}/score`, {
      innovation_score: innovationScore,
      rigor_score: rigorScore,
      veto_reason: vetoReason,
    });
    return response.data;
  },

  // 获取我的评分记录
  getMyReviews: async () => {
    const response = await apiClient.get<Review[]>('/reviews/my');
    return response.data;
  },
};

// 资料库相关 API
export const materialApi = {
  // 获取所有类别
  getCategories: async () => {
    const response = await apiClient.get<string[]>('/materials/categories');
    return response.data;
  },

  // 获取指定类别的资料
  getMaterialsByCategory: async (category: string) => {
    const response = await apiClient.get<Material[]>(`/materials/${category}`);
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
    const response = await apiClient.get<Ranking[]>('/users/rankings');
    return response.data;
  },

  // 获取交易记录
  getTransactions: async () => {
    const response = await apiClient.get<Transaction[]>('/users/transactions');
    return response.data;
  },

  // 获取统计信息
  getStats: async () => {
    const response = await apiClient.get('/users/stats');
    return response.data;
  },
};

