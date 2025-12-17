/**
 * 全局类型定义
 */

import { UserRole, TaskType, TaskStatus } from '../config/constants';

// 用户信息
export interface User {
  id: number;
  username: string;
  email?: string;
  role: UserRole;
  balance: number;
  problems_created_count: number;
  reviews_completed_count: number;
  is_active: boolean;
  is_impersonating: boolean;
  created_at: string;
  last_login_at?: string;
}

// 登录响应
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_info: User;
}

// 任务
export interface Task {
  id: number;
  task_type: TaskType;
  status: TaskStatus;
  claimed_by_user_id?: number;
  claimed_at?: string;
  expires_at?: string;
  submitted_at?: string;
  completed_at?: string;
}

// 题目
export interface Problem {
  id: number;
  creator_id: number;
  parent_problem_id?: number;
  content: string;
  explanation?: string;
  answer: string;
  difficulty_level?: number;
  validation_status?: string;
  quality_check?: QualityCheck;
  human_review_status?: string;
  human_review_note?: string;
  variant_count: number;
  created_at: string;
  updated_at: string;
}

// 质量检查
export interface QualityCheck {
  difficulty: {
    status: 'passed' | 'failed';
    correct_count: number;
    total_attempts: number;
  };
  originality: {
    status: 'passed' | 'failed';
    is_original: boolean;
    reason?: string;
  };
  rigor: {
    status: 'passed' | 'failed';
    is_rigorous: boolean;
    reason?: string;
  };
}

// 评分
export interface Review {
  id: number;
  problem_id: number;
  reviewer_id: number;
  correctness_verification?: {
    user_choice: string;
    is_correct: boolean;
  };
  innovation_score?: number;
  rigor_score?: number;
  veto_reason?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

// 资料库
export interface Material {
  id: number;
  category: string;
  title: string;
  description: string;
  baidu_link: string;
  extract_code: string;
  download_count: number;
  problem_count: number;
}

// 交易记录
export interface Transaction {
  id: number;
  user_id: number;
  amount: number;
  transaction_type: string;
  related_problem_id?: number;
  related_review_id?: number;
  status: string;
  description: string;
  created_at: string;
}

// 排名
export interface Ranking {
  user_id: number;
  username: string;
  total_earnings: number;
  problems_created: number;
  reviews_completed: number;
  rank: number;
}

// API响应包装
export interface ApiResponse<T = any> {
  data?: T;
  detail?: string;
  message?: string;
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

