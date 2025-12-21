export interface ReviewChoiceResponse {
  problem_id: number;
  problem_title?: string;
  problem_content: any;
  problem_explanation?: string;
  choices: string[];
  correct_index?: number;
  instruction?: string;
}

export interface TaskItem {
  task_id: number;
  problem_id: number;
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


