import { Alert, Button, Space, Table, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';

import type { VariantItem } from '../types';

export function QualityCheckStep({
  passedVariants,
  onBack,
  onSubmitAll,
}: {
  passedVariants: VariantItem[];
  onBack: () => void;
  onSubmitAll: () => Promise<void> | void;
}) {
  const columns: ColumnsType<VariantItem> = [
    { title: '题目内容', dataIndex: 'content', key: 'content', ellipsis: true, render: (c: any) => (typeof c === 'string' ? c : (c as any)?.text ?? String(c ?? '')) },
    { title: '答案', dataIndex: 'answer', key: 'answer', ellipsis: true },
  ];

  return (
    <Space orientation="vertical" style={{ width: '100%' }} size="large">
      <Alert
        message="恭喜！"
        description={`您已完成 ${passedVariants.length} 个合格题目的创建。这些题目将进入人工质检流程。`}
        type="success"
        showIcon
      />

      <Table columns={columns} dataSource={passedVariants} rowKey="key" pagination={false} />

      <Space>
        <Button onClick={onBack}>返回上一步</Button>
        <Button
          type="primary"
          onClick={async () => {
            if (passedVariants.length === 0) {
              message.warning('没有合格的题目可以提交');
              return;
            }
            await onSubmitAll();
          }}
        >
          提交所有合格题目
        </Button>
      </Space>
    </Space>
  );
}



