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
  Modal,
} from 'antd';
import {
  FileTextOutlined,
  CheckCircleOutlined,
  PlusOutlined,
  ExclamationCircleOutlined,
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

  // 处理放弃任务（带确认对话框）
  const handleAbandonTask = async (taskId: number) => {
    try {
      // 第一次调用：检查是否需要确认
      const response = await abandonTask(taskId, false);
      
      // 如果需要确认
      if (response?.requires_confirmation) {
        Modal.confirm({
          title: '确认放弃任务',
          icon: <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />,
          content: (
            <div>
              <p>{response.message}</p>
              <p style={{ color: '#ff4d4f', marginTop: 8 }}>
                {response.warning}
              </p>
            </div>
          ),
          okText: '确认放弃',
          okType: 'danger',
          cancelText: '取消',
          onOk: async () => {
            // 第二次调用：确认放弃
            await abandonTask(taskId, true);
          }
        });
      }
      // 如果不需要确认，abandonTask 会直接成功并刷新列表
    } catch (error) {
      // 错误已在Hook中处理
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
                  出题任务
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
                    onAbandon={handleAbandonTask}
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
                  评分任务
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
                    onAbandon={handleAbandonTask}
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

