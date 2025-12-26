/**
 * 题目验证与导出页面
 * 单页面设计：所有功能在一个界面
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Space,
  Typography,
  Input,
  Select,
  Form,
  message,
  Table,
  Tag,
  Divider,
  Modal,
  Spin,
  Statistic,
  Row,
  Col,
  Descriptions,
  Alert,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DownloadOutlined,
  DeleteOutlined,
  PlusOutlined,
  SyncOutlined,
  FileExcelOutlined,
  SafetyCertificateOutlined,
  ExperimentOutlined,
  EyeOutlined,
  EditOutlined,
  SaveOutlined,
  RadarChartOutlined,
} from '@ant-design/icons';
import { problemApi } from '../../api';
import { MATERIAL_CATEGORIES } from '../../config/constants';
import MathRenderer from '../../components/MathRenderer';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface CheckStatus {
  loading: boolean;
  result: any | null;
  passed: boolean | null;
}

interface ProblemFormData {
  problem: string;
  answer: string;
  explanation: string;
}

interface ExportListItem {
  id: number;
  difficulty_passed: boolean | null;
  originality_passed: boolean;
  rigor_passed: boolean;
  created_at: string;
}

export default function TotalPage() {
  const [form] = Form.useForm<ProblemFormData>();

  // 三个检测状态
  const [difficultyCheck, setDifficultyCheck] = useState<CheckStatus>({
    loading: false,
    result: null,
    passed: null,
  });
  const [originalityCheck, setOriginalityCheck] = useState<CheckStatus>({
    loading: false,
    result: null,
    passed: null,
  });
  const [rigorCheck, setRigorCheck] = useState<CheckStatus>({
    loading: false,
    result: null,
    passed: null,
  });

  // 导出列表
  const [exportList, setExportList] = useState<ExportListItem[]>([]);
  const [exportStats, setExportStats] = useState({ total: 0, passed: 0, failed: 0 });
  const [loadingList, setLoadingList] = useState(false);
  const [exporting, setExporting] = useState(false);

  // Modal状态
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [viewModalContent, setViewModalContent] = useState<{
    title: string;
    data: any;
  } | null>(null);

  // 是否可以保存到列表（三个检测都完成即可，无论是否通过）
  const canSaveToList =
    difficultyCheck.result !== null &&
    originalityCheck.result !== null &&
    rigorCheck.result !== null;

  // 验证难度
  const handleCheckDifficulty = async () => {
    try {
      await form.validateFields(['problem', 'answer']);
      const values = form.getFieldsValue();

      setDifficultyCheck({ loading: true, result: null, passed: null });
      const result = await problemApi.validateSingle(
        values.problem,
        values.answer,
        values.explanation
      );

      setDifficultyCheck({
        loading: false,
        result: result,
        passed: result.is_passed || false,
      });

      if (result.is_passed) {
        message.success('✅ 难度检测通过');
      } else {
        message.warning('⚠️ 难度检测未通过');
      }
    } catch (error: any) {
      console.error('难度检测失败:', error);
      setDifficultyCheck({ loading: false, result: null, passed: false });
      if (!error.errorFields) {
        message.error('难度检测失败，请重试');
      }
    }
  };

  // 检测原创性
  const handleCheckOriginality = async () => {
    try {
      await form.validateFields(['problem', 'answer']);
      const values = form.getFieldsValue();

      setOriginalityCheck({ loading: true, result: null, passed: null });
      const result = await problemApi.checkOriginality(
        values.problem,
        values.answer,
        values.explanation
      );

      const passed = result.originality?.is_original || false;
      setOriginalityCheck({
        loading: false,
        result: result.originality,
        passed: passed,
      });

      if (passed) {
        message.success('✅ 原创性检测通过');
      } else {
        message.warning('⚠️ 原创性检测未通过');
      }
    } catch (error: any) {
      console.error('原创性检测失败:', error);
      setOriginalityCheck({ loading: false, result: null, passed: false });
      if (!error.errorFields) {
        message.error('原创性检测失败，请重试');
      }
    }
  };

  // 检测严谨性
  const handleCheckRigor = async () => {
    try {
      await form.validateFields(['problem', 'answer']);
      const values = form.getFieldsValue();

      setRigorCheck({ loading: true, result: null, passed: null });
      const result = await problemApi.checkRigor(
        values.problem,
        values.answer,
        values.explanation
      );

      const passed = result.rigor?.is_rigorous || false;
      setRigorCheck({
        loading: false,
        result: result.rigor,
        passed: passed,
      });

      if (passed) {
        message.success('✅ 严谨性检测通过');
      } else {
        message.warning('⚠️ 严谨性检测未通过');
      }
    } catch (error: any) {
      console.error('严谨性检测失败:', error);
      setRigorCheck({ loading: false, result: null, passed: false });
      if (!error.errorFields) {
        message.error('严谨性检测失败，请重试');
      }
    }
  };

  // 查看检测报告
  const handleViewReport = (type: 'difficulty' | 'originality' | 'rigor') => {
    let title = '';
    let data = null;

    switch (type) {
      case 'difficulty':
        title = '难度检测报告';
        data = difficultyCheck.result;
        break;
      case 'originality':
        title = '原创性检测报告';
        data = originalityCheck.result;
        break;
      case 'rigor':
        title = '严谨性检测报告';
        data = rigorCheck.result;
        break;
    }

    if (!data) {
      message.warning('请先进行检测');
      return;
    }

    setViewModalContent({ title, data });
    setViewModalVisible(true);
  };

  // 保存到列表
  const handleSaveToList = async () => {
    if (!canSaveToList) {
      message.warning('请先完成所有检测');
      return;
    }

    try {
      await form.validateFields();
      const values = form.getFieldsValue();

      const result = await problemApi.validateAndSave({
        problem: values.problem,
        answer: values.answer,
        explanation: values.explanation,
        include_difficulty: false,
      });

      message.success('✅ 题目已保存到导出列表');
      
      // 刷新列表
      await loadExportList();
      
      // 重置表单和检测状态
      handleReset();
    } catch (error) {
      console.error('保存失败:', error);
      message.error('保存失败，请重试');
    }
  };

  // 删除题目（重置）
  const handleDelete = () => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除当前题目吗？所有检测结果将被清空。',
      okText: '确认',
      cancelText: '取消',
      okType: 'danger',
      onOk: handleReset,
    });
  };

  // 重置表单和状态
  const handleReset = () => {
    form.resetFields();
    setDifficultyCheck({ loading: false, result: null, passed: null });
    setOriginalityCheck({ loading: false, result: null, passed: null });
    setRigorCheck({ loading: false, result: null, passed: null });
  };

  // 修改（仅重置检测状态）
  const handleModify = () => {
    setDifficultyCheck({ loading: false, result: null, passed: null });
    setOriginalityCheck({ loading: false, result: null, passed: null });
    setRigorCheck({ loading: false, result: null, passed: null });
    message.info('已清除检测结果，请修改题目后重新检测');
  };

  // 加载导出列表
  const loadExportList = async () => {
    setLoadingList(true);
    try {
      const data = await problemApi.getExportList();
      setExportList(data.problems || []);
      setExportStats({
        total: data.total || 0,
        passed: data.passed || 0,
        failed: data.failed || 0,
      });
    } catch (error) {
      console.error('加载列表失败:', error);
      message.error('加载导出列表失败');
    } finally {
      setLoadingList(false);
    }
  };

  // 导出Excel
  const handleExport = async (onlyPassed: boolean = true) => {
    setExporting(true);
    try {
      const blob = await problemApi.exportValidated(onlyPassed);

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `验证题目_${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      message.success('✅ 导出成功！');
      await loadExportList();
    } catch (error) {
      console.error('导出失败:', error);
      message.error('导出失败，请重试');
    } finally {
      setExporting(false);
    }
  };

  // 清空列表
  const handleClearList = () => {
    Modal.confirm({
      title: '确认清空',
      content: '确定要清空待导出列表吗？此操作不可恢复。',
      okText: '确认',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await problemApi.clearExportList();
          message.success('✅ 列表已清空');
          await loadExportList();
        } catch (error) {
          console.error('清空失败:', error);
          message.error('清空失败，请重试');
        }
      },
    });
  };

  // 初始化加载列表
  useEffect(() => {
    loadExportList();
  }, []);

  // 表格列定义
  const columns = [
    {
      title: '序号',
      key: 'index',
      width: 80,
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: '难度',
      dataIndex: 'difficulty_passed',
      key: 'difficulty_passed',
      width: 100,
      render: (passed: boolean | null) =>
        passed === null ? (
          <Tag color="default">未检测</Tag>
        ) : passed ? (
          <Tag icon={<CheckCircleOutlined />} color="success">
            通过
          </Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="error">
            未通过
          </Tag>
        ),
    },
    {
      title: '原创性',
      dataIndex: 'originality_passed',
      key: 'originality_passed',
      width: 100,
      render: (passed: boolean) =>
        passed ? (
          <Tag icon={<CheckCircleOutlined />} color="success">
            通过
          </Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="error">
            未通过
          </Tag>
        ),
    },
    {
      title: '严谨性',
      dataIndex: 'rigor_passed',
      key: 'rigor_passed',
      width: 100,
      render: (passed: boolean) =>
        passed ? (
          <Tag icon={<CheckCircleOutlined />} color="success">
            通过
          </Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="error">
            未通过
          </Tag>
        ),
    },
    {
      title: '综合结果',
      key: 'result',
      width: 100,
      render: (_: any, record: ExportListItem) => {
        const allPassed = record.originality_passed && record.rigor_passed;
        return allPassed ? (
          <Tag icon={<CheckCircleOutlined />} color="success">
            合格
          </Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="warning">
            不合格
          </Tag>
        );
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
  ];

  // 渲染检测按钮
  const renderCheckButton = (
    label: string,
    icon: React.ReactNode,
    check: CheckStatus,
    onCheck: () => void,
    onView: () => void
  ) => {
    return (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Button
          type={check.passed === true ? 'primary' : 'default'}
          danger={check.passed === false}
          icon={icon}
          loading={check.loading}
          onClick={onCheck}
          block
          size="large"
          style={{ height: 48 }}
        >
          {check.loading
            ? '检测中...'
            : check.passed === null
            ? label
            : check.passed
            ? `${label}通过`
            : `${label}未通过`}
        </Button>
        <Button
          icon={<EyeOutlined />}
          onClick={onView}
          disabled={!check.result}
          block
        >
          查看报告
        </Button>
      </Space>
    );
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 顶部标题 */}
      <Card style={{ marginBottom: 24 }}>
        <Title level={2}>
          <FileExcelOutlined /> 题目验证与导出
        </Title>
        <Paragraph type="secondary">
          填写题目信息 → 三重检测（难度+原创性+严谨性）→ 保存到列表 → 批量导出Excel
        </Paragraph>
      </Card>

      {/* 题目输入区 */}
      <Card title="题目信息" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical">
          <Form.Item
            label="题目内容"
            name="problem"
            rules={[{ required: true, message: '请输入题目内容' }]}
          >
            <TextArea
              rows={6}
              placeholder="请输入题目内容（支持LaTeX公式，如 $x^2$）"
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="标准答案"
                name="answer"
                rules={[{ required: true, message: '请输入标准答案' }]}
              >
                <Input placeholder="请输入标准答案" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="题目解析"
                name="explanation"
                rules={[{ required: true, message: '请输入题目解析' }]}
              >
                <Input placeholder="请输入题目解析" />
              </Form.Item>
            </Col>
          </Row>
        </Form>

        {/* 操作按钮 */}
        <Space style={{ marginTop: 16 }}>
          <Button icon={<EditOutlined />} onClick={handleModify}>
            修改题目
          </Button>
          <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>
            删除题目
          </Button>
        </Space>
      </Card>

      {/* 三重检测区 */}
      <Card title="三重检测" style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={8}>
            {renderCheckButton(
              '难度检测',
              <ExperimentOutlined />,
              difficultyCheck,
              handleCheckDifficulty,
              () => handleViewReport('difficulty')
            )}
          </Col>
          <Col span={8}>
            {renderCheckButton(
              '原创性检测',
              <SafetyCertificateOutlined />,
              originalityCheck,
              handleCheckOriginality,
              () => handleViewReport('originality')
            )}
          </Col>
          <Col span={8}>
            {renderCheckButton(
              '严谨性检测',
              <RadarChartOutlined />,
              rigorCheck,
              handleCheckRigor,
              () => handleViewReport('rigor')
            )}
          </Col>
        </Row>

        {/* 检测状态提示 */}
        {canSaveToList && (
          <Alert
            message="✅ 所有检测已完成！"
            description={`难度检测：${difficultyCheck.passed ? '通过' : '未通过'} | 原创性检测：${originalityCheck.passed ? '通过' : '未通过'} | 严谨性检测：${rigorCheck.passed ? '通过' : '未通过'} - 非最终采纳结果`}
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}

        {/* 保存按钮 */}
        <Divider />
        <Button
          type="primary"
          size="large"
          icon={<SaveOutlined />}
          onClick={handleSaveToList}
          disabled={!canSaveToList}
          block
          style={{ height: 56, fontSize: 16 }}
        >
          {canSaveToList ? '保存到导出列表' : '请完成所有检测后保存'}
        </Button>
      </Card>

      {/* 导出列表区 */}
      <Card title="导出列表" style={{ marginBottom: 24 }}>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={8}>
            <Statistic
              title="总题目数"
              value={exportStats.total}
              prefix={<FileExcelOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="通过质检"
              value={exportStats.passed}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="未通过"
              value={exportStats.failed}
              valueStyle={{ color: '#cf1322' }}
              prefix={<CloseCircleOutlined />}
            />
          </Col>
        </Row>

        <Space style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            loading={exporting}
            onClick={() => handleExport(true)}
            disabled={exportStats.passed === 0}
          >
            导出通过的题目
          </Button>
          <Button
            icon={<DownloadOutlined />}
            loading={exporting}
            onClick={() => handleExport(false)}
            disabled={exportStats.total === 0}
          >
            导出全部题目
          </Button>
          <Button icon={<SyncOutlined />} onClick={loadExportList}>
            刷新列表
          </Button>
          <Button
            danger
            icon={<DeleteOutlined />}
            onClick={handleClearList}
            disabled={exportStats.total === 0}
          >
            清空列表
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={exportList}
          rowKey="id"
          loading={loadingList}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* 查看报告Modal */}
      <Modal
        title={viewModalContent?.title}
        open={viewModalVisible}
        onCancel={() => setViewModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setViewModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={700}
      >
        {viewModalContent && (
          <div>
            {viewModalContent.title === '难度检测报告' && (
              <Descriptions bordered column={1}>
                <Descriptions.Item label="检测结果">
                  {viewModalContent.data.is_passed ? (
                    <Tag color="success">通过</Tag>
                  ) : (
                    <Tag color="error">未通过</Tag>
                  )}
                </Descriptions.Item>
                <Descriptions.Item label="正确次数">
                  {viewModalContent.data.correct_count || 0} /{' '}
                  {viewModalContent.data.total_attempts || viewModalContent.data.attempts || 8}
                </Descriptions.Item>
                <Descriptions.Item label="结论">
                  {viewModalContent.data.verdict || '未知'}
                </Descriptions.Item>
                {viewModalContent.data.recommendation && (
                  <Descriptions.Item label="建议">
                    {viewModalContent.data.recommendation}
                  </Descriptions.Item>
                )}
              </Descriptions>
            )}

            {viewModalContent.title === '原创性检测报告' && (
              <Descriptions bordered column={1}>
                <Descriptions.Item label="检测结果">
                  {viewModalContent.data.is_original ? (
                    <Tag color="success">原创</Tag>
                  ) : (
                    <Tag color="error">非原创</Tag>
                  )}
                </Descriptions.Item>
                {viewModalContent.data.originality_score && (
                  <Descriptions.Item label="原创性分数">
                    {viewModalContent.data.originality_score}
                  </Descriptions.Item>
                )}
                <Descriptions.Item label="结论">
                  {viewModalContent.data.verdict || '未知'}
                </Descriptions.Item>
                <Descriptions.Item label="AI评价">
                  <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
                    {viewModalContent.data.details || viewModalContent.data.reason || '无'}
                  </Paragraph>
                </Descriptions.Item>
              </Descriptions>
            )}

            {viewModalContent.title === '严谨性检测报告' && (
              <Descriptions bordered column={1}>
                <Descriptions.Item label="检测结果">
                  {viewModalContent.data.is_rigorous ? (
                    <Tag color="success">严谨</Tag>
                  ) : (
                    <Tag color="error">不严谨</Tag>
                  )}
                </Descriptions.Item>
                {viewModalContent.data.rigor_score && (
                  <Descriptions.Item label="严谨性分数">
                    {viewModalContent.data.rigor_score}
                  </Descriptions.Item>
                )}
                <Descriptions.Item label="结论">
                  {viewModalContent.data.verdict || '未知'}
                </Descriptions.Item>
                <Descriptions.Item label="AI评价">
                  <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
                    {viewModalContent.data.details || viewModalContent.data.reason || '无'}
                  </Paragraph>
                </Descriptions.Item>
              </Descriptions>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
