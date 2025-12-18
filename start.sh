#!/bin/bash

# =============================================================================
# MathTasks 项目启动脚本
# =============================================================================
# 用途：一键启动所有服务（前端、后端、数据库）
# 使用方法：./start.sh
# =============================================================================

set -e

echo "=========================================="
echo "🚀 启动 MathTasks 项目"
echo "=========================================="
echo ""

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo "❌ Docker Desktop 未运行"
    echo "请先启动 Docker Desktop"
    exit 1
fi

# =============================================================================
# 1. 启动后端和数据库
# =============================================================================
echo "📦 步骤 1/2: 启动后端服务..."
echo ""

cd backend

# 检查容器状态
if docker compose ps | grep -q "Up"; then
    echo "✅ Docker 容器已在运行"
else
    echo "正在启动 Docker 容器..."
    docker compose up -d
    echo "⏳ 等待服务启动..."
    sleep 10
fi

# 测试后端连接
echo ""
echo "🧪 测试后端连接..."
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ 后端服务正常"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            echo "❌ 后端服务连接失败"
            echo "请检查日志: docker compose logs api"
            exit 1
        fi
        echo "⏳ 等待后端启动... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 3
    fi
done

cd ..

echo ""

# =============================================================================
# 2. 启动前端
# =============================================================================
echo "📦 步骤 2/2: 启动前端服务..."
echo ""

# 检查前端是否已在运行
if lsof -ti:5173 > /dev/null 2>&1; then
    echo "⚠️  端口 5173 已被占用"
    echo "前端可能已在运行，或需要手动停止占用进程"
else
    echo "正在启动前端开发服务器..."
    cd frontend
    
    # 检查 node_modules
    if [ ! -d "node_modules" ]; then
        echo "⚠️  未找到 node_modules，正在安装依赖..."
        npm install
    fi
    
    # 后台启动前端
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    
    cd ..
    
    echo "⏳ 等待前端启动..."
    sleep 5
    
    if lsof -ti:5173 > /dev/null 2>&1; then
        echo "✅ 前端服务已启动"
    else
        echo "⚠️  前端启动可能失败，请检查日志: logs/frontend.log"
    fi
fi

echo ""

# =============================================================================
# 完成
# =============================================================================
echo "=========================================="
echo "✅ 所有服务已启动"
echo "=========================================="
echo ""
echo "🌐 前端地址: http://localhost:5173"
echo "🔧 后端地址: http://localhost:8001"
echo "📚 API 文档: http://localhost:8001/docs"
echo ""
echo "=========================================="
echo "👥 测试账号"
echo "=========================================="
echo ""
echo "管理员: lifanghe / admin123"
echo "普通用户: hewenze / user123"
echo ""
echo "=========================================="
echo "💡 提示"
echo "=========================================="
echo ""
echo "停止服务: ./stop.sh"
echo "查看日志: ./logs.sh"
echo "重启服务: ./restart.sh"
echo ""
echo "=========================================="

