#!/bin/bash

# ============================================
# MathTasks 一键部署脚本
# 用法：./deploy.sh [dev|prod]
# ============================================

set -e

ENV=${1:-dev}
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=================================================="
echo "   MathTasks 部署脚本 - $ENV 环境"
echo "=================================================="

# 检查环境变量文件
if [ ! -f ".env.$ENV" ]; then
    echo -e "${RED}❌ 未找到 .env.$ENV 文件${NC}"
    echo -e "${YELLOW}请先创建 .env.$ENV 文件（可参考 .env.$ENV.example）${NC}"
    exit 1
fi

# 复制环境变量
cp ".env.$ENV" .env
echo -e "${GREEN}✅ 已加载 $ENV 环境配置${NC}"

# 检查 Docker
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker 未运行${NC}"
    exit 1
fi

# 停止旧容器
echo -e "\n${YELLOW}停止旧容器...${NC}"
docker compose down

# 启动服务
echo -e "\n${YELLOW}启动服务...${NC}"
docker compose up -d --build

# 等待数据库
echo -e "\n${YELLOW}等待数据库启动...${NC}"
sleep 10

# 检查数据库
if docker compose exec -T postgres pg_isready -U mathtasks &> /dev/null; then
    echo -e "${GREEN}✅ 数据库已就绪${NC}"
else
    echo -e "${RED}❌ 数据库启动失败${NC}"
    docker compose logs postgres
    exit 1
fi

# 备份数据库
echo -e "\n${YELLOW}备份数据库...${NC}"
mkdir -p backups
BACKUP_FILE="backups/db_backup_$(date +%Y%m%d_%H%M%S).sql"
if docker compose exec -T postgres pg_dump -U mathtasks mathtasks > "$BACKUP_FILE" 2>/dev/null; then
    echo -e "${GREEN}✅ 数据库已备份到: $BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠️  数据库备份失败（可能是新部署，数据库为空）${NC}"
    rm -f "$BACKUP_FILE"
fi

# 初始化数据库
echo -e "\n${YELLOW}初始化数据库...${NC}"
docker compose exec -T api alembic upgrade head
docker compose exec -T api python scripts/init_users.py 2>/dev/null || true
docker compose exec -T api python scripts/init_materials.py 2>/dev/null || true

# 读取端口
source .env
echo -e "\n=================================================="
echo -e "${GREEN}🎉 部署完成！${NC}"
echo "=================================================="
echo -e "前端：   http://localhost:${FRONTEND_PORT:-5173}"
echo -e "后端：   http://localhost:${API_PORT:-8001}"
echo -e "API文档：http://localhost:${API_PORT:-8001}/docs"
echo "=================================================="
