/**
 * 全局常量配置
 */

// API 基础 URL（优先读取环境变量，默认使用相对路径以便通过反向代理）
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || '/api';

// Token 存储 key
export const TOKEN_KEY = 'mathtasks_token';
export const USER_INFO_KEY = 'mathtasks_user';

// 用户角色（对象 + 字面量类型，避免使用 enum 以兼容 erasableSyntaxOnly）
export const UserRole = {
  ADMIN: 'admin',
  USER: 'user',
} as const;
export type UserRole = (typeof UserRole)[keyof typeof UserRole];

// 任务类型
export const TaskType = {
  PROBLEM_CREATION: 'problem_creation',
  PROBLEM_REVIEW: 'problem_review',
} as const;
export type TaskType = (typeof TaskType)[keyof typeof TaskType];

// 任务状态
export const TaskStatus = {
  AVAILABLE: 'available',
  CLAIMED: 'claimed',
  IN_PROGRESS: 'in_progress',
  SUBMITTED: 'submitted',
  COMPLETED: 'completed',
  REJECTED: 'rejected',
} as const;
export type TaskStatus = (typeof TaskStatus)[keyof typeof TaskStatus];

// 业务常量
export const BUSINESS_CONSTANTS = {
  MAX_TASKS_PER_CLAIM: 50,          // 每次最多领取任务数
  TASK_TIMEOUT_HOURS: 12,            // 任务超时时间（小时）
  REWARD_PER_PROBLEM: 50,            // 每个合格题目奖励（元）
  REWARD_PER_REVIEW: 10,             // 每个评分任务奖励（元）
  MAX_VARIANTS_PER_PROBLEM: 10,     // 每个母题最多变形次数
  MAX_BATCH_VALIDATION: 10,          // 批量验证最多题目数
  VALIDATION_ATTEMPTS: 8,            // AI验证尝试次数
  VALIDATION_THRESHOLD: 4,           // 验证通过阈值
};

// 资料库类别（与后端 MaterialCategory 枚举保持一致）
export const MATERIAL_CATEGORIES = [
  { key: 'high_school_comprehensive', label: '高中数学联赛综合' },
  { key: 'college_comprehensive', label: '大学数学竞赛综合' },
  { key: 'high_school_algebra', label: '高中数学联赛 - 代数' },
  { key: 'high_school_geometry', label: '高中数学联赛 - 几何' },
  { key: 'high_school_number_theory', label: '高中数学联赛 - 数论' },
  { key: 'high_school_combinatorics', label: '高中数学联赛 - 组合' },
  { key: 'college_algebra', label: '大学数学竞赛 - 代数' },
  { key: 'college_number_theory', label: '大学数学竞赛 - 数论' },
  { key: 'college_analysis', label: '大学数学竞赛 - 分析和方程' },
  { key: 'college_combinatorics', label: '大学数学竞赛 - 组合和概率' },
  { key: 'college_geometry', label: '大学数学竞赛 - 几何和拓扑' },
  { key: 'college_optimization', label: '大学数学竞赛 - 最优化方法' },
];

