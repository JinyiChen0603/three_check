import { Spin } from 'antd';

export function Loading({ tip }: { tip?: string }) {
  return (
    <div style={{ textAlign: 'center', padding: '100px 0' }}>
      <Spin size="large" tip={tip} />
    </div>
  );
}


