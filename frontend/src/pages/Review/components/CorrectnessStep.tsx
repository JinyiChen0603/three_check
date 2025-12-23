import { Alert, Button, Card, Radio, Space } from 'antd';

import type { ReviewChoiceResponse } from '../types';
import MathRenderer from '../../../components/MathRenderer';

export function CorrectnessStep({
  problemData,
  options,
  userChoiceIndex,
  onChangeChoice,
  onSubmit,
  submitting,
}: {
  problemData: ReviewChoiceResponse;
  options: string[];
  userChoiceIndex: number | null;
  onChangeChoice: (idx: number) => void;
  onSubmit: () => void;
  submitting: boolean;
}) {
  return (
    <Card title="步骤1：正确性验证">
      <Space orientation="vertical" style={{ width: '100%' }} size="large">
        <Alert
          title="请选择正确答案"
          description={problemData.instruction || '从以下选项中选择您认为正确的答案。'}
          type="info"
          showIcon
        />

        <Radio.Group
          value={userChoiceIndex}
          onChange={(e) => onChangeChoice(e.target.value)}
          style={{ width: '100%' }}
        >
          <Space orientation="vertical" style={{ width: '100%' }}>
            {options.map((option, index) => (
              <Radio
                key={index}
                value={index}
                style={{
                  fontSize: 16,
                  padding: '12px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '4px',
                  width: '100%',
                }}
              >
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                  选项 {String.fromCharCode(65 + index)}: 
                  <MathRenderer content={option} style={{ display: 'inline' }} />
                </span>
              </Radio>
            ))}
          </Space>
        </Radio.Group>

        <Button type="primary" onClick={onSubmit} loading={submitting}>
          提交答案
        </Button>
      </Space>
    </Card>
  );
}


