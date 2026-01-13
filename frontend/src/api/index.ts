/**
 * API 统一导出 - 三重质检工具
 */

import apiClient from './axios';

export { apiClient };

// 题目质检 API
export const problemApi = {
  // OCR 识别
  ocrImage: async (image: File) => {
    // 将文件转为 base64
    const base64 = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        resolve(result.split(',')[1]);
      };
      reader.onerror = reject;
      reader.readAsDataURL(image);
    });
    
    const response = await apiClient.post('/problems/ocr', {
      image_base64: base64,
      extract_answer: true
    });
    return response.data;
  },

  // 启动异步难度检测，返回task_id
  startDifficultyCheck: async (content: any, answer: string, explanation?: string) => {
    const response = await apiClient.post('/problems/check-difficulty-start', {
      content: typeof content === 'string' ? content : JSON.stringify(content),
      answer,
      explanation,
    });
    return response.data as { task_id: string };
  },

  // 订阅难度检测进度（SSE方式）
  subscribeDifficultyProgress: (taskId: string): EventSource => {
    let baseUrl = apiClient.defaults.baseURL || '';
    
    // 如果是相对路径（如 /api），需要转换为完整 URL
    if (baseUrl.startsWith('/')) {
      const origin = window.location.origin;
      baseUrl = `${origin}${baseUrl}`;
    }
    
    const url = `${baseUrl}/problems/check-difficulty-stream/${taskId}`;
    return new EventSource(url);
  },

  // 查询难度检测当前进度
  getDifficultyProgress: async (taskId: string) => {
    const response = await apiClient.get(`/problems/check-difficulty-progress/${taskId}`);
    return response.data as { progress: number; result?: any };
  },

  // 检测原创性
  checkOriginality: async (content: any, answer: string, explanation?: string) => {
    const response = await apiClient.post('/problems/check-originality', {
      content: typeof content === 'string' ? content : JSON.stringify(content),
      answer,
      explanation,
    });
    return response.data;
  },

  // 检测严谨性
  checkRigor: async (content: any, answer: string, explanation?: string) => {
    const response = await apiClient.post('/problems/check-rigor', {
      content: typeof content === 'string' ? content : JSON.stringify(content),
      answer,
      explanation,
    });
    return response.data;
  },
};
