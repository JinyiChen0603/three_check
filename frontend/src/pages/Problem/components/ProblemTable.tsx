import { Button, Input, Space, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { Table } from 'antd';
import { CheckCircleOutlined, DeleteOutlined, SyncOutlined } from '@ant-design/icons';

import { BUSINESS_CONSTANTS } from '../../../config/constants';
import type { ProblemItem } from '../types';

const { Text } = Typography;
const { TextArea } = Input;

export function ProblemTable({
  problems,
  onProblemChange,
  onValidateSingle,
  onUseSingle,
  onRemove,
}: {
  problems: ProblemItem[];
  onProblemChange: (key: string, field: keyof ProblemItem, value: string) => void;
  onValidateSingle: (problem: ProblemItem) => void;
  onUseSingle: (problem: ProblemItem) => void;
  onRemove: (key: string) => void;
}) {
  const columns: ColumnsType<ProblemItem> = [
    {
      title: '题目内容',
      dataIndex: 'content',
      key: 'content',
      width: '40%',
      render: (text: string, record) => (
        <TextArea
          value={text}
          disabled={
            record.validationStatus === 'validating' ||
            record.validationStatus === 'queued' ||
            record.validationStatus === 'passed'
          }
          style={{
            fontWeight:
              record.validationStatus === 'passed' || record.validationStatus === 'failed'
                ? 600
                : undefined,
          }}
          onChange={(e) => onProblemChange(record.key, 'content', e.target.value)}
          placeholder="请输入题目内容..."
          rows={3}
        />
      ),
    },
    {
      title: '解析',
      dataIndex: 'explanation',
      key: 'explanation',
      width: '25%',
      render: (text: string, record) => (
        <TextArea
          value={text}
          disabled={
            record.validationStatus === 'validating' ||
            record.validationStatus === 'queued' ||
            record.validationStatus === 'passed'
          }
          style={{
            fontWeight:
              record.validationStatus === 'passed' || record.validationStatus === 'failed'
                ? 600
                : undefined,
          }}
          onChange={(e) => onProblemChange(record.key, 'explanation', e.target.value)}
          placeholder="请输入解析（可选）..."
          rows={2}
        />
      ),
    },
    {
      title: '答案',
      dataIndex: 'answer',
      key: 'answer',
      width: '25%',
      render: (text: string, record) => (
        <Input
          value={text}
          disabled={
            record.validationStatus === 'validating' ||
            record.validationStatus === 'queued' ||
            record.validationStatus === 'passed'
          }
          style={{
            fontWeight:
              record.validationStatus === 'passed' || record.validationStatus === 'failed'
                ? 600
                : undefined,
          }}
          onChange={(e) => onProblemChange(record.key, 'answer', e.target.value)}
          placeholder="请输入答案..."
        />
      ),
    },
    {
      title: '验证状态',
      dataIndex: 'validationStatus',
      key: 'validationStatus',
      width: '15%',
      render: (status: string, record) => {
        if (status === 'queued') return <Tag color="default">排队中</Tag>;
        if (status === 'validating')
          return (
            <Tag icon={<SyncOutlined spin />} color="processing">
              验证中
            </Tag>
          );
        if (status === 'passed') {
          return (
            <div>
              <Tag icon={<CheckCircleOutlined />} color="success">
                通过
              </Tag>
              {record.validationResult && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {record.validationResult.correct_count}/{BUSINESS_CONSTANTS.VALIDATION_ATTEMPTS}
                </Text>
              )}
            </div>
          );
        }
        if (status === 'failed') return <Tag color="error">未通过</Tag>;
        return <Tag color="default">待验证</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: '20%',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => onValidateSingle(record)}
            loading={record.validationStatus === 'validating'}
          >
            验证
          </Button>
          <Button
            type="link"
            size="small"
            disabled={record.validationStatus !== 'passed'}
            onClick={() => onUseSingle(record)}
          >
            使用
          </Button>
          <Button
            type="link"
            danger
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => onRemove(record.key)}
          />
        </Space>
      ),
    },
  ];

  return <Table columns={columns} dataSource={problems} rowKey="key" pagination={false} />;
}



