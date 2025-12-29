/**
 * 变体生成状态管理
 * 支持跨页面保持状态，后台运行任务
 */

import { create } from 'zustand';
import { notification } from 'antd';

export interface VariantResult {
  variant_content: string;
  variant_explanation: string;
  variant_answer: string;
  timestamp: number;
}

export interface OriginalProblemData {
  original_content: string;
  original_explanation: string;
  original_answer: string;
  modification_requirement?: string;
}

interface VariantState {
  // 生成的变体列表
  variants: VariantResult[];
  // 是否正在生成
  loading: boolean;
  // 批量生成加载状态
  batchLoading: boolean;
  // 温度参数
  temperature: number;
  // 批量模式
  batchMode: boolean;
  // 批量数量
  batchCount: number;
  // 原始题目数据（用于保留表单内容）
  originalProblem: OriginalProblemData | null;
  
  // Actions
  addVariant: (variant: VariantResult) => void;
  addVariants: (variants: VariantResult[]) => void;
  removeVariant: (timestamp: number) => void;
  clearVariants: () => void;
  setLoading: (loading: boolean) => void;
  setBatchLoading: (loading: boolean) => void;
  setTemperature: (temp: number) => void;
  setBatchMode: (mode: boolean) => void;
  setBatchCount: (count: number) => void;
  setOriginalProblem: (data: OriginalProblemData | null) => void;
}

export const useVariantStore = create<VariantState>((set, get) => ({
  variants: [],
  loading: false,
  batchLoading: false,
  temperature: 1.5,
  batchMode: false,
  batchCount: 3,
  originalProblem: null,

  addVariant: (variant) => {
    set((state) => ({
      variants: [variant, ...state.variants],
    }));
    
    // 显示成功通知
    notification.success({
      message: '变体生成成功',
      description: '新变体已添加到列表',
      placement: 'topRight',
      duration: 3,
    });
  },

  addVariants: (variants) => {
    set((state) => ({
      variants: [...variants, ...state.variants],
    }));
    
    // 显示成功通知
    notification.success({
      message: '批量生成完成',
      description: `成功生成 ${variants.length} 个变体`,
      placement: 'topRight',
      duration: 4,
    });
  },

  removeVariant: (timestamp) => {
    set((state) => ({
      variants: state.variants.filter((v) => v.timestamp !== timestamp),
    }));
  },

  clearVariants: () => {
    set({ variants: [] });
  },

  setLoading: (loading) => {
    set({ loading });
  },

  setBatchLoading: (loading) => {
    set({ batchLoading: loading });
  },

  setTemperature: (temperature) => {
    set({ temperature });
  },

  setBatchMode: (batchMode) => {
    set({ batchMode });
  },

  setBatchCount: (batchCount) => {
    set({ batchCount });
  },

  setOriginalProblem: (data) => {
    set({ originalProblem: data });
  },
}));

