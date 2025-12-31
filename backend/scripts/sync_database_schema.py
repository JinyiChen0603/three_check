"""
智能数据库结构同步脚本

基于 models.py 中定义的表结构，自动检测并同步数据库：
1. 读取 SQLAlchemy models（真实来源）
2. 对比当前数据库结构
3. 自动添加缺失的字段
4. 自动添加缺失的外键和索引
5. 不删除数据，只修改表结构

适用场景：
- 将同事的旧数据库升级到最新结构
- 修复数据库结构不一致问题
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text, MetaData, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 设置输出编码为 UTF-8（Windows 兼容）
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 加载环境变量
load_dotenv()

# 导入所有模型（确保 SQLAlchemy 知道它们）
from app.database import Base
from app.models import (
    User, Problem, Task, Review, Transaction, 
    MaterialLibrary, ValidationRecord, ValidatedProblemExport
)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set.")
    sys.exit(1)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_current_columns(session: AsyncSession, table_name: str) -> dict:
    """获取当前数据库中表的所有列"""
    result = await session.execute(text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = :table_name
        ORDER BY ordinal_position
    """), {"table_name": table_name})
    
    columns = {}
    for row in result:
        columns[row.column_name] = {
            "type": row.data_type,
            "nullable": row.is_nullable == "YES",
            "default": row.column_default
        }
    return columns


async def get_current_foreign_keys(session: AsyncSession, table_name: str) -> dict:
    """获取当前数据库中表的所有外键"""
    result = await session.execute(text("""
        SELECT 
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.delete_rule
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
        JOIN information_schema.referential_constraints AS rc
          ON rc.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
          AND tc.table_name = :table_name
    """), {"table_name": table_name})
    
    fks = {}
    for row in result:
        fks[row.constraint_name] = {
            "column": row.column_name,
            "ref_table": row.foreign_table_name,
            "ref_column": row.foreign_column_name,
            "on_delete": row.delete_rule
        }
    return fks


async def check_column_exists(session: AsyncSession, table_name: str, column_name: str) -> bool:
    """检查字段是否存在"""
    result = await session.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = :table_name AND column_name = :column_name
    """), {"table_name": table_name, "column_name": column_name})
    return result.fetchone() is not None


async def add_column_safe(session: AsyncSession, table_name: str, column_name: str, 
                         column_type: str, nullable: bool = True, default: str = None):
    """安全添加字段"""
    if not await check_column_exists(session, table_name, column_name):
        null_clause = "" if nullable else " NOT NULL"
        default_clause = f" DEFAULT {default}" if default else ""
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}{default_clause}{null_clause}"
        print(f"  [+] Adding: {table_name}.{column_name} ({column_type})")
        await session.execute(text(sql))
        return True
    else:
        print(f"  [✓] Exists: {table_name}.{column_name}")
        return False


async def make_column_nullable(session: AsyncSession, table_name: str, column_name: str):
    """将字段设置为可空"""
    if await check_column_exists(session, table_name, column_name):
        sql = f"ALTER TABLE {table_name} ALTER COLUMN {column_name} DROP NOT NULL"
        print(f"  [~] Making nullable: {table_name}.{column_name}")
        try:
            await session.execute(text(sql))
            return True
        except Exception:
            # 已经是可空，忽略错误
            return False
    return False


async def add_foreign_key_safe(session: AsyncSession, constraint_name: str,
                               table_name: str, column_name: str,
                               ref_table: str, ref_column: str,
                               on_delete: str = None):
    """安全添加外键"""
    # 检查约束是否存在
    result = await session.execute(text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE constraint_name = :constraint_name
    """), {"constraint_name": constraint_name})
    
    if result.fetchone() is None:
        on_delete_clause = f" ON DELETE {on_delete}" if on_delete else ""
        sql = f"""
        ALTER TABLE {table_name} 
        ADD CONSTRAINT {constraint_name} 
        FOREIGN KEY ({column_name}) 
        REFERENCES {ref_table}({ref_column}){on_delete_clause}
        """
        print(f"  [+] Adding FK: {constraint_name}")
        await session.execute(text(sql))
        return True
    else:
        print(f"  [✓] FK exists: {constraint_name}")
        return False


async def drop_unique_constraint_safe(session: AsyncSession, table_name: str, column_name: str):
    """安全删除unique约束"""
    # 查找该列的unique约束名
    result = await session.execute(text("""
        SELECT tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
          ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_name = :table_name 
          AND tc.constraint_type = 'UNIQUE'
          AND kcu.column_name = :column_name
    """), {"table_name": table_name, "column_name": column_name})
    
    constraint = result.fetchone()
    if constraint:
        constraint_name = constraint.constraint_name
        sql = f"ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name}"
        print(f"  [-] Dropping UNIQUE: {table_name}.{column_name} ({constraint_name})")
        await session.execute(text(sql))
        return True
    else:
        print(f"  [✓] No UNIQUE constraint: {table_name}.{column_name}")
        return False


async def create_index_safe(session: AsyncSession, index_name: str, table_name: str, 
                            columns: list, unique: bool = False):
    """安全创建索引"""
    # 检查索引是否存在
    result = await session.execute(text("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE indexname = :index_name
    """), {"index_name": index_name})
    
    if result.fetchone() is None:
        unique_clause = "UNIQUE " if unique else ""
        columns_str = ", ".join(columns)
        sql = f"CREATE {unique_clause}INDEX {index_name} ON {table_name}({columns_str})"
        print(f"  [+] Creating index: {index_name} on {table_name}({columns_str})")
        await session.execute(text(sql))
        return True
    else:
        print(f"  [✓] Index exists: {index_name}")
        return False


async def drop_index_safe(session: AsyncSession, index_name: str):
    """安全删除索引"""
    result = await session.execute(text("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE indexname = :index_name
    """), {"index_name": index_name})
    
    if result.fetchone() is not None:
        sql = f"DROP INDEX IF EXISTS {index_name}"
        print(f"  [-] Dropping index: {index_name}")
        await session.execute(text(sql))
        return True
    else:
        print(f"  [✓] Index not exists: {index_name}")
        return False


async def sync_enum_type(session: AsyncSession, enum_name: str, values: list, 
                         table_column_map: list = None):
    """同步枚举类型 - 添加小写值并更新数据"""
    print(f"  [~] Syncing ENUM: {enum_name}")
    
    try:
        # 1. 查询当前枚举值
        result = await session.execute(
            text(f"SELECT unnest(enum_range(NULL::{enum_name}))")
        )
        current_values = [row[0] for row in result.fetchall()]
        print(f"      Current values: {current_values}")
        
        # 2. 添加缺失的小写枚举值
        added = False
        for value in values:
            if value not in current_values:
                print(f"      [+] Adding value: '{value}'")
                await session.execute(
                    text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'")
                )
                await session.commit()
                added = True
        
        if not added:
            print(f"      [✓] All lowercase values exist")
        
        # 3. 更新表中的数据为小写（如果提供了映射）
        if table_column_map:
            for table, column in table_column_map:
                for value in values:
                    upper_value = value.upper()
                    try:
                        result = await session.execute(
                            text(f"UPDATE {table} SET {column} = '{value}' WHERE {column} = '{upper_value}'")
                        )
                        if result.rowcount > 0:
                            print(f"      [~] Updated {result.rowcount} rows: {table}.{column} = '{value}'")
                    except Exception:
                        pass  # 忽略错误（可能大写值不存在）
                await session.commit()
        
        return True
        
    except Exception as e:
        print(f"      [!] Warning: {e}")
        await session.rollback()
        return False


async def sync_database_schema():
    """同步数据库结构"""
    print("\n" + "="*80)
    print("智能数据库结构同步脚本".center(80))
    print("基于 models.py 自动检测并同步".center(80))
    print("="*80 + "\n")
    
    async with AsyncSessionLocal() as session:
        try:
            # ===================================================================
            # 定义需要同步的关键字段（基于你的 models.py）
            # ===================================================================
            
            migrations = [
                # Step 0: 同步所有枚举类型（确保小写值存在）
                {
                    "name": "Sync Enum: userrole",
                    "enum_sync": {
                        "enum_name": "userrole",
                        "values": ["admin", "user"],
                        "table_column_map": [("users", "role")]
                    }
                },
                {
                    "name": "Sync Enum: problemsourcetype",
                    "enum_sync": {
                        "enum_name": "problemsourcetype",
                        "values": ["manual", "ocr", "variant"],
                        "table_column_map": [("problems", "source_type")]
                    }
                },
                {
                    "name": "Sync Enum: problemvalidationstatus",
                    "enum_sync": {
                        "enum_name": "problemvalidationstatus",
                        "values": ["not_validated", "difficulty_checking", "difficulty_passed", "difficulty_failed"],
                        "table_column_map": [("problems", "validation_status")]
                    }
                },
                {
                    "name": "Sync Enum: problemstatus",
                    "enum_sync": {
                        "enum_name": "problemstatus",
                        "values": ["draft", "pending_review", "approved", "rejected", "published"],
                        "table_column_map": [("problems", "status")]
                    }
                },
                {
                    "name": "Sync Enum: humanreviewstatus",
                    "enum_sync": {
                        "enum_name": "humanreviewstatus",
                        "values": ["pending", "in_progress", "approved", "rejected"],
                        "table_column_map": [("problems", "human_review_status")]
                    }
                },
                {
                    "name": "Sync Enum: materialcategory",
                    "enum_sync": {
                        "enum_name": "materialcategory",
                        "values": ["math", "physics", "chemistry", "biology", "other"],
                        "table_column_map": [("problems", "category"), ("material_library", "category")]
                    }
                },
                {
                    "name": "Sync Enum: tasktype",
                    "enum_sync": {
                        "enum_name": "tasktype",
                        "values": ["review_problem", "create_problem"],
                        "table_column_map": [("tasks", "task_type")]
                    }
                },
                {
                    "name": "Sync Enum: taskstatus",
                    "enum_sync": {
                        "enum_name": "taskstatus",
                        "values": ["pending", "in_progress", "submitted", "approved", "rejected", "timeout"],
                        "table_column_map": [("tasks", "status")]
                    }
                },
                {
                    "name": "Sync Enum: reviewstatus",
                    "enum_sync": {
                        "enum_name": "reviewstatus",
                        "values": ["pending", "approved", "rejected"],
                        "table_column_map": [("reviews", "status")]
                    }
                },
                {
                    "name": "Sync Enum: adminreviewstatus",
                    "enum_sync": {
                        "enum_name": "adminreviewstatus",
                        "values": ["pending", "approved", "rejected"],
                        "table_column_map": [("validated_problem_exports", "admin_review_status")]
                    }
                },
                {
                    "name": "Sync Enum: transactiontype",
                    "enum_sync": {
                        "enum_name": "transactiontype",
                        "values": ["problem_reward", "review_reward", "withdrawal", "adjustment"],
                        "table_column_map": [("transactions", "transaction_type")]
                    }
                },
                {
                    "name": "Sync Enum: transactionstatus",
                    "enum_sync": {
                        "enum_name": "transactionstatus",
                        "values": ["pending", "confirmed", "cancelled"],
                        "table_column_map": [("transactions", "status")]
                    }
                },
                
                # Step 1: validated_problem_exports 表 - 添加 task_id
                {
                    "name": "validated_problem_exports.task_id",
                    "table": "validated_problem_exports",
                    "column": "task_id",
                    "type": "INTEGER",
                    "nullable": True,
                    "foreign_key": {
                        "name": "fk_validated_problem_exports_task_id",
                        "ref_table": "tasks",
                        "ref_column": "id",
                        "on_delete": None
                    }
                },
                
                # Step 2: validated_problem_exports 表 - 添加评分相关字段
                {
                    "name": "validated_problem_exports.review_count",
                    "table": "validated_problem_exports",
                    "column": "review_count",
                    "type": "INTEGER",
                    "nullable": False,
                    "default": "0"
                },
                {
                    "name": "validated_problem_exports.avg_innovation_score",
                    "table": "validated_problem_exports",
                    "column": "avg_innovation_score",
                    "type": "DOUBLE PRECISION",
                    "nullable": True
                },
                {
                    "name": "validated_problem_exports.avg_rigor_score",
                    "table": "validated_problem_exports",
                    "column": "avg_rigor_score",
                    "type": "DOUBLE PRECISION",
                    "nullable": True
                },
                
                # Step 3: reviews 表 - 删除 task_id 的 unique 约束
                {
                    "name": "reviews.task_id - drop unique",
                    "table": "reviews",
                    "drop_unique": "task_id"
                },
                
                # Step 3.1: reviews 表 - is_answer_correct 改为可空（领取任务时还未验证）
                {
                    "name": "reviews.is_answer_correct - make nullable",
                    "table": "reviews",
                    "make_nullable": ["is_answer_correct"]
                },
                
                # Step 4: reviews 表 - 添加 validated_problem_id
                {
                    "name": "reviews.validated_problem_id",
                    "table": "reviews",
                    "column": "validated_problem_id",
                    "type": "INTEGER",
                    "nullable": True,
                    "make_nullable": ["problem_id"],  # 旧字段改为可空
                    "foreign_key": {
                        "name": "fk_reviews_validated_problem_id",
                        "ref_table": "validated_problem_exports",
                        "ref_column": "id",
                        "on_delete": "CASCADE"
                    }
                },
                
                # Step 4: tasks 表 - 添加 validated_problem_id
                {
                    "name": "tasks.validated_problem_id",
                    "table": "tasks",
                    "column": "validated_problem_id",
                    "type": "INTEGER",
                    "nullable": True,
                    "make_nullable": ["problem_id"],  # 旧字段改为可空
                    "foreign_key": {
                        "name": "fk_tasks_validated_problem_id",
                        "ref_table": "validated_problem_exports",
                        "ref_column": "id",
                        "on_delete": "CASCADE"
                    }
                },
                
                # Step 5: validation_records 表 - 添加 validated_problem_id
                {
                    "name": "validation_records.validated_problem_id",
                    "table": "validation_records",
                    "column": "validated_problem_id",
                    "type": "INTEGER",
                    "nullable": True,
                    "make_nullable": ["problem_id"],  # 旧字段改为可空
                    "foreign_key": {
                        "name": "fk_validation_validated_problem_id",
                        "ref_table": "validated_problem_exports",
                        "ref_column": "id",
                        "on_delete": "CASCADE"
                    },
                    "drop_indexes": ["idx_problem_type"],  # 删除旧索引
                    "create_indexes": [
                        {
                            "name": "idx_validated_problem_type",
                            "columns": ["validated_problem_id", "validation_type"]
                        }
                    ]
                },
            ]
            
            # ===================================================================
            # 执行迁移
            # ===================================================================
            
            for i, migration in enumerate(migrations, 1):
                print(f"Step {i}: {migration['name']}")
                print("-" * 80)
                
                # 0. 同步枚举类型（如果需要）
                if "enum_sync" in migration:
                    enum_config = migration["enum_sync"]
                    await sync_enum_type(
                        session,
                        enum_config["enum_name"],
                        enum_config["values"],
                        enum_config.get("table_column_map")
                    )
                    await session.commit()
                    print()
                    continue
                
                # 1. 删除unique约束（如果需要）
                if "drop_unique" in migration:
                    await drop_unique_constraint_safe(
                        session,
                        migration["table"],
                        migration["drop_unique"]
                    )
                
                # 2. 将旧字段改为可空（如果需要）
                if "make_nullable" in migration:
                    for old_col in migration["make_nullable"]:
                        await make_column_nullable(session, migration["table"], old_col)
                
                # 3. 添加新字段
                if "column" in migration:
                    await add_column_safe(
                        session,
                        migration["table"],
                        migration["column"],
                        migration["type"],
                        migration["nullable"],
                        migration.get("default")
                    )
                
                # 4. 添加外键
                if "foreign_key" in migration:
                    fk = migration["foreign_key"]
                    await add_foreign_key_safe(
                        session,
                        fk["name"],
                        migration["table"],
                        migration["column"],
                        fk["ref_table"],
                        fk["ref_column"],
                        fk.get("on_delete")
                    )
                
                # 5. 删除旧索引
                if "drop_indexes" in migration:
                    for index_name in migration["drop_indexes"]:
                        await drop_index_safe(session, index_name)
                
                # 6. 创建新索引
                if "create_indexes" in migration:
                    for idx in migration["create_indexes"]:
                        await create_index_safe(
                            session,
                            idx["name"],
                            migration["table"],
                            idx["columns"],
                            idx.get("unique", False)
                        )
                
                await session.commit()
                print()
            
            print("="*80)
            print("数据库结构同步完成！".center(80))
            print("="*80 + "\n")
            
            print("Summary:")
            print("  ✓ 所有枚举类型已同步为小写值 (12个枚举):")
            print("    - userrole, problemsourcetype, problemvalidationstatus, problemstatus")
            print("    - humanreviewstatus, materialcategory, tasktype, taskstatus")
            print("    - reviewstatus, adminreviewstatus, transactiontype, transactionstatus")
            print("  ✓ validated_problem_exports.task_id (关联出题任务)")
            print("  ✓ validated_problem_exports.review_count (评分次数, 默认0)")
            print("  ✓ validated_problem_exports.avg_innovation_score (平均创新分)")
            print("  ✓ validated_problem_exports.avg_rigor_score (平均严谨分)")
            print("  ✓ reviews.task_id - 删除UNIQUE约束 (允许一个任务多个评分)")
            print("  ✓ reviews.is_answer_correct - 改为可空 (领取任务时还未验证)")
            print("  ✓ reviews.validated_problem_id (CASCADE)")
            print("  ✓ tasks.validated_problem_id (CASCADE)")
            print("  ✓ validation_records.validated_problem_id (CASCADE)")
            print("  ✓ 旧数据保留，新字段使用默认值或NULL")
            print("\n设计说明:")
            print("  - 所有枚举类型使用小写值（与 models.py 保持一致）")
            print("  - 数据库中的大写枚举值会自动转换为小写")
            print("  - ValidatedProblemExport表包含评分状态和分数")
            print("  - Review表记录评分详情，task_id关联评分任务批次")
            print("  - ValidationRecord表记录质检验证详情，关联到ValidatedProblemExport")
            print("  - 一个评分任务(Task)可以产生多个评分记录(Review)")
            print("  - validation_records.validated_problem_id允许为NULL（用于内容质检）")
            print()

        except Exception as e:
            await session.rollback()
            print(f"\n[ERROR] 同步失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


async def check_database_diff():
    """检查数据库差异"""
    print("\n" + "="*80)
    print("数据库结构差异检查".center(80))
    print("="*80 + "\n")
    
    async with AsyncSessionLocal() as session:
        # 需要检查的表和字段
        expected_structure = {
            "validated_problem_exports": ["id", "user_id", "task_id", "content", 
                                         "answer", "explanation", "review_count", "created_at"],
            "reviews": ["id", "problem_id", "validated_problem_id", "reviewer_id", 
                       "task_id", "is_answer_correct", "status"],
            "tasks": ["id", "problem_id", "validated_problem_id", "user_id", 
                     "task_type", "status", "batch_id"],
            "validation_records": ["id", "problem_id", "validated_problem_id", 
                                  "validation_type", "ai_model", "is_passed"],
        }
        
        print("检查关键字段:")
        print("-" * 80)
        
        for table, columns in expected_structure.items():
            print(f"\nTable: {table}")
            current_cols = await get_current_columns(session, table)
            
            for col in columns:
                if col in current_cols:
                    info = current_cols[col]
                    status = "✓"
                    detail = f"({info['type']}, {'NULL' if info['nullable'] else 'NOT NULL'})"
                else:
                    status = "✗ MISSING"
                    detail = ""
                
                print(f"  {status} {col} {detail}")
        
        print("\n" + "="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="智能数据库结构同步脚本")
    parser.add_argument("--check", action="store_true", help="检查数据库差异")
    parser.add_argument("--sync", action="store_true", help="执行完整同步（需要确认）")
    parser.add_argument("--auto-sync", action="store_true", help="自动同步（Docker 启动时使用，无需确认）")
    
    args = parser.parse_args()
    
    if args.check:
        asyncio.run(check_database_diff())
    elif args.auto_sync:
        # Docker 启动时自动调用，不需要确认
        print("🚀 自动同步模式（无需确认）")
        asyncio.run(sync_database_schema())
    elif args.sync:
        response = input("警告: 这将修改数据库结构。是否继续？ (yes/no): ")
        if response.lower() == "yes":
            asyncio.run(sync_database_schema())
        else:
            print("已取消")
    else:
        print("Usage:")
        print("  python sync_database_schema.py --check      # 检查差异")
        print("  python sync_database_schema.py --sync       # 执行同步（需确认）")
        print("  python sync_database_schema.py --auto-sync  # 自动同步（无需确认）")

