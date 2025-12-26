import type { Problem } from '../../types';

export type ValidationStatus = 'pending' | 'queued' | 'validating' | 'passed' | 'failed';

export interface ProblemItem {
  key: string;
  id?: number;
  content: string;
  answer: string;
  explanation?: string;
  validationStatus?: ValidationStatus;
  validationResult?: any;
}

// 单个检测维度的状态
export type CheckStatus = 'pending' | 'checking' | 'passed' | 'failed';

export interface VariantItem extends Problem {
  key: string;
  qualityCheckStatus?: 'pending' | 'checking' | 'passed' | 'failed';
  // 三个独立的检测状态
  difficultyCheckStatus?: CheckStatus;
  originalityCheckStatus?: CheckStatus;
  rigorCheckStatus?: CheckStatus;
  // 延迟写入场景需要的额外字段
  title?: string;
  category?: string;
  source_type?: string;
  quality_check?: any;
}


