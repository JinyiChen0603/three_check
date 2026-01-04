"""
初始化用户脚本
创建管理员和普通用户初始账户
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

from sqlalchemy import select
import bcrypt

from app.database import _get_session_local
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
        {
        "username": "zhuzhijun",
        "email": "zhuzhijun@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {
        "username": "zhaozhuoying",
        "email": "zhaozhuoying@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {
        "username": "zhuyoupeng",
        "email": "zhuyoupeng@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {
        "username": "mayuzhong",
        "email": "mayuzhong@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
                                {
        "username": "kongyusu",
        "email": "kongyusu@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {
        "username": "gaokunyi",
        "email": "gaokunyi@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {
        "username": "zhujinhong",
        "email": "zhujinhong@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {
        "username": "xieshuhong",
        "email": "xieshuhong@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {
        "username": "sunjungxuan",
        "email": "sunjungxuan@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {
        "username": "lifanghe123",
        "email": "lifanghe123@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {
        "username": "gexinlin123",
        "email": "gexinlin123@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {"username": "penghaihang",
        "email": "penghaihang@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {"username": "wangzihe",
        "email": "wangzihe@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {"username": "zhangyilian",
        "email": "zhangyilian@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {"username": "chenbosheng",
        "email": "chenbosheng@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {"username": "zuoyuxiang",
        "email": "zuoyuxiang@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
    },
        {"username": "zhouyu",
        "email": "zhouyu@mathtasks.com",
        "password": "user123",  # 生产环境请修改
        "role": UserRole.USER,
        }
]


async def create_initial_users():
    """创建初始用户"""
    print("\n[Init] Creating initial users...")
    AsyncSessionLocal = _get_session_local()
    async with AsyncSessionLocal() as session:
        try:
            for user_data in INITIAL_USERS:
                # 检查用户是否已存在
                result = await session.execute(
                    select(User).where(User.username == user_data["username"])
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    print(f"[Skip] User {user_data['username']} already exists, skipping")
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
                print(f"[OK] Created user: {user_data['username']} ({user_data['role']})")
            
            await session.commit()
            print("\n[Success] Initial users created successfully!")
            
            # 打印登录信息（动态显示）
            print("\n" + "="*50)
            print("初始账户信息：")
            print("="*50)
            
            # 动态显示管理员账户
            admin_users = [u for u in INITIAL_USERS if u["role"] == UserRole.ADMIN]
            if admin_users:
                print("\n【管理员账户】")
                for user in admin_users:
                    print(f"  用户名: {user['username']:15} | 密码: {user['password']}")
            
            # 动态显示普通用户账户
            regular_users = [u for u in INITIAL_USERS if u["role"] == UserRole.USER]
            if regular_users:
                print("\n【普通用户账户】")
                for user in regular_users:
                    print(f"  用户名: {user['username']:15} | 密码: {user['password']}")
            
            print("\n[Warning] Please change these default passwords in production!")
            print("="*50)
            
        except Exception as e:
            await session.rollback()
            print(f"[Error] Failed to create users: {e}")
            raise


async def main():
    """主函数"""
    print("[Init] Starting user initialization...")
    await create_initial_users()


if __name__ == "__main__":
    asyncio.run(main())

