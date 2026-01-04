/**
 * 变体生成器页面
 * 允许用户直接输入题目内容生成变体，不依赖数据库中的母题
 * 包含已保存变体的管理功能
 */

import { useEffect, useState } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Space,
  message,
  Divider,
  Typography,
  Row,
  Col,
  Slider,
  Switch,
  Alert,
  Collapse,
  Tag,
  Table,
  Modal,
  Popconfirm,
  Empty,
} from 'antd';
import {
  ThunderboltOutlined,
  CopyOutlined,
  DeleteOutlined,
  DownloadOutlined,
  FireOutlined,
  SaveOutlined,
  CheckCircleOutlined,
  EyeOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { variantApi, taskApi } from '../../api';
import MathRenderer from '../../components/MathRenderer';
import { useVariantStore, type VariantResult } from '../../store/useVariantStore';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface SavedVariant {
  id: number;
  content: string;
  answer: string;
  explanation: string;
  created_at: string;
}

export default function VariantGenerator() {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  
  // 使用全局store替代本地state
  const {
    variants,
    loading,
    batchLoading,
    temperature,
    batchMode,
    batchCount,
    originalProblem,
    addVariant,
    addVariants,
    removeVariant,
    clearVariants,
    setLoading,
    setBatchLoading,
    setTemperature,
    setBatchMode,
    setBatchCount,
    setOriginalProblem,
  } = useVariantStore();

  // 已保存的变体列表
  const [savedVariants, setSavedVariants] = useState<SavedVariant[]>([]);
  const [savedLoading, setSavedLoading] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewVariant, setPreviewVariant] = useState<SavedVariant | null>(null);

  // 加载已保存的变体列表
  const loadSavedVariants = async () => {
    setSavedLoading(true);
    try {
      const result = await variantApi.getMyVariants();
      setSavedVariants(result.variants);
    } catch (error: any) {
      console.error('加载已保存变体失败:', error);
    } finally {
      setSavedLoading(false);
    }
  };

  // 恢复表单数据（从全局store）
  useEffect(() => {
    if (originalProblem) {
      form.setFieldsValue(originalProblem);
    }
  }, [originalProblem, form]);

  // 加载已保存的变体
  useEffect(() => {
    loadSavedVariants();
  }, []);

  // 生成单个变体
  const handleGenerateVariant = async (values: any) => {
    if (!values.original_content || !values.original_explanation || !values.original_answer) {
      message.warning('请填写完整的题目、解析和答案');
      return;
    }

    // 保存原始题目数据
    setOriginalProblem({
      original_content: values.original_content,
      original_explanation: values.original_explanation,
      original_answer: values.original_answer,
      modification_requirement: values.modification_requirement,
    });

    setLoading(true);
    try {
      const result = await variantApi.generateVariantDirect({
        original_content: values.original_content,
        original_explanation: values.original_explanation,
        original_answer: values.original_answer,
        modification_requirement: values.modification_requirement,
        temperature,
      });

      if (result.success) {
        const newVariant: VariantResult = {
          variant_content: result.variant_content,
          variant_explanation: result.variant_explanation,
          variant_answer: result.variant_answer,
          timestamp: Date.now(),
        };
        addVariant(newVariant); // 使用store的方法，会自动显示通知
      } else {
        message.error(result.error || '生成失败');
      }
    } catch (error: any) {
      console.error('生成变体失败:', error);
      message.error(error.response?.data?.detail || '生成变体失败');
    } finally {
      setLoading(false);
    }
  };

  // 批量生成变体
  const handleBatchGenerate = async (values: any) => {
    if (!values.original_content || !values.original_explanation || !values.original_answer) {
      message.warning('请填写完整的题目、解析和答案');
      return;
    }

    // 保存原始题目数据
    setOriginalProblem({
      original_content: values.original_content,
      original_explanation: values.original_explanation,
      original_answer: values.original_answer,
      modification_requirement: values.modification_requirement,
    });

    setBatchLoading(true);
    try {
      const result = await variantApi.generateMultipleVariants({
        original_content: values.original_content,
        original_explanation: values.original_explanation,
        original_answer: values.original_answer,
        modification_requirement: values.modification_requirement,
        count: batchCount,
        temperature,
      });

      if (result.success) {
        const newVariants: VariantResult[] = result.variants
          .filter((v: any) => v.success)
          .map((v: any) => ({
            variant_content: v.variant_content,
            variant_explanation: v.variant_explanation,
            variant_answer: v.variant_answer,
            timestamp: Date.now() + Math.random(), // 确保唯一性
          }));
        
        addVariants(newVariants); // 使用store的方法，会自动显示通知
        
        if (result.count < result.total) {
          message.warning(`部分变体生成失败：${result.total - result.count} 个`);
        }
      } else {
        message.error(result.error || '批量生成失败');
      }
    } catch (error: any) {
      console.error('批量生成变体失败:', error);
      message.error(error.response?.data?.detail || '批量生成变体失败');
    } finally {
      setBatchLoading(false);
    }
  };

  // 复制变体内容
  const handleCopyVariant = (variant: VariantResult) => {
    const text = `题目：\n${variant.variant_content}\n\n解析：\n${variant.variant_explanation}\n\n答案：\n${variant.variant_answer}`;
    navigator.clipboard.writeText(text).then(() => {
      message.success('已复制到剪贴板');
    });
  };

  // 删除变体
  const handleDeleteVariant = (timestamp: number) => {
    removeVariant(timestamp);
    message.success('已删除');
  };

  // 清空所有变体
  const handleClearAll = () => {
    clearVariants();
    message.success('已清空所有变体');
  };

  // 导出所有变体
  const handleExportAll = () => {
    if (variants.length === 0) {
      message.warning('没有变体可导出');
      return;
    }

    const text = variants.map((v, index) => {
      return `========== 变体 ${index + 1} ==========\n\n题目：\n${v.variant_content}\n\n解析：\n${v.variant_explanation}\n\n答案：\n${v.variant_answer}\n\n`;
    }).join('\n');

    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `变体集合_${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    message.success('导出成功');
  };

  // 保存单个变体到数据库
  const handleSaveVariant = async (variant: VariantResult) => {
    try {
      await variantApi.saveDraft({
        content: variant.variant_content,
        explanation: variant.variant_explanation,
        answer: variant.variant_answer,
      });
      message.success('保存成功！');
      loadSavedVariants(); // 刷新已保存列表
    } catch (error: any) {
      console.error('保存变体失败:', error);
      message.error(error.response?.data?.detail || '保存失败');
    }
  };

  // 批量保存所有变体
  const handleSaveAll = async () => {
    if (variants.length === 0) {
      message.warning('没有变体可保存');
      return;
    }

    try {
      const problems = variants.map(v => ({
        content: v.variant_content,
        explanation: v.variant_explanation,
        answer: v.variant_answer,
      }));

      const result = await variantApi.saveBatch(problems);
      message.success(`成功保存 ${result.count} 个变体！`);
      
      // 保存成功后清空并刷新已保存列表
      if (result.count === variants.length) {
        clearVariants();
      }
      loadSavedVariants(); // 刷新已保存列表
    } catch (error: any) {
      console.error('批量保存失败:', error);
      message.error(error.response?.data?.detail || '批量保存失败');
    }
  };

  // 预览已保存的变体
  const handlePreviewSaved = (variant: SavedVariant) => {
    setPreviewVariant(variant);
    setPreviewVisible(true);
  };

  // 删除已保存的变体
  const handleDeleteSaved = async (id: number) => {
    try {
      await variantApi.deleteVariant(id);
      message.success('删除成功');
      loadSavedVariants(); // 刷新列表
    } catch (error: any) {
      console.error('删除失败:', error);
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  // 检验变体（推入验证队列）
  const handleValidateSaved = async (variant: SavedVariant) => {
    try {
      // 1. 检查是否有进行中的出题任务
      const myTasks = await taskApi.getMyTasks();
      const createTask = myTasks.batches?.find(
        (batch: any) => batch.task_type === 'create_problem' && batch.status === 'in_progress'
      );

      if (!createTask) {
        Modal.warning({
          title: '无可用任务',
          content: '您需要先领取一个出题任务才能进行检验。是否前往任务管理页面？',
          okText: '前往领取',
          cancelText: '取消',
          onOk: () => {
            navigate('/tasks');
          },
        });
        return;
      }

      // 2. 关联到任务并跳转到验证页面
      const result = await variantApi.prepareValidate(variant.id);
      
      if (result.success) {
        message.success('已进入验证队列');
        // 跳转到题目验证导出页面，并传递题目ID
        navigate('/totalpage', { 
          state: { 
            variantId: variant.id,
            autoFill: true 
          } 
        });
      }
    } catch (error: any) {
      console.error('检验失败:', error);
      message.error(error.response?.data?.detail || '检验失败');
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <FireOutlined /> 变体生成（使用过程请勿刷新）
      </Title>
      <Paragraph type="secondary">
        直接输入题目内容即可生成变体。支持单个生成和批量生成。
        <Text type="success" style={{ marginLeft: '8px' }}>
          ✨ 现在可以在生成过程中切换页面，完成时会收到通知！
        </Text>
      </Paragraph>

      <Row gutter={24}>
        {/* 左侧：输入表单 */}
        <Col xs={24} lg={12}>
          <Card title="原始题目输入" bordered={false}>
            <Form
              form={form}
              layout="vertical"
              onFinish={batchMode ? handleBatchGenerate : handleGenerateVariant}
            >
              <Form.Item
                label="题目内容"
                name="original_content"
                rules={[{ required: true, message: '请输入题目内容' }]}
              >
                <TextArea
                  rows={6}
                  placeholder="输入完整的题目内容，支持 LaTeX 公式（$...$）"
                />
              </Form.Item>

              <Form.Item
                label="解析内容"
                name="original_explanation"
                rules={[{ required: true, message: '请输入解析内容' }]}
              >
                <TextArea
                  rows={6}
                  placeholder="输入详细的解题步骤和分析"
                />
              </Form.Item>

              <Form.Item
                label="答案"
                name="original_answer"
                rules={[{ required: true, message: '请输入答案' }]}
              >
                <TextArea
                  rows={3}
                  placeholder="输入最终答案"
                />
              </Form.Item>

              <Form.Item
                label="修改要求（可选）"
                name="modification_requirement"
                tooltip="留空则使用默认规则：保持难度，改变数值、场景或条件"
              >
                <TextArea
                  rows={3}
                  placeholder="例如：将场景改为物理问题、难度提升一级、改用三角函数求解等"
                />
              </Form.Item>

              <Form.Item label="创造性">
                <Slider
                  min={0.3}
                  max={2.0}
                  step={0.1}
                  value={temperature}
                  onChange={setTemperature}
                  marks={{
                    0.3: '保守',
                    1.0: '中等',
                    1.5: '推荐',
                    2.0: '激进',
                  }}
                />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  当前值: {temperature} - 值越高，变体创造性越强
                </Text>
              </Form.Item>

              <Divider />

              <Space direction="vertical" style={{ width: '100%' }}>
                <Space>
                  <Text>批量生成模式：</Text>
                  <Switch checked={batchMode} onChange={setBatchMode} />
                  {batchMode && (
                    <>
                      <Text>数量：</Text>
                      <Slider
                        style={{ width: 120 }}
                        min={2}
                        max={10}
                        value={batchCount}
                        onChange={setBatchCount}
                      />
                      <Text>{batchCount} 个</Text>
                    </>
                  )}
                </Space>

                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<ThunderboltOutlined />}
                  loading={loading || batchLoading}
                  size="large"
                  block
                >
                  {batchMode
                    ? `批量生成 ${batchCount} 个变体`
                    : '生成变体'}
                </Button>
              </Space>
            </Form>
          </Card>
        </Col>

        {/* 右侧：变体结果展示 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <span>生成的变体</span>
                <Tag color="blue">{variants.length} 个</Tag>
              </Space>
            }
            bordered={false}
            extra={
              <Space>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={handleSaveAll}
                  disabled={variants.length === 0}
                >
                  保存全部
                </Button>
                <Button
                  icon={<DownloadOutlined />}
                  onClick={handleExportAll}
                  disabled={variants.length === 0}
                >
                  导出全部
                </Button>
                <Button
                  icon={<DeleteOutlined />}
                  danger
                  onClick={handleClearAll}
                  disabled={variants.length === 0}
                >
                  清空
                </Button>
              </Space>
            }
          >
            {variants.length === 0 ? (
              <Alert
                message="还没有生成变体"
                description="填写左侧表单后点击生成按钮即可开始"
                type="info"
                showIcon
              />
            ) : (
              <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
                <Collapse accordion>
                  {variants.map((variant, index) => (
                    <Panel
                      header={`变体 ${index + 1}`}
                      key={variant.timestamp}
                      extra={
                        <Space onClick={e => e.stopPropagation()}>
                          <Button
                            type="primary"
                            size="small"
                            icon={<SaveOutlined />}
                            onClick={() => handleSaveVariant(variant)}
                          >
                            保存
                          </Button>
                          <Button
                            type="text"
                            size="small"
                            icon={<CopyOutlined />}
                            onClick={() => handleCopyVariant(variant)}
                          >
                            复制
                          </Button>
                          <Button
                            type="text"
                            size="small"
                            danger
                            icon={<DeleteOutlined />}
                            onClick={() => handleDeleteVariant(variant.timestamp)}
                          >
                            删除
                          </Button>
                        </Space>
                      }
                    >
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <div>
                          <Text strong>题目：</Text>
                          <div style={{ 
                            padding: '12px', 
                            background: '#f5f5f5', 
                            borderRadius: '4px',
                            marginTop: '8px',
                          }}>
                            <MathRenderer content={variant.variant_content} />
                          </div>
                        </div>

                        <div>
                          <Text strong>解析：</Text>
                          <div style={{ 
                            padding: '12px', 
                            background: '#f5f5f5', 
                            borderRadius: '4px',
                            marginTop: '8px',
                          }}>
                            <MathRenderer content={variant.variant_explanation} />
                          </div>
                        </div>

                        <div>
                          <Text strong>答案：</Text>
                          <div style={{ 
                            padding: '12px', 
                            background: '#e6f7ff', 
                            borderRadius: '4px',
                            marginTop: '8px',
                          }}>
                            <MathRenderer content={variant.variant_answer} />
                          </div>
                        </div>
                      </Space>
                    </Panel>
                  ))}
                </Collapse>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 已保存的变体列表 */}
      <Card
        title={
          <Space>
            <ExclamationCircleOutlined />
            <span>已保存的变体</span>
            <Tag color="blue">{savedVariants.length} 个</Tag>
          </Space>
        }
        style={{ marginTop: 24 }}
      >
        <Table
          columns={[
            {
              title: '序号',
              key: 'index',
              width: 80,
              render: (_: any, __: any, index: number) => index + 1,
            },
            {
              title: '题目内容（预览）',
              dataIndex: 'content',
              key: 'content',
              ellipsis: true,
              render: (text: string) => {
                // 性能优化：表格中显示纯文本，不渲染LaTeX（避免大量MathRenderer导致卡顿）
                const preview = text.substring(0, 100) + (text.length > 100 ? '...' : '');
                return (
                  <div style={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {preview}
                  </div>
                );
              },
            },
            {
              title: '创建时间',
              dataIndex: 'created_at',
              key: 'created_at',
              width: 180,
              render: (text: string) => new Date(text).toLocaleString('zh-CN'),
            },
            {
              title: '状态',
              key: 'status',
              width: 100,
              render: () => <Tag color="orange">草稿</Tag>,
            },
            {
              title: '操作',
              key: 'action',
              width: 280,
              render: (_: any, record: SavedVariant) => (
                <Space>
                  <Button
                    type="primary"
                    size="small"
                    icon={<CheckCircleOutlined />}
                    onClick={() => handleValidateSaved(record)}
                  >
                    检验
                  </Button>
                  <Button
                    size="small"
                    icon={<EyeOutlined />}
                    onClick={() => handlePreviewSaved(record)}
                  >
                    预览
                  </Button>
                  <Popconfirm
                    title="确定删除这个变体吗？"
                    onConfirm={() => handleDeleteSaved(record.id)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                    >
                      删除
                    </Button>
                  </Popconfirm>
                </Space>
              ),
            },
          ]}
          dataSource={savedVariants}
          rowKey="id"
          loading={savedLoading}
          locale={{
            emptyText: (
              <Empty
                description="还没有保存的变体"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ),
          }}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 个变体草稿`,
          }}
        />
      </Card>

      {/* 预览弹窗 */}
      <Modal
        title="变体详情预览"
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            关闭
          </Button>,
          <Button
            key="validate"
            type="primary"
            icon={<CheckCircleOutlined />}
            onClick={() => {
              setPreviewVisible(false);
              if (previewVariant) {
                handleValidateSaved(previewVariant);
              }
            }}
          >
            检验此题
          </Button>,
        ]}
        width={800}
      >
        {previewVariant && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <Text strong style={{ fontSize: 16 }}>题目内容：</Text>
              <div
                style={{
                  padding: '16px',
                  background: '#f5f5f5',
                  borderRadius: '4px',
                  marginTop: '8px',
                }}
              >
                <MathRenderer content={previewVariant.content} />
              </div>
            </div>

            <div>
              <Text strong style={{ fontSize: 16 }}>解析：</Text>
              <div
                style={{
                  padding: '16px',
                  background: '#f5f5f5',
                  borderRadius: '4px',
                  marginTop: '8px',
                }}
              >
                <MathRenderer content={previewVariant.explanation} />
              </div>
            </div>

            <div>
              <Text strong style={{ fontSize: 16 }}>答案：</Text>
              <div
                style={{
                  padding: '16px',
                  background: '#e6f7ff',
                  borderRadius: '4px',
                  marginTop: '8px',
                }}
              >
                <MathRenderer content={previewVariant.answer} />
              </div>
            </div>
          </Space>
        )}
      </Modal>
    </div>
  );
}

