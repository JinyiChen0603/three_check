"""
数据库重置脚本
用于清理所有数据并重新初始化数据库

⚠️ 警告：此脚本会删除所有数据，请谨慎使用！
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.database import Base, AsyncSessionLocal
from app.config import settings
from app.models import *  # noqa - 必须导入所有模型


async def drop_all_tables():
    """删除所有表"""
    print("🗑️  正在删除所有表...")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        # 获取所有表名
        result = await conn.execute(text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
        """))
        tables = [row[0] for row in result]
        
        if not tables:
            print("   ℹ️  数据库中没有表")
            return
        
        # 禁用外键约束检查（PostgreSQL）
        await conn.execute(text("SET session_replication_role = 'replica'"))
        
        # 删除所有表
        for table in tables:
            try:
                await conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                print(f"   ✅ 删除表: {table}")
            except Exception as e:
                print(f"   ⚠️  删除表 {table} 失败: {e}")
        
        # 恢复外键约束检查
        await conn.execute(text("SET session_replication_role = 'origin'"))
    
    await engine.dispose()
    print("✅ 所有表已删除\n")


async def run_migrations():
    """运行数据库迁移"""
    print("📦 正在运行数据库迁移...")
    
    import subprocess
    import os
    
    # 切换到项目根目录
    os.chdir(Path(__file__).parent.parent)
    
    try:
        # 运行 alembic upgrade head
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        print("✅ 数据库迁移完成\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ 迁移失败: {e}")
        print(f"错误输出: {e.stderr}")
        raise


async def create_initial_users():
    """创建初始用户"""
    print("👥 正在创建初始用户...")
    
    from sqlalchemy import select
    import bcrypt
    from app.models import User, UserRole
    
    def hash_password(password: str) -> str:
        """加密密码（使用bcrypt）"""
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    # 初始用户数据
    INITIAL_USERS = [
        # 管理员
        {
            "username": "lifanghe",
            "email": "lifanghe@mathtasks.com",
            "password": "admin123",
            "role": UserRole.ADMIN,
        },
        {
            "username": "gexinlin",
            "email": "gexinlin@mathtasks.com",
            "password": "admin123",
            "role": UserRole.ADMIN,
        },
        # 普通用户
        {
            "username": "hewenze",
            "email": "hewenze@mathtasks.com",
            "password": "user123",
            "role": UserRole.USER,
        },
        {
            "username": "chenjinyi",
            "email": "chenjinyi@mathtasks.com",
            "password": "user123",
            "role": UserRole.USER,
        },
        {
            "username": "zhuzhijun",
            "email": "zhuzhijun@mathtasks.com",
            "password": "user123",
            "role": UserRole.USER,
        },
        {
            "username": "zhaozhuoying",
            "email": "zhaozhuoying@mathtasks.com",
            "password": "user123",
            "role": UserRole.USER,
        },
    ]
    
    async with AsyncSessionLocal() as session:
        try:
            for user_data in INITIAL_USERS:
                # 检查用户是否已存在
                result = await session.execute(
                    select(User).where(User.username == user_data["username"])
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    print(f"   ⏭️  用户 {user_data['username']} 已存在，跳过")
                    continue
                
                # 创建新用户
                new_user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=hash_password(user_data["password"]),
                    role=user_data["role"],
                    balance=0.0,
                    is_active=True,
                )
                
                session.add(new_user)
                print(f"   ✅ 创建用户: {user_data['username']} ({user_data['role'].value})")
            
            await session.commit()
            print("\n✅ 初始用户创建完成！")
            
            # 打印登录信息
            print("\n" + "="*50)
            print("初始账户信息：")
            print("="*50)
            
            admin_users = [u for u in INITIAL_USERS if u["role"] == UserRole.ADMIN]
            if admin_users:
                print("\n【管理员账户】")
                for user in admin_users:
                    print(f"  用户名: {user['username']:15} | 密码: {user['password']}")
            
            regular_users = [u for u in INITIAL_USERS if u["role"] == UserRole.USER]
            if regular_users:
                print("\n【普通用户账户】")
                for user in regular_users:
                    print(f"  用户名: {user['username']:15} | 密码: {user['password']}")
            
            print("\n⚠️  生产环境请立即修改这些默认密码！")
            print("="*50 + "\n")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 创建用户失败: {e}")
            raise


async def main():
    """主函数"""
    print("=" * 60)
    print("🚀 数据库重置脚本")
    print("=" * 60)
    print("\n⚠️  警告：此操作将删除所有数据！")
    print("   包括：用户、题目、任务、评分、交易记录等所有数据\n")
    
    # 确认操作
    confirm = input("确认要继续吗？(yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ 操作已取消")
        return
    
    try:
        # 1. 删除所有表
        await drop_all_tables()
        
        # 2. 运行迁移
        await run_migrations()
        
        # 3. 创建初始用户
        await create_initial_users()
        
        print("=" * 60)
        print("🎉 数据库重置完成！")
        print("=" * 60)
        print("\n📝 下一步：")
        print("   1. 启动后端服务")
        print("   2. 使用初始账户登录")
        print("   3. 开始使用系统")
        print()
        
    except Exception as e:
        print(f"\n❌ 数据库重置失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

