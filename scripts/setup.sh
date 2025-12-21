#!/bin/bash

# =============================================================================
# MathTasks 项目初始化脚本
# =============================================================================
# 用途：首次克隆项目后，运行此脚本进行初始化配置
# 使用方法：chmod +x scripts/setup.sh && ./scripts/setup.sh
# =============================================================================

set -e  # 遇到错误立即退出

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=========================================="
echo "🚀 MathTasks 项目初始化"
echo "=========================================="
echo ""

# =============================================================================
# 1. 检查依赖
# =============================================================================
echo "📋 步骤 1/6: 检查系统依赖..."
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 未安装 Docker"
    echo "请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
else
    echo "✅ Docker 已安装"
fi

# 检查 Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo "❌ 未安装 Docker Compose"
    echo "请确保 Docker Desktop 已更新到最新版本"
    exit 1
else
    echo "✅ Docker Compose 已安装"
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 未安装 Node.js"
    echo "请先安装 Node.js (推荐版本 18+): https://nodejs.org/"
    exit 1
else
    NODE_VERSION=$(node -v)
    echo "✅ Node.js 已安装 ($NODE_VERSION)"
fi

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "❌ 未安装 npm"
    exit 1
else
    NPM_VERSION=$(npm -v)
    echo "✅ npm 已安装 ($NPM_VERSION)"
fi

echo ""

# =============================================================================
# 2. 配置后端环境变量
# =============================================================================
echo "=========================================="
echo "📝 步骤 2/6: 配置后端环境变量"
echo "=========================================="
echo ""

if [ ! -f "$ROOT_DIR/backend/.env" ]; then
    echo "⚠️  未找到 backend/.env 文件"
    
    if [ -f "$ROOT_DIR/backend/.env.example" ]; then
        echo "📄 从 .env.example 复制..."
        cp "$ROOT_DIR/backend/.env.example" "$ROOT_DIR/backend/.env"
        echo "✅ 已创建 backend/.env"
        echo ""
        echo "⚠️  重要提示："
        echo "   请编辑 backend/.env 文件，填入正确的 API 密钥："
        echo "   - OPENROUTER_API_KEY (GPT-4o)"
        echo "   - CANOPY_WAVE_API_KEY (DeepSeek Math-V2)"
        echo "   - DOUBAO_API_KEY (Doubao Seed Thinking)"
        echo ""
        read -p "按 Enter 继续..."
    else
        echo "❌ 未找到 backend/.env.example"
        echo "请联系项目管理员获取环境变量配置"
        exit 1
    fi
else
    echo "✅ backend/.env 已存在"
fi

echo ""

# =============================================================================
# 3. 安装前端依赖
# =============================================================================
echo "=========================================="
echo "📦 步骤 3/6: 安装前端依赖"
echo "=========================================="
echo ""

cd "$ROOT_DIR/frontend"

if [ ! -d "node_modules" ]; then
    echo "正在安装前端依赖（可能需要几分钟）..."
    npm install
    echo "✅ 前端依赖安装完成"
else
    echo "✅ 前端依赖已安装"
    echo "提示：如果遇到问题，可运行 'npm install' 重新安装"
fi

cd "$ROOT_DIR"

echo ""

# =============================================================================
# 4. 启动 Docker 容器
# =============================================================================
echo "=========================================="
echo "🐳 步骤 4/6: 启动 Docker 容器"
echo "=========================================="
echo ""

# 检查 Docker Desktop 是否运行
if ! docker info &> /dev/null; then
    echo "❌ Docker Desktop 未运行"
    echo "请启动 Docker Desktop 应用，然后重新运行此脚本"
    exit 1
fi

cd "$ROOT_DIR/backend"

echo "正在启动数据库和后端服务..."
docker compose up -d

echo ""
echo "等待服务启动（约15秒）..."
sleep 15

# 检查容器状态
echo ""
echo "容器状态："
docker compose ps

cd "$ROOT_DIR"

echo ""

# =============================================================================
# 5. 初始化数据库
# =============================================================================
echo "=========================================="
echo "🗄️  步骤 5/6: 初始化数据库"
echo "=========================================="
echo ""

echo "数据库会自动初始化，包括："
echo "  - 创建所有表结构"
echo "  - 创建测试用户账号"
echo "  - 导入资料库数据"

echo ""
echo "⏳ 等待后端完全启动..."
sleep 5

# 测试后端连接
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ 后端服务已就绪"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "⏳ 等待后端启动... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 3
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "⚠️  后端服务启动超时"
    echo "请运行以下命令查看日志："
    echo "  cd backend && docker compose logs api"
fi

echo ""

# =============================================================================
# 6. 完成
# =============================================================================
echo "=========================================="
echo "✅ 步骤 6/6: 初始化完成"
echo "=========================================="
echo ""

echo "🎉 项目初始化成功！"
echo ""
echo "=========================================="
echo "📋 服务信息"
echo "=========================================="
echo ""
echo "前端地址: http://localhost:5173"
echo "后端地址: http://localhost:8001"
echo "API 文档: http://localhost:8001/docs"
echo ""
echo "=========================================="
echo "👥 测试账号"
echo "=========================================="
echo ""
echo "管理员账号："
echo "  用户名: lifanghe   密码: admin123"
echo "  用户名: gexinlin   密码: admin123"
echo ""
echo "普通用户："
echo "  用户名: hewenze    密码: user123"
echo "  用户名: chenjinyi  密码: user123"
echo ""
echo "=========================================="
echo "🚀 下一步"
echo "=========================================="
echo ""
echo "1. 启动所有服务："
echo "   ./start.sh"
echo ""
echo "2. 访问前端："
echo "   http://localhost:5173"
echo ""
echo "3. 停止所有服务："
echo "   ./stop.sh"
echo ""
echo "=========================================="

