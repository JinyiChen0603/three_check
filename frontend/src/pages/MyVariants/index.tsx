/**
 * 我的变体题目页面
 * 显示用户创建的所有变体题目列表
 */

import { useEffect, useState } from 'react';
import { Card, Table, Tag, Typography, Space, Button, message, Modal, Descriptions, Spin } from 'antd';
import { EyeOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import { problemApi } from '../../api';

const { Title, Text, Paragraph } = Typography;

// TODO: 以后可扩展更多字段，如 title, status, category 等
interface VariantItem {
  id: number;
  parent_problem_id: number;
  created_at: string;
}

interface ProblemDetail {
  id: number;
  title: string;
  content: any;
  explanation?: string;
  answer: string;
  category: string;
  status: string;
  created_at: string;
}

export default function MyVariants() {
  const [loading, setLoading] = useState(false);
  const [variants, setVariants] = useState<VariantItem[]>([]);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });
  
  // 详情弹窗状态
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [selectedProblem, setSelectedProblem] = useState<ProblemDetail | null>(null);

  const loadVariants = async (page = 1, pageSize = 20) => {
    setLoading(true);
    try {
      const skip = (page - 1) * pageSize;
      const data = await problemApi.getMyVariants(skip, pageSize);
      setVariants(data.items);
      setTotal(data.total);
    } catch (error) {
      message.error('加载变体题目列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVariants(pagination.current, pagination.pageSize);
  }, []);

  const handleTableChange = (pag: TablePaginationConfig) => {
    const newPagination = {
      current: pag.current || 1,
      pageSize: pag.pageSize || 20,
    };
    setPagination(newPagination);
    loadVariants(newPagination.current, newPagination.pageSize);
  };

  const handleViewDetail = async (record: VariantItem) => {
    setDetailModalOpen(true);
    setDetailLoading(true);
    setSelectedProblem(null);
    try {
      const detail = await problemApi.getProblemDetail(record.id);
      setSelectedProblem(detail);
    } catch (error) {
      message.error('加载题目详情失败');
      setDetailModalOpen(false);
    } finally {
      setDetailLoading(false);
    }
  };

  // TODO: 状态映射暂不使用，后续可按需开启（用于详情弹窗）
  const statusMap: Record<string, { text: string; color: string }> = {
    draft: { text: '草稿', color: 'default' },
    pending_review: { text: '待审核', color: 'processing' },
    published: { text: '已发布', color: 'success' },
    rejected: { text: '已拒绝', color: 'error' },
  };

  // TODO: 以后可扩展更多列，如 title, status, category 等
  const columns: ColumnsType<VariantItem> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      render: (id) => <Text strong>#{id}</Text>,
    },
    {
      title: '母题ID',
      dataIndex: 'parent_problem_id',
      key: 'parent_problem_id',
      width: 100,
      render: (id) => <Text type="secondary">#{id}</Text>,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetail(record)}
        >
          查看
        </Button>
      ),
    },
  ];

  // 渲染题目内容
  const renderContent = (content: any) => {
    if (!content) return '-';
    if (typeof content === 'string') return content;
    if (typeof content === 'object') {
      if (content.text) return content.text;
      return JSON.stringify(content, null, 2);
    }
    return String(content);
  };

  return (
    <div>
      <Title level={2}>我的变体题目</Title>

      <Card>
        <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
          <Space>
            <Text>共 {total} 道变体题目</Text>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => loadVariants(pagination.current, pagination.pageSize)}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        </Space>

        <Table
          columns={columns}
          dataSource={variants}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: total,
            showTotal: (t) => `共 ${t} 条记录`,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
          onChange={handleTableChange}
        />
      </Card>

      {/* 题目详情弹窗 */}
      <Modal
        title={selectedProblem ? `题目详情 #${selectedProblem.id}` : '题目详情'}
        open={detailModalOpen}
        onCancel={() => setDetailModalOpen(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalOpen(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {detailLoading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>加载中...</div>
          </div>
        ) : selectedProblem ? (
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="标题">
              {selectedProblem.title}
            </Descriptions.Item>
            <Descriptions.Item label="类别">
              <Tag>{selectedProblem.category}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              {(() => {
                const config = statusMap[selectedProblem.status] || { text: selectedProblem.status, color: 'default' };
                return <Tag color={config.color}>{config.text}</Tag>;
              })()}
            </Descriptions.Item>
            <Descriptions.Item label="题目内容">
              <Paragraph
                style={{
                  whiteSpace: 'pre-wrap',
                  maxHeight: 300,
                  overflow: 'auto',
                  margin: 0,
                }}
              >
                {renderContent(selectedProblem.content)}
              </Paragraph>
            </Descriptions.Item>
            <Descriptions.Item label="答案">
              <Text code>{selectedProblem.answer}</Text>
            </Descriptions.Item>
            {selectedProblem.explanation && (
              <Descriptions.Item label="解析">
                <Paragraph
                  style={{
                    whiteSpace: 'pre-wrap',
                    maxHeight: 200,
                    overflow: 'auto',
                    margin: 0,
                  }}
                >
                  {selectedProblem.explanation}
                </Paragraph>
              </Descriptions.Item>
            )}
            <Descriptions.Item label="创建时间">
              {new Date(selectedProblem.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
          </Descriptions>
        ) : null}
      </Modal>
    </div>
  );
}

