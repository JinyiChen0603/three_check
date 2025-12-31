"""
数据迁移脚本
从备份数据迁移到新数据库结构

使用方法：
    python migrate_data.py

功能：
    1. 迁移 users 表（20条）
    2. 迁移 tasks 表（18条）
    3. 迁移 validated_problem_exports 表（5条）
    4. 从 JSON 字段提取并创建 validation_records（约15条）
    5. 验证迁移结果
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.models import (
    User, ValidatedProblemExport, Task, ValidationRecord,
    UserRole, TaskType, TaskStatus, AdminReviewStatus
)


# ==================== 配置区 ====================
DATABASE_URL = "postgresql+asyncpg://mathtasks:mathtasks123@localhost:5433/mathtasks?ssl=disable"
BACKUP_DIR = Path(__file__).parent  # 备份数据在当前目录
# ================================================


async def migrate_users(session: AsyncSession):
    """迁移 users 表"""
    print("📦 [1/4] 迁移 users 表...")
    
    users_file = BACKUP_DIR / "tables" / "users.json"
    with open(users_file, 'r', encoding='utf-8') as f:
        users_data = json.load(f)
    
    for user_data in users_data:
        user = User(
            id=user_data['id'],
            username=user_data['username'],
            email=user_data['email'],
            password_hash=user_data['password_hash'],
            role=UserRole(user_data['role'].lower()),  # ADMIN -> admin
            balance=user_data['balance'],
            problems_created_count=user_data['problems_created_count'],
            reviews_completed_count=user_data['reviews_completed_count'],
            is_active=user_data['is_active'],
            is_impersonating=user_data['is_impersonating'],
            created_at=datetime.fromisoformat(user_data['created_at']),
            updated_at=datetime.fromisoformat(user_data['updated_at']),
            last_login_at=datetime.fromisoformat(user_data['last_login_at']) 
                          if user_data['last_login_at'] else None,
        )
        session.add(user)
    
    await session.flush()
    print(f"  ✅ 已迁移 {len(users_data)} 条用户记录")


async def migrate_tasks(session: AsyncSession):
    """迁移 tasks 表"""
    print("📦 [2/4] 迁移 tasks 表...")
    
    tasks_file = BACKUP_DIR / "tables" / "tasks.json"
    with open(tasks_file, 'r', encoding='utf-8') as f:
        tasks_data = json.load(f)
    
    for task_data in tasks_data:
        # 枚举值转换为小写
        status_value = task_data['status'].lower()  # IN_PROGRESS -> in_progress
        task_type_value = task_data['task_type'].lower()  # CREATE_PROBLEM -> create_problem
        
        task = Task(
            id=task_data['id'],
            problem_id=task_data.get('problem_id'),
            validated_problem_id=None,  # 新字段，暂时为NULL（兼容用）
            user_id=task_data['user_id'],
            task_type=TaskType(task_type_value),
            batch_id=task_data.get('batch_id'),
            total_count=task_data['total_count'],
            completed_count=task_data['completed_count'],
            abandoned_count=task_data['abandoned_count'],
            status=TaskStatus(status_value),
            claimed_at=datetime.fromisoformat(task_data['claimed_at']) 
                       if task_data['claimed_at'] else None,
            expires_at=datetime.fromisoformat(task_data['expires_at']) 
                       if task_data['expires_at'] else None,
            submitted_at=datetime.fromisoformat(task_data['submitted_at']) 
                        if task_data['submitted_at'] else None,
            approved_at=datetime.fromisoformat(task_data['approved_at']) 
                       if task_data['approved_at'] else None,
            result_data=task_data.get('result_data'),
            created_at=datetime.fromisoformat(task_data['created_at']),
            updated_at=datetime.fromisoformat(task_data['updated_at']),
        )
        session.add(task)
    
    await session.flush()
    print(f"  ✅ 已迁移 {len(tasks_data)} 条任务记录")


async def migrate_validated_problem_exports(session: AsyncSession):
    """迁移 validated_problem_exports 表"""
    print("📦 [3/4] 迁移 validated_problem_exports 表...")
    
    exports_file = BACKUP_DIR / "tables" / "validated_problem_exports.json"
    with open(exports_file, 'r', encoding='utf-8') as f:
        exports_data = json.load(f)
    
    for export_data in exports_data:
        export = ValidatedProblemExport(
            id=export_data['id'],
            user_id=export_data['user_id'],
            task_id=export_data.get('task_id'),
            content=export_data['content'],
            answer=export_data['answer'],
            explanation=export_data['explanation'],
            difficulty_validation=export_data.get('difficulty_validation'),
            originality_check=export_data['originality_check'],
            rigor_check=export_data['rigor_check'],
            # 🆕 新字段 - 设置默认值
            review_count=0,
            avg_innovation_score=None,
            avg_rigor_score=None,
            admin_review_status=AdminReviewStatus.PENDING,
            admin_reviewer_id=None,
            admin_review_note=None,
            admin_reviewed_at=None,
            created_at=datetime.fromisoformat(export_data['created_at']),
        )
        session.add(export)
    
    await session.flush()
    print(f"  ✅ 已迁移 {len(exports_data)} 条导出记录")
    print(f"      新增字段已设置默认值：review_count=0, admin_review_status=PENDING")
    
    return exports_data


async def migrate_validation_records(session: AsyncSession, exports_data):
    """
    从旧数据的 JSON 字段提取并创建 validation_records
    
    旧结构：validated_problem_exports 表中有三个 JSON 字段
        - difficulty_validation
        - originality_check
        - rigor_check
    
    新结构：独立的 validation_records 表
    """
    print("📦 [4/4] 提取并创建 validation_records...")
    
    validation_records_created = 0
    
    for export_data in exports_data:
        validated_problem_id = export_data['id']
        created_at = datetime.fromisoformat(export_data['created_at'])
        
        # 1. 难度验证记录
        if export_data.get('difficulty_validation'):
            dv = export_data['difficulty_validation']
            if dv.get('success'):
                record = ValidationRecord(
                    validated_problem_id=validated_problem_id,
                    validation_type='difficulty',
                    ai_model=dv.get('ai_model', 'doubao-seed-thinking'),
                    attempts=dv.get('attempts'),
                    correct_count=dv.get('correct_count'),
                    is_passed=dv.get('is_passed', False),
                    result_data=dv,
                    created_at=created_at,
                )
                session.add(record)
                validation_records_created += 1
        
        # 2. 原创性验证记录
        if export_data.get('originality_check'):
            oc = export_data['originality_check']
            if oc.get('success'):
                record = ValidationRecord(
                    validated_problem_id=validated_problem_id,
                    validation_type='originality',
                    ai_model=oc.get('ai_model', 'gpt-5.2-research'),
                    attempts=None,
                    correct_count=None,
                    is_passed=oc.get('is_original', False),
                    result_data=oc,
                    created_at=created_at,
                )
                session.add(record)
                validation_records_created += 1
        
        # 3. 严谨性验证记录
        if export_data.get('rigor_check'):
            rc = export_data['rigor_check']
            if rc.get('success'):
                record = ValidationRecord(
                    validated_problem_id=validated_problem_id,
                    validation_type='rigor',
                    ai_model=rc.get('ai_model', 'gpt-5.2'),
                    attempts=None,
                    correct_count=None,
                    is_passed=rc.get('is_rigorous', False),
                    result_data=rc,
                    created_at=created_at,
                )
                session.add(record)
                validation_records_created += 1
    
    await session.flush()
    print(f"  ✅ 已创建 {validation_records_created} 条验证记录")
    print(f"      每个题目提取了 3 种验证记录（difficulty, originality, rigor）")


async def verify_migration(session: AsyncSession):
    """验证迁移结果"""
    print("\n🔍 验证迁移结果...")
    print("-" * 60)
    
    # 1. 统计各表记录数
    tables = [
        ('users', User),
        ('tasks', Task),
        ('validated_problem_exports', ValidatedProblemExport),
        ('validation_records', ValidationRecord),
    ]
    
    print("📊 各表记录数：")
    for table_name, model in tables:
        result = await session.execute(select(func.count()).select_from(model))
        count = result.scalar()
        print(f"  ✓ {table_name}: {count} 条")
    
    # 2. 检查新增字段
    print("\n🆕 新增字段检查（validated_problem_exports）：")
    result = await session.execute(
        select(
            ValidatedProblemExport.id,
            ValidatedProblemExport.review_count,
            ValidatedProblemExport.admin_review_status
        ).limit(3)
    )
    rows = result.all()
    for row in rows:
        print(f"  ✓ ID={row.id}: review_count={row.review_count}, admin_review_status={row.admin_review_status}")
    
    # 3. 检查外键完整性
    print("\n🔗 外键完整性检查：")
    result = await session.execute(
        select(ValidatedProblemExport)
        .outerjoin(User, ValidatedProblemExport.user_id == User.id)
        .where(User.id.is_(None))
    )
    orphaned = result.scalars().all()
    if orphaned:
        print(f"  ⚠️  发现 {len(orphaned)} 条孤立记录")
    else:
        print("  ✓ 所有外键关系完整")
    
    # 4. 检查 validation_records 分布
    print("\n📋 验证记录分布：")
    result = await session.execute(
        select(
            ValidationRecord.validation_type,
            func.count(ValidationRecord.id).label('count')
        )
        .group_by(ValidationRecord.validation_type)
    )
    for row in result:
        print(f"  ✓ {row.validation_type}: {row.count} 条")
    
    print("-" * 60)


async def main():
    """主迁移流程"""
    print("=" * 60)
    print("🚀 开始数据迁移")
    print("=" * 60)
    print(f"备份目录: {BACKUP_DIR}")
    print(f"数据库: {DATABASE_URL.split('@')[-1]}")
    print()
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            async with session.begin():
                # 执行迁移（按依赖顺序）
                await migrate_users(session)
                await migrate_tasks(session)
                exports_data = await migrate_validated_problem_exports(session)
                await migrate_validation_records(session, exports_data)
            
            # 验证（在新事务中）
            await verify_migration(session)
        
        print("\n" + "=" * 60)
        print("🎉 数据迁移成功完成！")
        print("=" * 60)
        print("\n下一步：")
        print("  1. 运行 python reset_sequences.py 重置主键序列")
        print("  2. 运行 python verify_migration.py 进行完整验证")
        print("  3. 启动应用服务测试")
        print()
        
    except FileNotFoundError as e:
        print(f"\n❌ 文件未找到: {e}")
        print("提示：确保在备份目录中执行此脚本")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

