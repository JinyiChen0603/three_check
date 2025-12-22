import { Alert, Button, Card, Divider, Input, Space, Typography, message } from 'antd';

import { BUSINESS_CONSTANTS } from '../../../config/constants';
import type { VariantItem } from '../types';
import type { ParentProblem } from '../hooks/useProblemTransform';
import { VariantTable } from './VariantTable';

const { Text } = Typography;
const { TextArea } = Input;

export function ProblemTransformStep({
  parentProblems,
  transformPrompts,
  variantsMap,
  variantCountMap,
  setPrompt,
  onGenerateVariant,
  onQualityCheck,
  onSubmitForReview,
  onDeleteVariant,
  onBack,
  onNext,
  canNext,
}: {
  parentProblems: ParentProblem[];
  transformPrompts: Record<number, string>;
  variantsMap: Record<number, VariantItem[]>;
  variantCountMap: Record<number, number>;
  setPrompt: (parentId: number, prompt: string) => void;
  onGenerateVariant: (parentId: number) => Promise<void>;
  onQualityCheck: (parentId: number, variant: VariantItem) => void;
  onSubmitForReview: (parentId: number, variant: VariantItem) => void;
  onDeleteVariant: (parentId: number, variantKey: string) => void;
  onBack: () => void;
  onNext: () => void;
  canNext: boolean;
}) {
  return (
    <Space orientation="vertical" style={{ width: '100%' }} size="large">
      {parentProblems.map((p, idx) => {
        const parentId = p.id;
        const promptValue = transformPrompts[parentId] || '';
        const variants = variantsMap[parentId] || [];
        const variantCount = variantCountMap[parentId] || 0;

        return (
          <Card
            key={parentId}
            type="inner"
            title={`母题 ${idx + 1}（ID: ${parentId}）`}
            style={{ borderColor: '#f0f0f0' }}
          >
            <Space orientation="vertical" style={{ width: '100%' }} size="middle">
              <Alert
                message="母题信息"
                description={
                  <div>
                    <p>
                      <strong>内容：</strong>
                      {p.source.content}
                    </p>
                    <p>
                      <strong>答案：</strong>
                      {p.source.answer}
                    </p>
                  </div>
                }
                type="success"
                showIcon
              />

              <Card size="small">
                <Space orientation="vertical" style={{ width: '100%' }}>
                  <Text strong>变形提示词：</Text>
                  <TextArea
                    value={promptValue}
                    onChange={(e) => setPrompt(parentId, e.target.value)}
                    placeholder="请输入如何变形这道题目的提示，例如：将题目中的数字改为其他值，或改变题目的表述方式..."
                    rows={3}
                  />
                  <Space>
                    <Button
                      type="primary"
                      onClick={async () => {
                        try {
                          await onGenerateVariant(parentId);
                          message.success('题目变形成功并已保存到数据库！');
                        } catch (error: any) {
                          if (error?.message === 'EMPTY_PROMPT') {
                            message.warning('请填写变形提示词');
                            return;
                          }
                          if (error?.message === 'MAX_VARIANTS_REACHED') {
                            message.warning(
                              `每个母题最多可以变形 ${BUSINESS_CONSTANTS.MAX_VARIANTS_PER_PROBLEM} 次`
                            );
                            return;
                          }
                          console.error('❌ [DEBUG] 题目变形失败:', error);
                          console.error('❌ [DEBUG] 错误详情:', {
                            message: error?.message,
                            response: error?.response?.data,
                            status: error?.response?.status,
                          });
                          message.error(
                            '题目变形失败: ' +
                              (error?.response?.data?.detail || error?.message || '未知错误')
                          );
                        }
                      }}
                      disabled={
                        !promptValue ||
                        variantCount >= BUSINESS_CONSTANTS.MAX_VARIANTS_PER_PROBLEM
                      }
                    >
                      生成变体
                    </Button>
                    <Text type="secondary">
                      已生成 {variantCount}/{BUSINESS_CONSTANTS.MAX_VARIANTS_PER_PROBLEM}
                    </Text>
                  </Space>
                </Space>
              </Card>

              {variants.length > 0 && (
                <>
                  <Divider>生成的变体</Divider>
                  <VariantTable
                    parentId={parentId}
                    variants={variants}
                    onQualityCheck={onQualityCheck}
                    onSubmitForReview={onSubmitForReview}
                    onDeleteVariant={onDeleteVariant}
                  />
                </>
              )}
            </Space>
          </Card>
        );
      })}

      <Space>
        <Button onClick={onBack}>返回上一步</Button>
        <Button type="primary" onClick={onNext} disabled={!canNext}>
          下一步：提交合格题目
        </Button>
      </Space>
    </Space>
  );
}



