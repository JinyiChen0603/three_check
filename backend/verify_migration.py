"""
完整的迁移验证脚本
检查数据完整性、外键关系、新字段等

使用方法：
    python verify_migration.py
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, text

sys.path.insert(0, str(Path(__file__).parent))

from app.models import (
    User, Task, ValidatedProblemExport, ValidationRecord,
    Problem, MaterialLibrary, Review, Transaction
)


# ==================== 配置区 ====================
DATABASE_URL = "postgresql+asyncpg://mathtasks:mathtasks123@localhost:5433/mathtasks?ssl=disable"
# ================================================


async def verify():
    """执行完整验证"""
    print("=" * 60)
    print("🔍 数据库迁移验证")
    print("=" * 60)
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    all_checks_passed = True
    
    try:
        async with async_session() as session:
            # 1. 记录数检查
            print("\n📊 1. 记录数检查")
            print("-" * 60)
            
            expected_counts = {
                'users': 20,
                'tasks': 18,
                'validated_problem_exports': 5,
                'validation_records': 15,
            }
            
            tables = [
                ('users', User, 20),
                ('tasks', Task, 18),
                ('validated_problem_exports', ValidatedProblemExport, 5),
                ('validation_records', ValidationRecord, 15),
                ('problems', Problem, 0),
                ('material_library', MaterialLibrary, 0),
                ('reviews', Review, 0),
                ('transactions', Transaction, 0),
            ]
            
            for table_name, model, expected in tables:
                result = await session.execute(select(func.count()).select_from(model))
                count = result.scalar()
                status = "✓" if count == expected else "✗"
                print(f"  {status} {table_name}: {count} 条 (预期 {expected})")
                if count != expected:
                    all_checks_passed = False
            
            # 2. 外键完整性检查
            print("\n🔗 2. 外键完整性检查")
            print("-" * 60)
            
            # 检查 validated_problem_exports.user_id
            result = await session.execute(
                select(func.count())
                .select_from(ValidatedProblemExport)
                .outerjoin(User, ValidatedProblemExport.user_id == User.id)
                .where(User.id.is_(None))
            )
            orphaned_count = result.scalar()
            status = "✓" if orphaned_count == 0 else "✗"
            print(f"  {status} validated_problem_exports.user_id: {orphaned_count} 条孤立记录")
            if orphaned_count > 0:
                all_checks_passed = False
            
            # 检查 tasks.user_id
            result = await session.execute(
                select(func.count())
                .select_from(Task)
                .outerjoin(User, Task.user_id == User.id)
                .where(User.id.is_(None))
            )
            orphaned_count = result.scalar()
            status = "✓" if orphaned_count == 0 else "✗"
            print(f"  {status} tasks.user_id: {orphaned_count} 条孤立记录")
            if orphaned_count > 0:
                all_checks_passed = False
            
            # 检查 validation_records.validated_problem_id
            result = await session.execute(
                select(func.count())
                .select_from(ValidationRecord)
                .outerjoin(ValidatedProblemExport, ValidationRecord.validated_problem_id == ValidatedProblemExport.id)
                .where(ValidatedProblemExport.id.is_(None))
            )
            orphaned_count = result.scalar()
            status = "✓" if orphaned_count == 0 else "✗"
            print(f"  {status} validation_records.validated_problem_id: {orphaned_count} 条孤立记录")
            if orphaned_count > 0:
                all_checks_passed = False
            
            # 3. 新字段检查
            print("\n🆕 3. 新增字段检查")
            print("-" * 60)
            
            result = await session.execute(
                select(ValidatedProblemExport).limit(1)
            )
            sample = result.scalar_one_or_none()
            
            if sample:
                checks = [
                    ('review_count', sample.review_count == 0),
                    ('avg_innovation_score', sample.avg_innovation_score is None),
                    ('avg_rigor_score', sample.avg_rigor_score is None),
                    ('admin_review_status', sample.admin_review_status.value == 'pending'),
                    ('admin_reviewer_id', sample.admin_reviewer_id is None),
                    ('admin_review_note', sample.admin_review_note is None),
                    ('admin_reviewed_at', sample.admin_reviewed_at is None),
                ]
                
                for field_name, is_correct in checks:
                    status = "✓" if is_correct else "✗"
                    print(f"  {status} {field_name}: {'默认值正确' if is_correct else '默认值错误'}")
                    if not is_correct:
                        all_checks_passed = False
            
            # 4. validation_records 分布检查
            print("\n📋 4. 验证记录分布检查")
            print("-" * 60)
            
            result = await session.execute(
                select(
                    ValidationRecord.validation_type,
                    func.count(ValidationRecord.id).label('count')
                )
                .group_by(ValidationRecord.validation_type)
                .order_by(ValidationRecord.validation_type)
            )
            
            expected_distribution = {
                'difficulty': 5,
                'originality': 5,
                'rigor': 5,
            }
            
            for row in result:
                expected = expected_distribution.get(row.validation_type, 0)
                status = "✓" if row.count == expected else "✗"
                print(f"  {status} {row.validation_type}: {row.count} 条 (预期 {expected})")
                if row.count != expected:
                    all_checks_passed = False
            
            # 5. 主键序列检查
            print("\n🔢 5. 主键序列检查")
            print("-" * 60)
            
            sequences = [
                ('users_id_seq', User),
                ('tasks_id_seq', Task),
                ('validated_problem_exports_id_seq', ValidatedProblemExport),
                ('validation_records_id_seq', ValidationRecord),
            ]
            
            for seq_name, model in sequences:
                # 获取序列当前值
                result = await session.execute(text(f"SELECT last_value FROM {seq_name}"))
                seq_value = result.scalar()
                
                # 获取表中最大 ID
                result = await session.execute(select(func.max(model.id)))
                max_id = result.scalar() or 0
                
                status = "✓" if seq_value >= max_id else "⚠️"
                print(f"  {status} {seq_name}: {seq_value} (表最大ID: {max_id})")
                if seq_value < max_id:
                    print(f"      警告：序列值小于最大ID，可能导致插入冲突！")
                    print(f"      请运行: python reset_sequences.py")
                    all_checks_passed = False
            
            # 6. 枚举值检查
            print("\n🏷️  6. 枚举值检查")
            print("-" * 60)
            
            # 检查 User.role
            result = await session.execute(
                select(User.role, func.count()).group_by(User.role)
            )
            print(f"  ✓ User.role 枚举值：")
            for row in result:
                print(f"      - {row[0]}: {row[1]} 条")
            
            # 检查 Task.status
            result = await session.execute(
                select(Task.status, func.count()).group_by(Task.status)
            )
            print(f"  ✓ Task.status 枚举值：")
            for row in result:
                print(f"      - {row[0]}: {row[1]} 条")
            
        print("\n" + "=" * 60)
        if all_checks_passed:
            print("✅ 所有检查通过！数据迁移成功！")
        else:
            print("⚠️  部分检查未通过，请检查上述问题")
        print("=" * 60)
        print()
        
        return all_checks_passed
        
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    result = asyncio.run(verify())
    sys.exit(0 if result else 1)

