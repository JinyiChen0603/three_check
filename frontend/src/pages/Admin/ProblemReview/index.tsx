/**
 * 管理员题目审核页面
 */

import { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Tag, Select, message, Modal, Descriptions } from 'antd';
import { EyeOutlined, CheckOutlined, CloseOutlined, DownloadOutlined } from '@ant-design/icons';
import { adminApi } from '../../../api';
import { ProblemReviewModal } from './ProblemReviewModal';

const { Option } = Select;

export default function ProblemReview() {
  const [loading, setLoading] = useState(false);
  const [problems, setProblems] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const [selectedProblem, setSelectedProblem] = useState<any>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [exporting, setExporting] = useState(false);

  // 加载题目列表
  const loadProblems = async () => {
    setLoading(true);
    try {
      const response = await adminApi.getPendingReviewProblems(statusFilter, 0, 100);
      setProblems(response.problems || []);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加载题目列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProblems();
  }, [statusFilter]);

  // 查看详情
  const handleView = async (problemId: number) => {
    try {
      const detail = await adminApi.getProblemReviewDetail(problemId);
      setSelectedProblem(detail);
      setModalVisible(true);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加载题目详情失败');
    }
  };

  // 审核通过/不通过
  const handleReview = async (approved: boolean, note?: string) => {
    if (!selectedProblem) return;

    try {
      await adminApi.reviewProblem(selectedProblem.id, approved, note);
      message.success(approved ? '审核通过' : '审核未通过');
      setModalVisible(false);
      setSelectedProblem(null);
      loadProblems();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '审核失败');
    }
  };

  // 导出题目（根据当前筛选条件）
  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await adminApi.exportProblems(statusFilter || undefined);

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // 根据当前筛选条件生成文件名
      const statusText = {
        '': '全部',
        'pending': '待审核',
        'approved': '已通过',
        'rejected': '未通过',
      }[statusFilter] || '全部';
      
      link.download = `题目审核_${statusText}_${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      message.success('✅ 导出成功！');
    } catch (error) {
      console.error('导出失败:', error);
      message.error('导出失败，请重试');
    } finally {
      setExporting(false);
    }
  };

  const columns = [
    {
      title: '序号',
      key: 'index',
      width: 60,
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: '用户ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 120,
    },
    {
      title: '题目',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      width: 200,
    },
    {
      title: '解析',
      dataIndex: 'explanation',
      key: 'explanation',
      ellipsis: true,
      width: 150,
    },
    {
      title: '答案',
      dataIndex: 'answer',
      key: 'answer',
      ellipsis: true,
      width: 100,
    },
    {
      title: '难度检测',
      dataIndex: 'difficulty_passed',
      key: 'difficulty_passed',
      width: 100,
      render: (passed: boolean | null) => {
        if (passed === null) return <Tag>未检测</Tag>;
        return passed ? <Tag color="success">通过</Tag> : <Tag color="error">不通过</Tag>;
      },
    },
    {
      title: '原创性',
      dataIndex: 'originality_passed',
      key: 'originality_passed',
      width: 90,
      render: (passed: boolean) =>
        passed ? <Tag color="success">通过</Tag> : <Tag color="error">不通过</Tag>,
    },
    {
      title: '严谨性',
      dataIndex: 'rigor_passed',
      key: 'rigor_passed',
      width: 90,
      render: (passed: boolean) =>
        passed ? <Tag color="success">通过</Tag> : <Tag color="error">不通过</Tag>,
    },
    {
      title: '创新性评分',
      dataIndex: 'avg_innovation_score',
      key: 'avg_innovation_score',
      width: 110,
      render: (score: number | null) => (score !== null ? score.toFixed(2) : '-'),
    },
    {
      title: '严谨性评分',
      dataIndex: 'avg_rigor_score',
      key: 'avg_rigor_score',
      width: 110,
      render: (score: number | null) => (score !== null ? score.toFixed(2) : '-'),
    },
    {
      title: '一票否决',
      dataIndex: 'has_veto',
      key: 'has_veto',
      width: 90,
      render: (hasVeto: boolean) =>
        hasVeto ? <Tag color="error">是</Tag> : <Tag color="success">否</Tag>,
    },
    {
      title: '审核状态',
      dataIndex: 'admin_review_status',
      key: 'admin_review_status',
      width: 100,
      render: (status: string) => {
        const statusMap: any = {
          pending: { text: '待审核', color: 'default' },
          approved: { text: '通过', color: 'success' },
          rejected: { text: '未通过', color: 'error' },
        };
        const s = statusMap[status] || statusMap.pending;
        return <Tag color={s.color}>{s.text}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right' as const,
      width: 100,
      render: (_: any, record: any) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleView(record.id)}
          >
            查看
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h1>题目审核</h1>

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <span>审核状态：</span>
          <Select
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 150 }}
          >
            <Option value="">全部</Option>
            <Option value="pending">待审核</Option>
            <Option value="approved">已通过</Option>
            <Option value="rejected">未通过</Option>
          </Select>

          <Button
            type="primary"
            icon={<DownloadOutlined />}
            loading={exporting}
            onClick={handleExport}
          >
            导出题目
          </Button>
        </Space>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={problems}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1800 }}
          pagination={{
            pageSize: 20,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      {/* 题目详情审核模态框 */}
      {selectedProblem && (
        <ProblemReviewModal
          visible={modalVisible}
          problem={selectedProblem}
          onReview={handleReview}
          onCancel={() => {
            setModalVisible(false);
            setSelectedProblem(null);
          }}
        />
      )}
    </div>
  );
}

