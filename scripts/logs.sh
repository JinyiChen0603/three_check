#!/bin/bash

# =============================================================================
# MathTasks 项目日志查看脚本
# =============================================================================
# 用途：查看服务日志
# 使用方法：./scripts/logs.sh [frontend|backend|database|all]
# =============================================================================

SERVICE=${1:-all}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=========================================="
echo "📋 MathTasks 服务日志"
echo "=========================================="
echo ""

case $SERVICE in
    frontend)
        echo "🌐 前端日志："
        echo "=========================================="
        if [ -f "logs/frontend.log" ]; then
            tail -50 logs/frontend.log
        else
            echo "❌ 未找到前端日志文件"
        fi
        ;;
    
    backend)
        echo "🔧 后端日志："
        echo "=========================================="
        cd "$ROOT_DIR/backend"
        docker compose logs api --tail 50
        cd "$ROOT_DIR"
        ;;
    
    database)
        echo "🗄️  数据库日志："
        echo "=========================================="
        cd "$ROOT_DIR/backend"
        docker compose logs postgres --tail 50
        cd "$ROOT_DIR"
        ;;
    
    all)
        echo "🌐 前端日志（最后20行）："
        echo "=========================================="
        if [ -f "$ROOT_DIR/logs/frontend.log" ]; then
            tail -20 "$ROOT_DIR/logs/frontend.log"
        else
            echo "❌ 未找到前端日志文件"
        fi
        
        echo ""
        echo "🔧 后端日志（最后20行）："
        echo "=========================================="
        cd "$ROOT_DIR/backend"
        docker compose logs api --tail 20
        
        echo ""
        echo "🗄️  数据库日志（最后10行）："
        echo "=========================================="
        docker compose logs postgres --tail 10
        cd "$ROOT_DIR"
        ;;
    
    *)
        echo "❌ 无效的服务名称: $SERVICE"
        echo ""
        echo "用法："
        echo "  ./logs.sh              # 查看所有日志"
        echo "  ./logs.sh frontend     # 仅查看前端日志"
        echo "  ./logs.sh backend      # 仅查看后端日志"
        echo "  ./logs.sh database     # 仅查看数据库日志"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "💡 提示"
echo "=========================================="
echo ""
echo "实时查看日志："
echo "  前端: tail -f logs/frontend.log"
echo "  后端: cd backend && docker compose logs -f api"
echo "  数据库: cd backend && docker compose logs -f postgres"
echo ""

