import { Modal, Typography } from 'antd';

import type { User } from '../../../types';

const { Text } = Typography;

export function ImpersonateModal({
  open,
  targetUser,
  onOk,
  onCancel,
}: {
  open: boolean;
  targetUser: User | null;
  onOk: () => void;
  onCancel: () => void;
}) {
  return (
    <Modal
      open={open}
      title="确认冒充用户"
      okText="确认切换"
      cancelText="取消"
      onOk={onOk}
      onCancel={onCancel}
    >
      <div>
        <p>
          您将以访客模式查看用户 <Text strong>{targetUser?.username}</Text> 的视角
        </p>
        <p>在冒充模式下，您可以：</p>
        <ul>
          <li>查看该用户的所有信息</li>
          <li>以该用户身份浏览系统</li>
        </ul>
        <p style={{ color: '#ff4d4f', marginTop: 16 }}>
          ⚠️ 注意：您仍然是管理员身份，不能代替用户执行操作
        </p>
      </div>
    </Modal>
  );
}


