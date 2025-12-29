/**
 * 题目验证状态管理
 * 支持跨页面保持验证状态
 */

import { create } from 'zustand';
import { notification } from 'antd';

export interface CheckStatus {
  loading: boolean;
  result: any | null;
  passed: boolean | null;
}

// 检测任务状态类型
export type CheckTaskStatus = 'idle' | 'running' | 'completed' | 'error';

// 单项检测任务状态
export interface CheckTaskState {
  status: CheckTaskStatus;
  progress: number;              // 0-100
  result: any | null;
  passed: boolean | null;
  taskId?: string;               // SSE任务ID（仅难度检测）
}

// 多题目队列项类型
export interface ProblemQueueItem {
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

// 导出列表项类型
export interface ExportListItem {
  id: number;
  content?: string;
  answer?: string;
  explanation?: string;
  difficulty_passed: boolean | null;
  originality_passed: boolean | null;
  rigor_passed: boolean | null;
  difficulty_validation?: any;
  originality_check?: any;
  rigor_check?: any;
  created_at: string;
}

interface ValidationState {
  // 三个检测状态（旧版单题目模式，保留兼容）
  difficultyCheck: CheckStatus;
  originalityCheck: CheckStatus;
  rigorCheck: CheckStatus;
  
  // 表单数据（避免切换页面丢失）
  formData: {
    problem: string;
    answer: string;
    explanation: string;
  } | null;
  
  // 新增：检测队列状态
  problemQueue: ProblemQueueItem[];
  
  // 新增：导出列表状态
  exportList: ExportListItem[];
  exportStats: { total: number; passed: number; failed: number };
  loadingList: boolean;
  
  // Actions - 旧版
  setDifficultyCheck: (check: CheckStatus) => void;
  setOriginalityCheck: (check: CheckStatus) => void;
  setRigorCheck: (check: CheckStatus) => void;
  setFormData: (data: { problem: string; answer: string; explanation: string }) => void;
  clearAllChecks: () => void;
  
  // Actions - 检测队列
  addToProblemQueue: (item: ProblemQueueItem) => void;
  updateProblemInQueue: (id: string, updates: Partial<ProblemQueueItem>) => void;
  updateProblemCheck: (
    problemId: string,
    checkType: 'difficulty' | 'originality' | 'rigor',
    updates: Partial<CheckTaskState>
  ) => void;
  removeFromProblemQueue: (id: string) => void;
  clearProblemQueue: () => void;
  markProblemAsSaved: (id: string) => void;
  
  // Actions - 导出列表
  setExportList: (list: ExportListItem[]) => void;
  setExportStats: (stats: { total: number; passed: number; failed: number }) => void;
  setLoadingList: (loading: boolean) => void;
  
  // 完成检查时的通知
  notifyCheckComplete: (checkType: 'difficulty' | 'originality' | 'rigor', passed: boolean) => void;
}

export const useValidationStore = create<ValidationState>((set, get) => ({
  // 初始状态 - 旧版
  difficultyCheck: {
    loading: false,
    result: null,
    passed: null,
  },
  originalityCheck: {
    loading: false,
    result: null,
    passed: null,
  },
  rigorCheck: {
    loading: false,
    result: null,
    passed: null,
  },
  formData: null,
  
  // 初始状态 - 新增
  problemQueue: [],
  exportList: [],
  exportStats: { total: 0, passed: 0, failed: 0 },
  loadingList: false,

  // Actions - 旧版
  setDifficultyCheck: (check) => {
    set({ difficultyCheck: check });
    // 如果检测完成，发送通知
    if (!check.loading && check.result !== null) {
      get().notifyCheckComplete('difficulty', check.passed || false);
    }
  },

  setOriginalityCheck: (check) => {
    set({ originalityCheck: check });
    if (!check.loading && check.result !== null) {
      get().notifyCheckComplete('originality', check.passed || false);
    }
  },

  setRigorCheck: (check) => {
    set({ rigorCheck: check });
    if (!check.loading && check.result !== null) {
      get().notifyCheckComplete('rigor', check.passed || false);
    }
  },

  setFormData: (data) => {
    set({ formData: data });
  },

  clearAllChecks: () => {
    set({
      difficultyCheck: { loading: false, result: null, passed: null },
      originalityCheck: { loading: false, result: null, passed: null },
      rigorCheck: { loading: false, result: null, passed: null },
      formData: null,
    });
  },

  // Actions - 检测队列
  addToProblemQueue: (item) => {
    set((state) => ({
      problemQueue: [...state.problemQueue, item],
    }));
  },

  updateProblemInQueue: (id, updates) => {
    set((state) => ({
      problemQueue: state.problemQueue.map((item) =>
        item.id === id ? { ...item, ...updates } : item
      ),
    }));
  },

  updateProblemCheck: (problemId, checkType, updates) => {
    set((state) => ({
      problemQueue: state.problemQueue.map((item) => {
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
      }),
    }));
  },

  removeFromProblemQueue: (id) => {
    set((state) => ({
      problemQueue: state.problemQueue.filter((item) => item.id !== id),
    }));
  },

  clearProblemQueue: () => {
    set({ problemQueue: [] });
  },

  markProblemAsSaved: (id) => {
    set((state) => ({
      problemQueue: state.problemQueue.map((item) =>
        item.id === id ? { ...item, saved: true } : item
      ),
    }));
  },

  // Actions - 导出列表
  setExportList: (list) => {
    set({ exportList: list });
  },

  setExportStats: (stats) => {
    set({ exportStats: stats });
  },

  setLoadingList: (loading) => {
    set({ loadingList: loading });
  },

  // 通知
  notifyCheckComplete: (checkType, passed) => {
    const typeNames = {
      difficulty: '难度验证',
      originality: '原创性检测',
      rigor: '严谨性检测',
    };

    notification[passed ? 'success' : 'warning']({
      message: `${typeNames[checkType]}完成`,
      description: passed ? '检测通过！' : '检测未通过，请查看详情',
      placement: 'topRight',
      duration: 4,
    });
  },
}));

