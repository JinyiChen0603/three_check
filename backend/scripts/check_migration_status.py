#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库迁移状态和表结构
"""
import asyncio
import sys
import os
from pathlib import Path

# 设置 UTF-8 编码
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from app.database import engine
from app.config import settings


async def check_migration_status():
    """检查迁移状态"""
    print("=" * 60)
    print("数据库迁移状态检查")
    print("=" * 60)
    
    async with engine.connect() as conn:
        # 检查 alembic_version 表是否存在
        check_table_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'alembic_version'
            );
        """)
        result = await conn.execute(check_table_query)
        table_exists = result.scalar()
        
        if not table_exists:
            print("[X] alembic_version 表不存在，数据库可能未初始化")
            return
        
        # 获取当前迁移版本
        version_query = text("SELECT version_num FROM alembic_version;")
        result = await conn.execute(version_query)
        current_version = result.scalar()
        
        print(f"[OK] 当前迁移版本: {current_version}")
        
        # 列出所有迁移版本
        print("\n所有迁移版本:")
        versions = [
            ("4deaebe64c95", "initial_schema_with_all_tables"),
            ("9781f667e036", "remove_problem_count_from_materials"),
            ("add_mongo_id_001", "add_mongo_id_to_problems"),
            ("validated_export_001", "add_validated_problem_export_table"),
            ("make_category_nullable", "make_category_nullable"),
            ("remove_is_exported_001", "remove_is_exported_fields"),
        ]
        
        for version_id, description in versions:
            status = "[OK] 已执行" if current_version == version_id else "[  ] 待执行"
            print(f"  {status} - {version_id}: {description}")
        
        # 检查最新的迁移是否已执行
        latest_migration = "remove_is_exported_001"
        if current_version == latest_migration:
            print(f"\n[OK] 最新迁移 ({latest_migration}) 已执行")
        else:
            print(f"\n[!] 最新迁移 ({latest_migration}) 尚未执行")


async def check_table_structure():
    """检查表结构"""
    print("\n" + "=" * 60)
    print("检查 validated_problem_exports 表结构")
    print("=" * 60)
    
    async with engine.connect() as conn:
        # 检查表是否存在
        check_table_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'validated_problem_exports'
            );
        """)
        result = await conn.execute(check_table_query)
        table_exists = result.scalar()
        
        if not table_exists:
            print("[X] validated_problem_exports 表不存在")
            return
        
        print("[OK] validated_problem_exports 表存在")
        
        # 获取所有列信息
        columns_query = text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'validated_problem_exports'
            ORDER BY ordinal_position;
        """)
        result = await conn.execute(columns_query)
        columns = result.fetchall()
        
        print("\n表结构:")
        for col_name, data_type, is_nullable in columns:
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            print(f"  - {col_name:30s} {data_type:20s} {nullable}")
        
        # 检查 is_exported 和 exported_at 字段
        column_names = [col[0] for col in columns]
        
        print("\n字段检查:")
        if "is_exported" in column_names:
            print("  [X] is_exported 字段仍然存在（需要执行迁移）")
        else:
            print("  [OK] is_exported 字段已删除")
        
        if "exported_at" in column_names:
            print("  [X] exported_at 字段仍然存在（需要执行迁移）")
        else:
            print("  [OK] exported_at 字段已删除")


async def main():
    """主函数"""
    try:
        db_info = settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'N/A'
        print(f"数据库连接: {db_info}")
        print()
        
        await check_migration_status()
        await check_table_structure()
        
        print("\n" + "=" * 60)
        print("提示:")
        print("  如果迁移未执行，请运行: alembic upgrade head")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

