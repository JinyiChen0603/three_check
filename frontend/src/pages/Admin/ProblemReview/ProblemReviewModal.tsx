/**
 * 题目审核详情模态框
 */

import { useState } from 'react';
import { Modal, Descriptions, Tag, Space, Button, Input, Card, Table } from 'antd';
import { CheckOutlined, CloseOutlined } from '@ant-design/icons';
import MathRenderer from '../../../components/MathRenderer';

const { TextArea } = Input;

interface ProblemReviewModalProps {
  visible: boolean;
  problem: any;
  onReview: (approved: boolean, note?: string) => void;
  onCancel: () => void;
}

export function ProblemReviewModal({ visible, problem, onReview, onCancel }: ProblemReviewModalProps) {
  const [note, setNote] = useState('');
  const [approvingLoading, setApprovingLoading] = useState(false);
  const [rejectingLoading, setRejectingLoading] = useState(false);

  const handleReview = async (approved: boolean) => {
    if (approved) {
      setApprovingLoading(true);
    } else {
      setRejectingLoading(true);
    }
    
    try {
      await onReview(approved, note);
      setNote('');
    } finally {
      if (approved) {
        setApprovingLoading(false);
      } else {
        setRejectingLoading(false);
      }
    }
  };

  // 清理内容中的方括号包裹（如果有的话）
  const cleanContent = (content: string) => {
    if (!content) return '';
    // 移除开头的 "[ " 和结尾的 " ]"
    let cleaned = content.trim();
    if (cleaned.startsWith('[') && cleaned.endsWith(']')) {
      cleaned = cleaned.slice(1, -1).trim();
    }
    return cleaned;
  };

  // 评分记录列
  const reviewColumns = [
    {
      title: '评分人',
      dataIndex: 'reviewer_username',
      key: 'reviewer_username',
    },
    {
      title: '答案正确',
      dataIndex: 'is_answer_correct',
      key: 'is_answer_correct',
      render: (correct: boolean) =>
        correct ? <Tag color="success">正确</Tag> : <Tag color="error">错误</Tag>,
    },
    {
      title: '创新性评分',
      dataIndex: 'innovation_score',
      key: 'innovation_score',
      render: (score: number | null) => score !== null ? score : '-',
    },
    {
      title: '严谨性评分',
      dataIndex: 'rigor_score',
      key: 'rigor_score',
      render: (score: number | null) => score !== null ? score : '-',
    },
    {
      title: '一票否决',
      dataIndex: 'is_vetoed',
      key: 'is_vetoed',
      render: (vetoed: boolean) =>
        vetoed ? <Tag color="error">是</Tag> : <Tag color="success">否</Tag>,
    },
    {
      title: '否决理由',
      dataIndex: 'veto_reason',
      key: 'veto_reason',
      ellipsis: true,
      render: (reason: string | null) => reason || '-',
    },
    {
      title: '评论',
      dataIndex: 'comment',
      key: 'comment',
      ellipsis: true,
      render: (comment: string | null) => comment || '-',
    },
  ];

  // 解析三重质检结果
  const getDifficultyResult = () => {
    if (!problem.difficulty_validation) return '未检测';
    return problem.difficulty_validation.passed ? '通过' : '不通过';
  };

  const getOriginalityResult = () => {
    return problem.originality_check?.passed ? '通过' : '不通过';
  };

  const getRigorResult = () => {
    return problem.rigor_check?.passed ? '通过' : '不通过';
  };

  return (
    <Modal
      title="题目审核详情"
      open={visible}
      onCancel={onCancel}
      width={1200}
      footer={
        problem.admin_review_status === 'pending' ? (
          <Space>
            <Button 
              onClick={onCancel}
              disabled={approvingLoading || rejectingLoading}
            >
              取消
            </Button>
            <Button
              type="primary"
              danger
              icon={<CloseOutlined />}
              onClick={() => handleReview(false)}
              loading={rejectingLoading}
              disabled={approvingLoading}
            >
              不通过
            </Button>
            <Button
              type="primary"
              icon={<CheckOutlined />}
              onClick={() => handleReview(true)}
              loading={approvingLoading}
              disabled={rejectingLoading}
            >
              通过
            </Button>
          </Space>
        ) : (
          <Button onClick={onCancel}>关闭</Button>
        )
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* 基本信息 */}
        <Card title="基本信息" size="small">
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="题目ID">{problem.id}</Descriptions.Item>
            <Descriptions.Item label="用户ID">{problem.user_id}</Descriptions.Item>
            <Descriptions.Item label="用户名">{problem.username}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{problem.created_at}</Descriptions.Item>
            <Descriptions.Item label="审核状态" span={2}>
              {problem.admin_review_status === 'pending' && <Tag color="default">待审核</Tag>}
              {problem.admin_review_status === 'approved' && <Tag color="success">已通过</Tag>}
              {problem.admin_review_status === 'rejected' && <Tag color="error">未通过</Tag>}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 题目内容 */}
        <Card title="题目内容" size="small">
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="题目">
              <div style={{ maxWidth: '100%', overflow: 'auto', wordBreak: 'break-word' }}>
                <MathRenderer content={cleanContent(problem.content)} />
              </div>
            </Descriptions.Item>
            <Descriptions.Item label="答案">
              <div style={{ maxWidth: '100%', overflow: 'auto', wordBreak: 'break-word' }}>
                <MathRenderer content={cleanContent(problem.answer)} />
              </div>
            </Descriptions.Item>
            <Descriptions.Item label="解析">
              <div style={{ maxWidth: '100%', overflow: 'auto', wordBreak: 'break-word' }}>
                <MathRenderer content={cleanContent(problem.explanation)} />
              </div>
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 三重质检结果 */}
        <Card title="三重质检结果" size="small">
          <Descriptions column={3} bordered size="small">
            <Descriptions.Item label="难度检测">
              {getDifficultyResult() === '通过' ? (
                <Tag color="success">通过</Tag>
              ) : getDifficultyResult() === '不通过' ? (
                <Tag color="error">不通过</Tag>
              ) : (
                <Tag>未检测</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="原创性检测">
              {getOriginalityResult() === '通过' ? (
                <Tag color="success">通过</Tag>
              ) : (
                <Tag color="error">不通过</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="严谨性检测">
              {getRigorResult() === '通过' ? (
                <Tag color="success">通过</Tag>
              ) : (
                <Tag color="error">不通过</Tag>
              )}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 人工评分记录 */}
        <Card title="人工评分记录" size="small">
          {problem.reviews && problem.reviews.length > 0 ? (
            <Table
              columns={reviewColumns}
              dataSource={problem.reviews}
              rowKey="id"
              pagination={false}
              size="small"
            />
          ) : (
            <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
              暂无评分记录
            </div>
          )}
        </Card>

        {/* 已有审核信息（如果已审核） */}
        {problem.admin_review_status !== 'pending' && (
          <Card title="审核信息" size="small">
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="审核人">
                {problem.admin_reviewer_username || '未知'}
              </Descriptions.Item>
              <Descriptions.Item label="审核时间">
                {problem.admin_reviewed_at || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="审核备注">
                {problem.admin_review_note || '-'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}

        {/* 审核备注（仅待审核状态显示） */}
        {problem.admin_review_status === 'pending' && (
          <Card title="审核备注（可选）" size="small">
            <TextArea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="输入审核备注..."
              rows={3}
            />
          </Card>
        )}
      </Space>
    </Modal>
  );
}

