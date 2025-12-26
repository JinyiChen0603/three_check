/**
 * 任务管理页面
 */

import { useState } from 'react';
import {
  Button,
  Space,
  Tabs,
  Typography,
  Card,
} from 'antd';
import {
  FileTextOutlined,
  CheckCircleOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { useTask } from '../../hooks/useTask';
import { useConfig } from '../../hooks/useConfig';
import { TaskType, TaskStatus } from '../../config/constants';
import { getUniqueBatchTasks } from '../../services/taskService';
import { TaskStats } from './components/TaskStats';
import { TaskList } from './components/TaskList';
import { ClaimTaskModal } from './components/ClaimTaskModal';

const { Title, Text } = Typography;

export default function Tasks() {
  const config = useConfig();
  
  // 使用自定义Hook管理任务状态
  const {
    tasks,
    loading,
    problemCreationTotal,
    problemCreationCompleted,
    problemReviewTotal,
    problemReviewCompleted,
    claimTasks,
    abandonTask,
    submitTask,
  } = useTask();

  const [claimModalVisible, setClaimModalVisible] = useState(false);
  const [claimCount, setClaimCount] = useState(10);
  const [claimLoading, setClaimLoading] = useState(false);
  const [currentTaskType, setCurrentTaskType] = useState<TaskType>(
    TaskType.PROBLEM_CREATION
  );

  const handleClaimTasks = async () => {
    if (claimCount < 1 || claimCount > config.maxTasksPerClaim) {
      return;
    }

    try {
      setClaimLoading(true);
      await claimTasks(currentTaskType, claimCount);
      setClaimModalVisible(false);
      setClaimCount(10); // 重置数量
    } catch (error) {
      // 错误已在Hook中处理
    } finally {
      setClaimLoading(false);
    }
  };

  // 按批次去重后的任务列表（避免评分任务显示多条重复记录）
  const uniqueTasks = getUniqueBatchTasks(tasks);
  
  const problemCreationTasks = uniqueTasks.filter(
    (t) => t.task_type === TaskType.PROBLEM_CREATION
  );
  const problemReviewTasks = uniqueTasks.filter(
    (t) => t.task_type === TaskType.PROBLEM_REVIEW
  );

  // 检查是否有进行中的任务
  const hasInProgressTasks = uniqueTasks.some(
    (t) => t.status === TaskStatus.IN_PROGRESS
  );

  return (
    <div>
      <Title level={2}>任务管理</Title>

      {/* 统计卡片 */}
      <TaskStats 
        problemCreationTotal={problemCreationTotal} 
        problemCreationCompleted={problemCreationCompleted}
        problemReviewTotal={problemReviewTotal} 
        problemReviewCompleted={problemReviewCompleted}
      />

      {/* 任务列表 */}
      <Card>
        <Tabs 
          defaultActiveKey="problem_creation"
          items={[
            {
              key: 'problem_creation',
              label: (
                <span>
                  <FileTextOutlined />
                  出题任务 ({problemCreationTotal})
                </span>
              ),
              children: (
                <>
                  <Space style={{ marginBottom: 16 }}>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => {
                        setCurrentTaskType(TaskType.PROBLEM_CREATION);
                        setClaimModalVisible(true);
                      }}
                      disabled={hasInProgressTasks}
                    >
                      领取出题任务
                    </Button>
                    <Text type="secondary">
                      每个任务需在 {config.taskTimeoutHours} 小时内完成
                      {hasInProgressTasks && '（请先完成或放弃当前任务）'}
                    </Text>
                  </Space>
                  
                  <TaskList
                    tasks={problemCreationTasks}
                    loading={loading}
                    onAbandon={async (taskId) => {
                      try {
                        await abandonTask(taskId);
                      } catch (error) {
                        // 错误已在Hook中处理
                      }
                    }}
                    onSubmit={async (taskId) => {
                      try {
                        await submitTask(taskId);
                      } catch (error) {
                        // 错误已在Hook中处理
                      }
                    }}
                  />
                </>
              ),
            },
            {
              key: 'problem_review',
              label: (
                <span>
                  <CheckCircleOutlined />
                  评分任务 ({problemReviewTotal})
                </span>
              ),
              children: (
                <>
                  <Space style={{ marginBottom: 16 }}>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => {
                        setCurrentTaskType(TaskType.PROBLEM_REVIEW);
                        setClaimModalVisible(true);
                      }}
                      disabled={hasInProgressTasks}
                    >
                      领取评分任务
                    </Button>
                    <Text type="secondary">
                      每个任务需在 {config.taskTimeoutHours} 小时内完成
                      {hasInProgressTasks && '（请先完成或放弃当前任务）'}
                    </Text>
                  </Space>
                  
                  <TaskList
                    tasks={problemReviewTasks}
                    loading={loading}
                    onAbandon={async (taskId) => {
                      try {
                        await abandonTask(taskId);
                      } catch (error) {
                        // 错误已在Hook中处理
                      }
                    }}
                  />
                </>
              ),
            },
          ]}
        />
      </Card>

      {/* 领取任务对话框 */}
      <ClaimTaskModal
        open={claimModalVisible}
        currentTaskType={currentTaskType}
        claimCount={claimCount}
        setClaimCount={setClaimCount}
        onOk={handleClaimTasks}
        onCancel={() => setClaimModalVisible(false)}
        loading={claimLoading}
      />
    </div>
  );
}

