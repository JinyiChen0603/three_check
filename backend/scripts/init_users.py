"""
初始化用户脚本
创建管理员和普通用户初始账户
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
import bcrypt

from app.database import AsyncSessionLocal
from app.models import User, UserRole


def hash_password(password: str) -> str:
    """加密密码（使用bcrypt）"""
    # bcrypt限制72字节，简化密码处理
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


# 初始用户数据
INITIAL_USERS = [
    # 管理员
    {
        "username": "lifanghe",
        "email": "lifanghe@mathtasks.com",
        "password": "admin123",  # 生产环境请修改
        "role": UserRole.ADMIN,
    },
    {
        "username": "gexinlin",
        "email": "gexinlin@mathtasks.com",
        "password": "admin123",  # 生产环境请修改
        "role": UserRole.ADMIN,
    },
    # 普通用户
    {
        "username": "hewenze",
        "email": "hewenze@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
    {
        "username": "chenjinyi",
        "email": "chenjinyi@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
]


async def create_initial_users():
    """创建初始用户"""
    async with AsyncSessionLocal() as session:
        try:
            for user_data in INITIAL_USERS:
                # 检查用户是否已存在
                result = await session.execute(
                    select(User).where(User.username == user_data["username"])
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    print(f"⏭️  用户 {user_data['username']} 已存在，跳过")
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
                print(f"✅ 创建用户: {user_data['username']} ({user_data['role'].value})")
            
            await session.commit()
            print("\n🎉 初始用户创建完成！")
            
            # 打印登录信息
            print("\n" + "="*50)
            print("初始账户信息：")
            print("="*50)
            print("\n【管理员账户】")
            print("  用户名: lifanghe  | 密码: admin123")
            print("  用户名: gexinlin  | 密码: admin123")
            print("\n【普通用户账户】")
            print("  用户名: hewenze   | 密码: user123")
            print("  用户名: chenjinyi | 密码: user123")
            print("\n⚠️  生产环境请立即修改这些默认密码！")
            print("="*50)
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 创建用户失败: {e}")
            raise


async def main():
    """主函数"""
    print("🚀 开始初始化用户...")
    await create_initial_users()


if __name__ == "__main__":
    asyncio.run(main())

