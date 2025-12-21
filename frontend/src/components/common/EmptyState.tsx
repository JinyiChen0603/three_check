import { Button, Empty } from 'antd';

export function EmptyState({
  description,
  actionText,
  onAction,
}: {
  description: string;
  actionText?: string;
  onAction?: () => void;
}) {
  return (
    <Empty description={description} image={Empty.PRESENTED_IMAGE_SIMPLE}>
      {actionText && onAction && (
        <Button type="primary" onClick={onAction}>
          {actionText}
        </Button>
      )}
    </Empty>
  );
}


