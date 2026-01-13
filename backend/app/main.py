"""
FastAPI 应用入口 - 数学题目三重质检工具
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.redis_client import init_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时
    print(f"🚀 启动 {settings.APP_NAME} v{settings.VERSION}")
    
    # 初始化Redis（用于进度追踪）
    if settings.REDIS_URL:
        try:
            await init_redis()
            print("✅ Redis连接成功")
        except Exception as e:
            print(f"⚠️ Redis连接失败: {e}，进度追踪功能将不可用")
    else:
        print("⚠️ Redis URL未配置，进度追踪功能将不可用")
    
    yield
    
    # 关闭时
    print("🛑 关闭服务...")
    if settings.REDIS_URL:
        await close_redis()
    print("👋 再见！")


# 创建 FastAPI 应用
app = FastAPI(
    title="数学题目三重质检工具",
    description="提供难度、原创性、严谨性三重质检服务",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 配置 CORS（无需认证）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,  # 不需要cookie认证
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 路由 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "数学题目三重质检工具",
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "features": ["难度检测", "原创性检测", "严谨性检测", "OCR识别"],
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
    }


# ==================== API 路由 ====================
from app.api import problems

# 题目质检路由（包含三重检测和OCR）
app.include_router(problems.router, prefix="/api/problems", tags=["题目质检"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )

