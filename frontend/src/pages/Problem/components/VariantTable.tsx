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
      render: (_: any, record: VariantItem) => {
        // 直接从 record.content 获取，因为 dataIndex 已经指定了 'content'
        // 但为了保险，我们也直接从 record 获取
        const content = record.content;
        
        // 处理字符串格式
        if (typeof content === 'string') {
          return content;
        }
        
        // 处理对象格式 { text: "..." }
        if (content && typeof content === 'object') {
          const textValue = (content as any).text;
          if (typeof textValue === 'string' && textValue.trim()) {
            return textValue;
          }
          // 如果是其他对象格式，尝试 JSON 序列化
          return JSON.stringify(content);
        }
        
        // 如果 content 为空，返回空字符串
        return '';
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
            <Space orientation="vertical" size="small">
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



