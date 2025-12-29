/**
 * 全局类型定义
 */

import { UserRole, TaskType, TaskStatus } from '../config/constants';

// 重新导出常量，方便统一导入
export { UserRole, TaskType, TaskStatus };

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

// 任务批次（后端返回的格式）
export interface TaskBatch {
  batch_id: string;
  task_type: string;
  status: string;
  total_count: number;
  completed_count: number;
  claimed_at?: string;
  expires_at?: string;
  tasks: Array<{
    task_id: number;
    problem_id?: number;
  }>;
}

// 任务批次响应~
export interface TaskBatchesResponse {
  total_batches: number;
  batches: TaskBatch[];
  total_problems_created: number;  // 用户累计出题总数
  total_reviews_completed: number;  // 用户累计评分总数
}

// 任务（前端使用的格式）
export interface Task {
  id: number;
  batch_id?: string;
  task_type: TaskType;
  status: TaskStatus;
  total_count?: number;  // 任务数量（批次总数）
  completed_count?: number;  // 已完成数量
  claimed_by_user_id?: number;
  claimed_at?: string;
  expires_at?: string;
  submitted_at?: string;
  completed_at?: string;
  problem_id?: number;  // 关联的题目ID（评分任务有）
}

// 题目
export interface Problem {
  id: number;
  creator_id: number;
  parent_problem_id?: number;
  content: string | { text: string };  // 支持字符串或对象格式
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
  all_passed?: boolean;
  difficulty: {
    status?: 'passed' | 'failed';
    correct_count?: number;
    total_attempts?: number;
    attempts?: number;
    is_passed?: boolean;
    ai_model?: string;
    evaluation?: string;
    chatgpt_result?: {
      correct_count: number;
      attempts: number;
      is_passed: boolean;
      evaluation?: string;
      [key: string]: any;
    };
    zhipu_result?: {
      correct_count: number;
      attempts: number;
      is_passed: boolean;
      evaluation?: string;
      [key: string]: any;
    };
    verdict?: string;
    [key: string]: any;
  };
  originality: {
    status?: 'passed' | 'failed';
    is_original?: boolean;
    reason?: string;
    verdict?: string;
    details?: string;
    [key: string]: any;
  };
  rigor: {
    status?: 'passed' | 'failed';
    is_rigorous?: boolean;
    reason?: string;
    verdict?: string;
    details?: string;
    [key: string]: any;
  };
  early_stop?: boolean;
  early_stop_reason?: string;
  [key: string]: any;
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
  category_display?: string; // 类别显示名称
  title: string;
  description: string | null;
  baidu_link: string;
  extract_code: string | null;
  download_count: number;
  problem_count?: number; // 题目数量
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

