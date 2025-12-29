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

interface ValidationState {
  // 三个检测状态
  difficultyCheck: CheckStatus;
  originalityCheck: CheckStatus;
  rigorCheck: CheckStatus;
  
  // 表单数据（避免切换页面丢失）
  formData: {
    problem: string;
    answer: string;
    explanation: string;
  } | null;
  
  // Actions
  setDifficultyCheck: (check: CheckStatus) => void;
  setOriginalityCheck: (check: CheckStatus) => void;
  setRigorCheck: (check: CheckStatus) => void;
  setFormData: (data: { problem: string; answer: string; explanation: string }) => void;
  clearAllChecks: () => void;
  
  // 完成检查时的通知
  notifyCheckComplete: (checkType: 'difficulty' | 'originality' | 'rigor', passed: boolean) => void;
}

export const useValidationStore = create<ValidationState>((set, get) => ({
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

