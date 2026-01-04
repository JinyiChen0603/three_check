"""
数据库表结构初始化脚本
直接从 models.py 创建所有表结构（不使用 Alembic）

使用方法：
    python init_database.py

注意：
    - 确保 models.py 中的 Base 和所有模型已正确导入
    - 需要修改 DATABASE_URL 为实际的数据库连接字符串
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径到 sys.path（假设 models.py 在同目录）
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine


# ==================== 配置区 ====================
# 根据实际情况修改数据库连接
# 如果在 Docker 容器内执行，使用服务名：
# DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres:5433/mathtasks"

# 如果在宿主机执行，使用 localhost：
DATABASE_URL = "postgresql+asyncpg://mathtasks:mathtasks123@localhost:5434/mathtasks?ssl=disable"
# ================================================


async def init_database():
    """创建所有表结构"""
    try:
        # 导入所有模型（确保所有表都被注册到 Base.metadata）
        from app.models import (
            Base, User, Problem, Task, Review, Transaction,
            MaterialLibrary, ValidationRecord, ValidatedProblemExport
        )
        
        print("=" * 60)
        print("🏗️  开始创建数据库表结构")
        print("=" * 60)
        print(f"数据库: {DATABASE_URL.split('@')[-1]}")  # 隐藏密码
        print()
        
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
        
        await engine.dispose()
        
        print()
        print("=" * 60)
        print("✅ 表结构创建成功！")
        print("=" * 60)
        print("\n已创建的表：")
        print("  - users")
        print("  - material_library")
        print("  - problems")
        print("  - tasks")
        print("  - validated_problem_exports")
        print("  - validation_records")
        print("  - reviews")
        print("  - transactions")
        print()
        
    # except ImportError as e:
    #     print(f"❌ 导入错误: {e}")
    #     print("提示：确保 models.py 在当前目录，且 Base 已正确定义")
    #     sys.exit(1)
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(init_database())

