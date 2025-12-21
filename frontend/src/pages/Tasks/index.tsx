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
import { BUSINESS_CONSTANTS, TaskType } from '../../config/constants';
import { TaskStats } from './components/TaskStats';
import { TaskList } from './components/TaskList';
import { ClaimTaskModal } from './components/ClaimTaskModal';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

export default function Tasks() {
  // 使用自定义Hook管理任务状态
  const {
    tasks,
    loading,
    problemCreationTotal,
    problemReviewTotal,
    claimTasks,
    abandonTask,
  } = useTask();

  const [claimModalVisible, setClaimModalVisible] = useState(false);
  const [claimCount, setClaimCount] = useState(10);
  const [currentTaskType, setCurrentTaskType] = useState<TaskType>(
    TaskType.PROBLEM_CREATION
  );

  const handleClaimTasks = async () => {
    if (claimCount < 1 || claimCount > BUSINESS_CONSTANTS.MAX_TASKS_PER_CLAIM) {
      return;
    }

    try {
      await claimTasks(currentTaskType, claimCount);
      setClaimModalVisible(false);
      setClaimCount(10); // 重置数量
    } catch (error) {
      // 错误已在Hook中处理
    }
  };

  const problemCreationTasks = tasks.filter(
    (t) => t.task_type === TaskType.PROBLEM_CREATION
  );
  const problemReviewTasks = tasks.filter(
    (t) => t.task_type === TaskType.PROBLEM_REVIEW
  );

  return (
    <div>
      <Title level={2}>任务管理</Title>

      {/* 统计卡片 */}
      <TaskStats problemCreationTotal={problemCreationTotal} problemReviewTotal={problemReviewTotal} />

      {/* 任务列表 */}
      <Card>
        <Tabs defaultActiveKey="problem_creation">
          <TabPane
            tab={
              <span>
                <FileTextOutlined />
                出题任务 ({problemCreationTotal})
              </span>
            }
            key="problem_creation"
          >
            <Space style={{ marginBottom: 16 }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setCurrentTaskType(TaskType.PROBLEM_CREATION);
                  setClaimModalVisible(true);
                }}
              >
                领取出题任务
              </Button>
              <Text type="secondary">
                每个任务需在 {BUSINESS_CONSTANTS.TASK_TIMEOUT_HOURS} 小时内完成
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
            />
          </TabPane>

          <TabPane
            tab={
              <span>
                <CheckCircleOutlined />
                评分任务 ({problemReviewTotal})
              </span>
            }
            key="problem_review"
          >
            <Space style={{ marginBottom: 16 }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setCurrentTaskType(TaskType.PROBLEM_REVIEW);
                  setClaimModalVisible(true);
                }}
              >
                领取评分任务
              </Button>
              <Text type="secondary">
                每个任务需在 {BUSINESS_CONSTANTS.TASK_TIMEOUT_HOURS} 小时内完成
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
          </TabPane>
        </Tabs>
      </Card>

      {/* 领取任务对话框 */}
      <ClaimTaskModal
        open={claimModalVisible}
        currentTaskType={currentTaskType}
        claimCount={claimCount}
        setClaimCount={setClaimCount}
        onOk={handleClaimTasks}
        onCancel={() => setClaimModalVisible(false)}
      />
    </div>
  );
}

