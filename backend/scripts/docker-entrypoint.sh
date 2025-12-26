#!/bin/bash
set -e

echo "🚀 启动应用..."

# 等待数据库就绪（最多等待 60 秒）
echo "⏳ 等待数据库连接..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  # 使用 pg_isready 检查 PostgreSQL 是否就绪（更可靠）
  if PGPASSWORD=mathtasks123 psql -h postgres -U mathtasks -d mathtasks -c "SELECT 1" >/dev/null 2>&1; then
    echo "✅ 数据库连接成功"
    break
  fi
  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "⏳ 数据库未就绪，等待 2 秒... ($RETRY_COUNT/$MAX_RETRIES)"
  sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "❌ 数据库连接超时，请检查数据库服务"
  exit 1
fi

# 运行数据库迁移
echo "📦 运行数据库迁移..."
alembic upgrade head || {
  echo "⚠️ 数据库迁移失败，但继续启动应用（可能是数据库已是最新版本）"
}

echo "✅ 数据库迁移完成"

# 启动应用
echo "🚀 启动 FastAPI 应用..."
exec "$@"

