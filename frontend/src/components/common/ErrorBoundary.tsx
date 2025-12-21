import type { ReactNode } from 'react';
import { Component } from 'react';
import { Alert, Button, Space } from 'antd';

type Props = {
  children: ReactNode;
  title?: string;
};

type State = {
  hasError: boolean;
  error?: unknown;
};

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: unknown): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: unknown) {
    // 保持最小实现：只打日志，避免影响业务
    // eslint-disable-next-line no-console
    console.error('[ErrorBoundary] uncaught error', error);
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <div style={{ padding: 24 }}>
        <Alert
          type="error"
          showIcon
          message={this.props.title || '页面发生错误'}
          description="请刷新页面重试；如果持续出现，请联系管理员。"
        />
        <Space style={{ marginTop: 16 }}>
          <Button onClick={() => window.location.reload()}>刷新页面</Button>
          <Button
            type="link"
            onClick={() => this.setState({ hasError: false, error: undefined })}
          >
            尝试继续
          </Button>
        </Space>
      </div>
    );
  }
}


