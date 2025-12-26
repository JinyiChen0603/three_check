/**
 * 配置管理Hook
 * 从后端获取配置信息
 */

import { useState, useEffect } from 'react';
import { configApi } from '../api';

interface AppConfig {
  maxTasksPerClaim: number;
  taskTimeoutHours: number;
  rewardPerProblem: number;
  rewardPerReview: number;
}

let cachedConfig: AppConfig | null = null;
let configPromise: Promise<AppConfig> | null = null;

export function useConfig(): AppConfig {
  const [config, setConfig] = useState<AppConfig>(() => {
    // 如果有缓存，直接返回
    if (cachedConfig) {
      return cachedConfig;
    }
    // 默认值（如果API调用失败时使用）
    return {
      maxTasksPerClaim: 50,
      taskTimeoutHours: 12,
      rewardPerProblem: 50,
      rewardPerReview: 10,
    };
  });

  useEffect(() => {
    // 如果已经有缓存的配置，不需要重新获取
    if (cachedConfig) {
      return;
    }

    // 如果已经有正在进行的请求，等待它完成
    if (configPromise) {
      configPromise.then(setConfig).catch(() => {
        // 如果请求失败，使用默认值（已经在useState中设置）
      });
      return;
    }

    // 发起新的请求
    configPromise = configApi.getConfig().then((data) => {
      const appConfig: AppConfig = {
        maxTasksPerClaim: data.max_tasks_per_claim,
        taskTimeoutHours: data.task_timeout_hours,
        rewardPerProblem: data.reward_per_problem,
        rewardPerReview: data.reward_per_review,
      };
      cachedConfig = appConfig;
      setConfig(appConfig);
      return appConfig;
    }).catch((error) => {
      console.error('获取配置失败:', error);
      // 请求失败时，使用默认值（已经在useState中设置）
      return config;
    });

    // 清理promise引用
    configPromise.finally(() => {
      configPromise = null;
    });
  }, []);

  return config;
}

