import { InputNumber, Modal, Space, Typography } from 'antd';

import { BUSINESS_CONSTANTS, TaskType } from '../../../config/constants';

const { Text } = Typography;

export function ClaimTaskModal({
  open,
  currentTaskType,
  claimCount,
  setClaimCount,
  onOk,
  onCancel,
  loading,
}: {
  open: boolean;
  currentTaskType: TaskType;
  claimCount: number;
  setClaimCount: (v: number) => void;
  onOk: () => void;
  onCancel: () => void;
  loading?: boolean;
}) {
  return (
    <Modal
      title={`领取${currentTaskType === TaskType.PROBLEM_CREATION ? '出题' : '评分'}任务`}
      open={open}
      onOk={onOk}
      onCancel={onCancel}
      okText="确认领取"
      cancelText="取消"
      confirmLoading={loading}
      okButtonProps={{ disabled: loading }}
    >
      <Space orientation="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Text>领取数量：</Text>
          <InputNumber
            min={1}
            max={BUSINESS_CONSTANTS.MAX_TASKS_PER_CLAIM}
            value={claimCount}
            onChange={(value) => setClaimCount(value || 1)}
            style={{ width: '100%', marginTop: 8 }}
          />
          <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
            每次最多领取 {BUSINESS_CONSTANTS.MAX_TASKS_PER_CLAIM} 个任务
          </Text>
        </div>

        <div>
          <Text strong>注意事项：</Text>
          <ul style={{ marginTop: 8, paddingLeft: 20 }}>
            <li>领取后需在 {BUSINESS_CONSTANTS.TASK_TIMEOUT_HOURS} 小时内完成</li>
            <li>只有完成当前任务后才能继续领取新任务</li>
            <li>可以随时放弃任务，放弃的任务会返回任务池</li>
          </ul>
        </div>
      </Space>
    </Modal>
  );
}


