import { Button, Modal, Space, Table, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { SyncOutlined } from '@ant-design/icons';

import type { VariantItem } from '../types';

export function VariantTable({
  parentId,
  variants,
  onQualityCheck,
  onSubmitForReview,
  onDeleteVariant,
}: {
  parentId: number;
  variants: VariantItem[];
  onQualityCheck: (parentId: number, variant: VariantItem) => void;
  onSubmitForReview: (parentId: number, variant: VariantItem) => void;
  onDeleteVariant: (parentId: number, variantKey: string) => void;
}) {
  const columns: ColumnsType<VariantItem> = [
    {
      title: '题目内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (content: any) => {
        // 后端可能返回 {text: "..."} 或 string，这里做最小兼容
        if (typeof content === 'string') return content;
        if (content && typeof content === 'object' && typeof content.text === 'string') return content.text;
        return String(content ?? '');
      },
    },
    {
      title: '质量检查',
      key: 'quality',
      render: (_, record) => {
        if (record.qualityCheckStatus === 'checking') {
          return (
            <Tag icon={<SyncOutlined spin />} color="processing">
              检查中
            </Tag>
          );
        }
        if (record.qualityCheckStatus === 'passed') {
          return (
            <Space direction="vertical" size="small">
              <Tag color="success">全部通过</Tag>
              {record.quality_check && (
                <Space size="small">
                  <Tag color="blue">难度✓</Tag>
                  <Tag color="green">原创✓</Tag>
                  <Tag color="purple">严谨✓</Tag>
                </Space>
              )}
            </Space>
          );
        }
        if (record.qualityCheckStatus === 'failed') {
          return <Tag color="error">未通过</Tag>;
        }
        return <Tag color="default">待检查</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => onQualityCheck(parentId, record)}
            loading={record.qualityCheckStatus === 'checking'}
          >
            质检
          </Button>
          <Button
            type="link"
            size="small"
            disabled={record.qualityCheckStatus !== 'passed'}
            onClick={() => onSubmitForReview(parentId, record)}
          >
            提交审核
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => {
              Modal.info({
                title: '题目详情',
                width: 800,
                content: (
                  <div>
                    <p>
                      <strong>内容：</strong>
                      {typeof record.content === 'string'
                        ? record.content
                        : (record.content as any)?.text ?? String(record.content ?? '')}
                    </p>
                    <p>
                      <strong>答案：</strong>
                      {record.answer}
                    </p>
                    {record.explanation && (
                      <p>
                        <strong>解析：</strong>
                        {record.explanation}
                      </p>
                    )}
                  </div>
                ),
              });
            }}
          >
            查看
          </Button>
          <Button type="link" danger size="small" onClick={() => onDeleteVariant(parentId, record.key)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return <Table columns={columns} dataSource={variants} rowKey="key" pagination={false} />;
}



