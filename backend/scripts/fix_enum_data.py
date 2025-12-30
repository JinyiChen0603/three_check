#!/usr/bin/env python3
"""
修复数据库中的枚举数据
将旧的大写枚举值转换为小写
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from sqlalchemy import text


async def fix_enum_data():
    """修复数据库中的枚举值"""
    print("🔧 开始修复枚举数据...")
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. 修复 users 表的 role 字段
            print("📝 修复 users.role 字段...")
            result = await session.execute(text(
                "UPDATE users SET role = 'admin' WHERE role::text = 'ADMIN'"
            ))
            print(f"   更新了 {result.rowcount} 个 ADMIN 角色")
            
            result = await session.execute(text(
                "UPDATE users SET role = 'user' WHERE role::text = 'USER'"
            ))
            print(f"   更新了 {result.rowcount} 个 USER 角色")
            
            # 提交更改
            await session.commit()
            print("✅ 枚举数据修复完成！")
            
        except Exception as e:
            print(f"❌ 修复失败: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(fix_enum_data())

