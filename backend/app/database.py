"""
数据库连接管理
使用 SQLAlchemy 异步引擎
"""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import declarative_base

from app.config import settings

# 声明基类（不依赖引擎，可以立即创建）
Base = declarative_base()

# 延迟初始化的引擎和会话工厂
_engine: Optional[AsyncEngine] = None
_AsyncSessionLocal: Optional[async_sessionmaker] = None


def _get_engine() -> AsyncEngine:
    """延迟初始化数据库引擎"""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,  # 开发环境打印SQL
            pool_pre_ping=True,   # 连接池预检查
            pool_size=10,         # 连接池大小
            max_overflow=20,      # 最大溢出连接数
        )
    return _engine


def _get_session_local() -> async_sessionmaker:
    """延迟初始化会话工厂"""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _AsyncSessionLocal


# 为了向后兼容，提供 engine 和 AsyncSessionLocal 作为模块级变量
# 使用 __getattr__ 实现延迟访问（Python 3.7+）
# 这样导入模块时不会立即创建引擎，只有在实际使用时才会创建
def __getattr__(name: str):
    if name == "engine":
        return _get_engine()
    elif name == "AsyncSessionLocal":
        return _get_session_local()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    依赖注入：获取数据库会话
    
    使用方式:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with _get_session_local()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    初始化数据库
    创建所有表（生产环境应使用 Alembic）
    """
    async with _get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    关闭数据库连接
    应在应用关闭时调用
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        global _AsyncSessionLocal
        _AsyncSessionLocal = None

