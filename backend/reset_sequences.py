"""
重置数据库主键序列
在迁移数据后必须执行，否则下次插入数据时可能出现主键冲突

使用方法：
    python reset_sequences.py

原因：
    当直接插入指定 ID 的数据时，PostgreSQL 的序列不会自动更新。
    例如：插入了 ID=20 的用户，但序列还停留在 1，下次插入会尝试使用 ID=1 导致冲突。
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent))


# ==================== 配置区 ====================
DATABASE_URL = "postgresql+asyncpg://mathtasks:mathtasks123@localhost:5433/mathtasks?ssl=disable"
# ================================================


async def reset_sequences():
    """重置所有表的主键序列"""
    print("=" * 60)
    print("🔄 重置主键序列")
    print("=" * 60)
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    sequences = [
        ('users_id_seq', 'users'),
        ('tasks_id_seq', 'tasks'),
        ('validated_problem_exports_id_seq', 'validated_problem_exports'),
        ('validation_records_id_seq', 'validation_records'),
        ('problems_id_seq', 'problems'),
        ('material_library_id_seq', 'material_library'),
        ('reviews_id_seq', 'reviews'),
        ('transactions_id_seq', 'transactions'),
    ]
    
    try:
        async with async_session() as session:
            for seq_name, table_name in sequences:
                # 将序列设置为表中最大 ID + 1
                query = text(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM {table_name}), 1), true)")
                result = await session.execute(query)
                new_value = result.scalar()
                print(f"  ✓ {seq_name}: 已重置为 {new_value}")
            
            await session.commit()
        
        print()
        print("=" * 60)
        print("✅ 序列重置完成！")
        print("=" * 60)
        print("\n现在可以安全地插入新数据，主键不会冲突。")
        print()
        
    except Exception as e:
        print(f"\n❌ 重置失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_sequences())

