import { Alert, Button, Space, Upload } from 'antd';
import { PlusOutlined, UploadOutlined } from '@ant-design/icons';

import { BUSINESS_CONSTANTS } from '../../../config/constants';
import type { ProblemItem } from '../types';
import { ProblemTable } from './ProblemTable';

export function ProblemValidationStep({
  problems,
  ocrLoading,
  onAddProblem,
  onOCR,
  onValidateBatch,
  onBatchUse,
  onProblemChange,
  onValidateSingle,
  onUseSingle,
  onRemove,
}: {
  problems: ProblemItem[];
  ocrLoading: boolean;
  onAddProblem: () => void;
  onOCR: (file: File) => Promise<boolean>;
  onValidateBatch: () => void;
  onBatchUse: () => void;
  onProblemChange: (key: string, field: keyof ProblemItem, value: string) => void;
  onValidateSingle: (problem: ProblemItem) => void;
  onUseSingle: (problem: ProblemItem) => void;
  onRemove: (key: string) => void;
}) {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Alert
        message="准备母题"
        description={
          <div>
            <p>您可以：</p>
            <ul style={{ paddingLeft: 20 }}>
              <li>手动输入题目和答案</li>
              <li>使用OCR识别图片中的题目</li>
              <li>从资料库下载题目后输入</li>
            </ul>
            <p style={{ marginTop: 8, color: '#ff4d4f' }}>
              ⚠️ 注意：只需要有明确答案的解答题，不要证明题、判断题或选择题
            </p>
          </div>
        }
        type="info"
        showIcon
      />

      <Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={onAddProblem}>
          添加题目
        </Button>
        <Upload beforeUpload={onOCR} showUploadList={false} accept="image/*">
          <Button icon={<UploadOutlined />} loading={ocrLoading}>
            OCR识别图片
          </Button>
        </Upload>
        <Button onClick={onValidateBatch} disabled={problems.length === 0}>
          批量验证
        </Button>
        <Button onClick={onBatchUse} disabled={problems.filter((p) => p.validationStatus === 'passed').length === 0}>
          批量使用
        </Button>
      </Space>

      <ProblemTable
        problems={problems}
        onProblemChange={onProblemChange}
        onValidateSingle={onValidateSingle}
        onUseSingle={onUseSingle}
        onRemove={onRemove}
      />

      {problems.length > 0 && (
        <Alert
          message="验证说明"
          description={`系统会使用AI模型测试${BUSINESS_CONSTANTS.VALIDATION_ATTEMPTS}次，如果正确次数不超过${BUSINESS_CONSTANTS.VALIDATION_THRESHOLD}次，则认为题目难度合适。`}
          type="info"
          showIcon
        />
      )}
    </Space>
  );
}



