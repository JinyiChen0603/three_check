import { Card, Space, Typography } from 'antd';

import type { ReviewChoiceResponse } from '../types';
import MathRenderer from '../../../components/MathRenderer';

const { Text } = Typography;

export function ProblemDisplay({
  problemData,
  showSolution,
}: {
  problemData: ReviewChoiceResponse;
  showSolution: boolean;
}) {
  return (
    <Card title={problemData.problem_title || '题目信息'} style={{ marginBottom: 24 }}>
      <Space orientation="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Text strong>题目内容：</Text>
          <MathRenderer 
            content={typeof problemData.problem_content === 'string'
              ? problemData.problem_content
              : JSON.stringify(problemData.problem_content, null, 2)}
            style={{ marginTop: 8, fontSize: 16 }}
          />
        </div>

        {showSolution && problemData.problem_explanation && (
          <div>
            <Text strong>解题过程：</Text>
            <MathRenderer 
              content={problemData.problem_explanation}
              style={{ marginTop: 8 }}
            />
          </div>
        )}
      </Space>
    </Card>
  );
}


