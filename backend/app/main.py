"""
FastAPI 应用入口
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.services.problem_storage import init_mongodb, close_mongodb


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时初始化数据库，关闭时清理资源
    """
    # 启动时
    print(f"🚀 启动 {settings.APP_NAME} v{settings.VERSION}")
    await init_db()
    print("✅ PostgreSQL连接成功")
    
    # 初始化MongoDB
    if settings.MONGODB_URL:
        init_mongodb(settings.MONGODB_URL)
        print("✅ MongoDB连接成功")
    else:
        print("⚠️ MongoDB URL未配置，题目内容将存储在PostgreSQL")
    
    yield
    
    # 关闭时
    print("🛑 关闭数据库连接...")
    await close_db()
    if settings.MONGODB_URL:
        await close_mongodb()
    print("👋 再见！")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="数学题目众包平台 API",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 路由 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "database": "connected",
    }


@app.get("/api/config")
async def get_config():
    """获取前端配置（公开接口，无需认证）"""
    return {
        "max_tasks_per_claim": settings.MAX_TASKS_PER_CLAIM,
        "task_timeout_hours": settings.TASK_TIMEOUT_HOURS,
        "reward_per_problem": settings.PROBLEM_REWARD,
        "reward_per_review": settings.REVIEW_REWARD,
        "max_problems_total": settings.MAX_PROBLEMS_TOTAL,  # 用户总出题数上限
    }


# ==================== API 路由 ====================
from app.api import auth, materials, problems, reviews, tasks, users, deep_transform

# 认证路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])

# 用户路由
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])

# 资料库路由
app.include_router(materials.router, prefix="/api/materials", tags=["资料库"])

# 题目管理路由
app.include_router(problems.router, prefix="/api/problems", tags=["题目管理"])

# 评分路由
app.include_router(reviews.router, prefix="/api/reviews", tags=["评分管理"])

# 任务路由
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务管理"])

# 深度变形路由
app.include_router(deep_transform.router, prefix="/api/deep-transform", tags=["深度变形"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )

