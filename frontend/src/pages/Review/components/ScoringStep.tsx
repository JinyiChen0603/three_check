import { Alert, Button, Card, Input, InputNumber, Radio, Space, Typography } from 'antd';
import { StarOutlined } from '@ant-design/icons';

const { Text } = Typography;
const { TextArea } = Input;

export function ScoringStep({
  isCorrect,
  innovationScore,
  setInnovationScore,
  rigorScore,
  setRigorScore,
  isVeto,
  setIsVeto,
  vetoReason,
  setVetoReason,
  onSubmit,
  onSkip,
  submitting,
}: {
  isCorrect: boolean | null;
  innovationScore: number;
  setInnovationScore: (v: number) => void;
  rigorScore: number;
  setRigorScore: (v: number) => void;
  isVeto: boolean;
  setIsVeto: (v: boolean) => void;
  vetoReason: string;
  setVetoReason: (v: string) => void;
  onSubmit: () => void;
  onSkip: () => void;
  submitting: boolean;
}) {
  return (
    <Card title="步骤2：质量评分">
      <Space orientation="vertical" style={{ width: '100%' }} size="large">
        {isCorrect === false && (
          <Alert
            title="答案不正确"
            description="请参考解析，必要时可一票否决或给出较低评分。"
            type="warning"
            showIcon
          />
        )}

        <div>
          <Text strong>创新性评分：</Text>
          <div style={{ marginTop: 12 }}>
            <InputNumber
              min={0}
              max={10}
              value={innovationScore}
              onChange={(value) => setInnovationScore(value || 0)}
              style={{ width: 200 }}
            />
            <Text type="secondary" style={{ marginLeft: 12 }}>
              分（0-10）
            </Text>
          </div>
        </div>

        <div>
          <Text strong>数学严谨性评分：</Text>
          <div style={{ marginTop: 12 }}>
            <InputNumber
              min={0}
              max={10}
              value={rigorScore}
              onChange={(value) => setRigorScore(value || 0)}
              style={{ width: 200 }}
            />
            <Text type="secondary" style={{ marginLeft: 12 }}>
              分（0-10）
            </Text>
          </div>
        </div>

        <div>
          <Text strong>一票否决：</Text>
          <Radio.Group value={isVeto} onChange={(e) => setIsVeto(e.target.value)}>
            <Radio value={false}>否</Radio>
            <Radio value={true}>是</Radio>
          </Radio.Group>
          {isVeto && (
            <TextArea
              value={vetoReason}
              onChange={(e) => setVetoReason(e.target.value)}
              placeholder="请输入否决理由"
              rows={3}
              style={{ marginTop: 8 }}
            />
          )}
        </div>

        <Space>
          <Button type="primary" icon={<StarOutlined />} onClick={onSubmit} loading={submitting}>
            提交评分
          </Button>
          <Button onClick={onSkip}>跳过/下一题</Button>
        </Space>
      </Space>
    </Card>
  );
}


