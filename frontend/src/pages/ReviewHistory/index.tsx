/**
 * 我的评分记录页面
 * 显示用户所有的评分历史
 */

import { useEffect, useState } from 'react';
import { Card, Table, Tag, Typography, Space, Button, message, Descriptions } from 'antd';
import { StarOutlined, CloseCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { reviewApi } from '../../api';
import type { Review } from '../../types';

const { Title, Text } = Typography;

export default function ReviewHistory() {
  const [loading, setLoading] = useState(false);
  const [reviews, setReviews] = useState<Review[]>([]);

  const loadReviews = async () => {
    setLoading(true);
    try {
      const data = await reviewApi.getMyReviews();
      setReviews(data);
    } catch (error) {
      message.error('加载评分记录失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReviews();
  }, []);

  const columns: ColumnsType<Review> = [
    {
      title: '题目ID',
      dataIndex: 'problem_id',
      key: 'problem_id',
      width: 100,
      render: (id) => <Text strong>#{id}</Text>,
    },
    {
      title: '评分情况',
      key: 'correctness',
      width: 100,
      render: (_, record) => {
        const isCorrect = record.is_answer_correct;
        if (isCorrect === undefined || isCorrect === null) return <Tag>未验证</Tag>;
        return isCorrect ? (
          <Tag icon={<CheckCircleOutlined />} color="success">
            回答正确
          </Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="error">
            回答错误
          </Tag>
        );
      },
    },
    {
      title: '创新性评分',
      dataIndex: 'innovation_score',
      key: 'innovation_score',
      width: 120,
      render: (score) => (
        <Space>
          <StarOutlined style={{ color: '#faad14' }} />
          <Text strong>{score !== null && score !== undefined ? `${score} 分` : '-'}</Text>
        </Space>
      ),
    },
    {
      title: '严谨性评分',
      dataIndex: 'rigor_score',
      key: 'rigor_score',
      width: 120,
      render: (score) => (
        <Space>
          <StarOutlined style={{ color: '#1890ff' }} />
          <Text strong>{score !== null && score !== undefined ? `${score} 分` : '-'}</Text>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const statusMap: Record<string, { text: string; color: string }> = {
          pending: { text: '待评分', color: 'default' },
          approved: { text: '已评分', color: 'success' },
          rejected: { text: '已驳回', color: 'error' },
        };
        const config = statusMap[status] || { text: status, color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '一票否决',
      key: 'veto',
      width: 100,
      render: (_, record) => {
        if (record.veto_reason) {
          return (
            <Tag icon={<CloseCircleOutlined />} color="error">
              已否决
            </Tag>
          );
        }
        return <Text type="secondary">-</Text>;
      },
    },
    // {
    //   title: '评分时间',
    //   dataIndex: 'created_at',
    //   key: 'created_at',
    //   width: 180,
    //   render: (date) => new Date(date).toLocaleString('zh-CN'),
    // },
  ];

  const expandedRowRender = (record: Review) => {
    return (
      <Descriptions bordered size="small" column={1}>
        {/* 题目信息区域 */}
        {record.problem && (
          <>
            <Descriptions.Item label="📝 题目内容">
              <div style={{ 
                whiteSpace: 'pre-wrap', 
                padding: '12px',
                background: '#f5f5f5',
                borderRadius: '6px',
                lineHeight: '1.6'
              }}>
                {record.problem.content}
              </div>
            </Descriptions.Item>
            
            <Descriptions.Item label="✅ 正确答案">
              <Text strong style={{ 
                color: '#52c41a', 
                fontSize: '16px',
                padding: '4px 8px',
                background: '#f6ffed',
                borderRadius: '4px'
              }}>
                {record.problem.answer}
              </Text>
            </Descriptions.Item>
            
            <Descriptions.Item label="💡 题目解析">
              <div style={{ 
                whiteSpace: 'pre-wrap',
                padding: '12px',
                background: '#e6f7ff',
                borderRadius: '6px',
                lineHeight: '1.6'
              }}>
                {record.problem.explanation}
              </div>
            </Descriptions.Item>
          </>
        )}
        
        {/* 用户答题信息 */}
        {record.correctness_verification && (
          <Descriptions.Item label="🎯 用户选择">
            <Space>
              <Text strong>
                {record.correctness_verification.selected_answer || 
                 `选项 ${record.correctness_verification.selected_index}`}
              </Text>
              {record.is_answer_correct !== null && record.is_answer_correct !== undefined && (
                record.is_answer_correct ? (
                  <Tag icon={<CheckCircleOutlined />} color="success">回答正确</Tag>
                ) : (
                  <Tag icon={<CloseCircleOutlined />} color="error">回答错误</Tag>
                )
              )}
            </Space>
          </Descriptions.Item>
        )}
        
        {/* 否决理由 */}
        {record.veto_reason && (
          <Descriptions.Item label="❌ 否决理由">
            <Text type="danger" strong>{record.veto_reason}</Text>
          </Descriptions.Item>
        )}
        
        {/* 更新时间
        {record.updated_at && (
          <Descriptions.Item label="⏰ 更新时间">
            {new Date(record.updated_at).toLocaleString('zh-CN')}
          </Descriptions.Item>
        )} */}
      </Descriptions>
    );
  };

  return (
    <div>
      <Title level={2}>我的评分记录</Title>

      <Card>
        <Space orientation="vertical" style={{ width: '100%', marginBottom: 16 }}>
          <Space>
            <Text>共 {reviews.length} 条评分记录</Text>
            <Button onClick={loadReviews} loading={loading}>
              刷新
            </Button>
          </Space>
        </Space>

        <Table
          columns={columns}
          dataSource={reviews}
          rowKey="id"
          loading={loading}
          expandable={{
            expandedRowRender,
            rowExpandable: (record) => 
              record.is_answer_correct !== null && 
              record.is_answer_correct !== undefined &&
              !!record.problem,
          }}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 条记录`,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
        />
      </Card>
    </div>
  );
}

