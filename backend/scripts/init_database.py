"""
数据库初始化脚本
1. 清空所有数据表（除了 users 表）
2. 运行数据库迁移（确保表结构是最新的）

⚠️ 警告：此脚本会清空所有数据（除了 users 表），请谨慎使用！
"""

import asyncio
import sys
import io
from pathlib import Path

# 设置标准输出编码为 UTF-8（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.database import _get_session_local


async def clear_all_tables():
    """清空所有数据表（除了 users 表）"""
    print("\n[Init] Clearing all tables (except users)...")
    
    # 需要清空的表列表（按外键依赖顺序，先删除有外键的表）
    tables_to_clear = [
        "validated_problem_exports",
        "validation_records",
        "reviews",
        "transactions",
        "tasks",
        "problems",
        "material_library",
    ]
    
    AsyncSessionLocal = _get_session_local()
    async with AsyncSessionLocal() as session:
        try:
            # 禁用外键检查（PostgreSQL）
            await session.execute(text("SET session_replication_role = 'replica';"))
            
            for table_name in tables_to_clear:
                try:
                    # 使用 TRUNCATE CASCADE 清空表（包括外键关联的数据）
                    await session.execute(text(f'TRUNCATE TABLE "{table_name}" CASCADE;'))
                    print(f"  [OK] Cleared table: {table_name}")
                except OperationalError as e:
                    # 如果表不存在，跳过（可能是首次运行，表还未创建）
                    if "does not exist" in str(e) or "不存在" in str(e):
                        print(f"  [Skip] Table {table_name} does not exist, skipping")
                    else:
                        print(f"  [Warning] Failed to clear table {table_name}: {e}")
                except Exception as e:
                    print(f"  [Warning] Error clearing table {table_name}: {e}")
            
            # 恢复外键检查
            await session.execute(text("SET session_replication_role = 'origin';"))
            await session.commit()
            print("[Success] All tables cleared successfully!")
            
        except Exception as e:
            await session.rollback()
            print(f"[Error] Failed to clear tables: {e}")
            raise


async def run_migrations():
    """运行数据库迁移"""
    print("\n[Init] Running database migrations...")
    try:
        import subprocess
        import os
        
        # 切换到项目根目录
        backend_dir = Path(__file__).parent.parent
        os.chdir(backend_dir)
        
        # 运行 alembic upgrade head
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=backend_dir
        )
        
        if result.returncode == 0:
            print("[Success] Database migrations completed!")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"[Warning] Migration command returned non-zero exit code: {result.returncode}")
            if result.stderr:
                print(f"[Error] {result.stderr}")
            print("[Info] You may need to run 'alembic upgrade head' manually")
        
    except FileNotFoundError:
        print("[Warning] Alembic command not found. Please run 'alembic upgrade head' manually")
    except Exception as e:
        print(f"[Warning] Failed to run migrations: {e}")
        print("[Info] You may need to run 'alembic upgrade head' manually")


async def main():
    """主函数"""
    print("="*60)
    print("数据库初始化脚本")
    print("="*60)
    print("\n⚠️  警告：此脚本会清空所有数据表（除了 users 表）！")
    print("\n[Info] This script will:")
    print("  1. Clear all data tables (except users)")
    print("  2. Run database migrations")
    print("="*60)
    
    # 确认操作
    try:
        response = input("\n确认要继续吗？(yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("[Cancel] Operation cancelled by user")
            sys.exit(0)
    except (KeyboardInterrupt, EOFError):
        print("\n[Cancel] Operation cancelled by user")
        sys.exit(0)
    
    try:
        # 1. 清空所有表（除了 users）
        await clear_all_tables()
        
        # 2. 运行数据库迁移
        await run_migrations()
        
        print("\n" + "="*60)
        print("[Success] Database initialization completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n[Error] Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

