import { Button, Modal, Space, Table, Tag, Tooltip, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { SyncOutlined } from '@ant-design/icons';

import type { VariantItem } from '../types';
import MathRenderer from '../../../components/MathRenderer';

const { Text } = Typography;

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
      title: '题目内容（鼠标悬停预览全部内容）',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (_: any, record: VariantItem) => {
        const content = record.content;
        const text = typeof content === 'string' 
          ? content 
          : (content as any)?.text ?? String(content ?? '');
        return (
          <Tooltip 
            title={<MathRenderer content={text} style={{ maxWidth: 400, maxHeight: 300, overflow: 'auto' }} />} 
            placement="topLeft"
            overlayStyle={{ maxWidth: 450 }}
          >
            <span>{text.slice(0, 50)}{text.length > 50 ? '...' : ''}</span>
          </Tooltip>
        );
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
        
        if (record.quality_check) {
          const qc = record.quality_check;
          return (
            <Space orientation="vertical" size="small">
              <Tag color={qc.all_passed ? 'success' : 'error'}>
                {qc.all_passed ? '全部通过' : '未完全通过'}
              </Tag>
              <Space size="small">
                <Tag color={qc.difficulty?.is_passed ? 'blue' : 'default'}>
                  难度{qc.difficulty?.is_passed ? '✓' : '✗'}
                </Tag>
                <Tag color={qc.originality?.is_original ? 'green' : 'default'}>
                  原创{qc.originality?.is_original ? '✓' : '✗'}
                </Tag>
                <Tag color={qc.rigor?.is_rigorous ? 'purple' : 'default'}>
                  严谨{qc.rigor?.is_rigorous ? '✓' : '✗'}
                </Tag>
              </Space>
              {qc.difficulty?.correct_count !== undefined && (
                <Text type="secondary" style={{ fontSize: '11px' }}>
                  难度测试: {qc.difficulty.correct_count}/{qc.difficulty.attempts || qc.difficulty.total_attempts || 8}次正确
                </Text>
              )}
            </Space>
          );
        }
        
        if (record.qualityCheckStatus === 'failed') {
          return <Tag color="error">检查失败</Tag>;
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
                    <div style={{ marginBottom: '20px' }}>
                      <p>
                        <strong>内容：</strong>
                      </p>
                      <MathRenderer 
                        content={typeof record.content === 'string'
                          ? record.content
                          : (record.content as any)?.text ?? String(record.content ?? '')}
                        style={{ marginLeft: '20px', marginTop: '8px' }}
                      />
                    </div>
                    
                    <div style={{ marginBottom: '20px' }}>
                      <p>
                        <strong>答案：</strong>
                      </p>
                      <MathRenderer 
                        content={record.answer || ''}
                        style={{ marginLeft: '20px', marginTop: '8px' }}
                      />
                    </div>
                    
                    {record.explanation && (
                      <div style={{ marginBottom: '20px' }}>
                        <p>
                          <strong>解析：</strong>
                        </p>
                        <MathRenderer 
                          content={record.explanation}
                          style={{ marginLeft: '20px', marginTop: '8px' }}
                        />
                      </div>
                    )}
                    
                    {/* 质检详情 */}
                    {record.quality_check && (
                      <div style={{ marginTop: '30px', paddingTop: '20px', borderTop: '2px solid #f0f0f0' }}>
                        <h4 style={{ marginBottom: '16px' }}>质检结果详情</h4>
                        
                        {/* 总体状态 */}
                        <div style={{ marginBottom: '16px' }}>
                          <Tag color={record.quality_check.all_passed ? 'success' : 'error'} style={{ fontSize: '14px' }}>
                            {record.quality_check.all_passed ? '✅ 全部通过' : '❌ 未完全通过'}
                          </Tag>
                        </div>
                        
                        {/* 难度检测 */}
                        {record.quality_check.difficulty && (
                          <div style={{ marginBottom: '16px', padding: '12px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                            <div style={{ marginBottom: '8px' }}>
                              <strong>难度检测：</strong>
                              <Tag color={record.quality_check.difficulty.is_passed ? 'blue' : 'orange'} style={{ marginLeft: '8px' }}>
                                {record.quality_check.difficulty.is_passed ? '通过' : '未通过'}
                              </Tag>
                            </div>
                            <div style={{ fontSize: '13px', color: '#666', marginLeft: '20px' }}>
                              <div>测试结果：{record.quality_check.difficulty.correct_count}/{record.quality_check.difficulty.attempts || record.quality_check.difficulty.total_attempts || 8}次正确</div>
                              {record.quality_check.difficulty.verdict && (
                                <div style={{ marginTop: '4px' }}>判定：{record.quality_check.difficulty.verdict}</div>
                              )}
                            </div>
                          </div>
                        )}
                        
                        {/* 原创性检测 */}
                        {record.quality_check.originality && (
                          <div style={{ marginBottom: '16px', padding: '12px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                            <div style={{ marginBottom: '8px' }}>
                              <strong>原创性检测：</strong>
                              <Tag color={record.quality_check.originality.is_original ? 'green' : 'orange'} style={{ marginLeft: '8px' }}>
                                {record.quality_check.originality.is_original ? '通过' : '未通过'}
                              </Tag>
                            </div>
                            <div style={{ fontSize: '13px', color: '#666', marginLeft: '20px' }}>
                              {record.quality_check.originality.verdict && (
                                <div>判定：{record.quality_check.originality.verdict}</div>
                              )}
                              {record.quality_check.originality.details && (
                                <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#fff', borderLeft: '3px solid #52c41a', whiteSpace: 'pre-wrap' }}>
                                  {record.quality_check.originality.details}
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                        
                        {/* 严谨性检测 */}
                        {record.quality_check.rigor && (
                          <div style={{ marginBottom: '16px', padding: '12px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                            <div style={{ marginBottom: '8px' }}>
                              <strong>严谨性检测：</strong>
                              <Tag color={record.quality_check.rigor.is_rigorous ? 'purple' : 'orange'} style={{ marginLeft: '8px' }}>
                                {record.quality_check.rigor.is_rigorous ? '通过' : '未通过'}
                              </Tag>
                            </div>
                            <div style={{ fontSize: '13px', color: '#666', marginLeft: '20px' }}>
                              {record.quality_check.rigor.verdict && (
                                <div>判定：{record.quality_check.rigor.verdict}</div>
                              )}
                              {record.quality_check.rigor.details && (
                                <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#fff', borderLeft: '3px solid #722ed1', whiteSpace: 'pre-wrap' }}>
                                  {record.quality_check.rigor.details}
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                        
                        {/* 提前终止提示 */}
                        {record.quality_check.early_stop && record.quality_check.early_stop_reason && (
                          <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#fff7e6', border: '1px solid #ffd591', borderRadius: '4px' }}>
                            <Text type="warning">
                              ⚠️ 提前终止：{record.quality_check.early_stop_reason}（未执行难度检测）
                            </Text>
                          </div>
                        )}
                      </div>
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



