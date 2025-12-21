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

export interface VariantItem extends Problem {
  key: string;
  qualityCheckStatus?: 'pending' | 'checking' | 'passed' | 'failed';
}


