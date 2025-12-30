export interface ReviewChoiceResponse {
  validated_problem_id: number;
  problem_content: any;
  problem_explanation?: string;
  choices: string[];
  correct_index?: number;
  instruction?: string;
}

export interface TaskItem {
  task_id: number;
  validated_problem_id: number;
  status: string;  // Task状态：in_progress, timeout等
  has_review: boolean;  // 是否已有评分记录（判断是否已评分）
}

export interface TaskBatch {
  batch_id: string;
  task_type: string;
  status: string;
  total_count: number;
  completed_count: number;
  claimed_at?: string;
  expires_at?: string;
  tasks: TaskItem[];
}


