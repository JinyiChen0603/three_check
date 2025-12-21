import { Card, Space, Typography } from 'antd';

import type { ReviewChoiceResponse } from '../types';

const { Text, Paragraph } = Typography;

export function ProblemDisplay({
  problemData,
  showSolution,
}: {
  problemData: ReviewChoiceResponse;
  showSolution: boolean;
}) {
  return (
    <Card title={problemData.problem_title || '题目信息'} style={{ marginBottom: 24 }}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Text strong>题目内容：</Text>
          <Paragraph style={{ marginTop: 8, fontSize: 16 }}>
            {typeof problemData.problem_content === 'string'
              ? problemData.problem_content
              : JSON.stringify(problemData.problem_content, null, 2)}
          </Paragraph>
        </div>

        {showSolution && problemData.problem_explanation && (
          <div>
            <Text strong>解题过程：</Text>
            <Paragraph style={{ marginTop: 8 }}>{problemData.problem_explanation}</Paragraph>
          </div>
        )}
      </Space>
    </Card>
  );
}


