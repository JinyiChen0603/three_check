"""
数据库完整初始化脚本
运行方式: cd backend && python init_database.py

⚠️ 警告：此版本使用明文密码存储，仅适用于开发/测试环境！
生产环境必须使用加密密码！
"""

import asyncio
import sys
import io
import subprocess

# 设置标准输出编码为 UTF-8（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def run_alembic_upgrade():
    """运行 Alembic 迁移"""
    print_section("步骤 1/3: 运行数据库迁移")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print("✅ 数据库迁移成功")
            print(result.stdout)
            return True
        else:
            print("❌ 数据库迁移失败")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ 运行迁移时出错: {e}")
        return False


async def init_users():
    """初始化用户"""
    print_section("步骤 2/3: 初始化用户账户")
    try:
        from sqlalchemy import select
        from app.database import _get_session_local
        from app.models import User, UserRole

        # ⚠️ 警告：明文密码存储！仅用于开发/测试！
        print("⚠️  警告：使用明文密码存储（仅开发/测试环境）")
        
        # 初始用户数据
        INITIAL_USERS = [
            # 管理员
            {"username": "lifanghe", "email": "lifanghe@mathtasks.com", "password": "admin123", "role": UserRole.ADMIN},
            {"username": "gexinlin", "email": "gexinlin@mathtasks.com", "password": "admin123", "role": UserRole.ADMIN},
            # 普通用户
            {"username": "hewenze", "email": "hewenze@mathtasks.com", "password": "user123", "role": UserRole.USER},
            {"username": "chenjinyi", "email": "chenjinyi@mathtasks.com", "password": "user123", "role": UserRole.USER},
            {"username": "zhuzhijun", "email": "zhuzhijun@mathtasks.com", "password": "user123", "role": UserRole.USER},
            {"username": "zhaozhuoying", "email": "zhaozhuoying@mathtasks.com", "password": "user123", "role": UserRole.USER},
            {"username": "zhuyoupeng", "email": "zhuyoupeng@mathtasks.com", "password": "user123", "role": UserRole.USER},
            {"username": "mayuzhong", "email": "mayuzhong@mathtasks.com", "password": "user123", "role": UserRole.USER},
            {"username": "kongyusu", "email": "kongyusu@mathtasks.com", "password": "user123", "role": UserRole.USER},
            {"username": "gaokunyi", "email": "gaokunyi@mathtasks.com", "password": "user123", "role": UserRole.USER},
            {"username": "zhujinhong", "email": "zhujinhong@mathtasks.com", "password": "user123", "role": UserRole.USER},
            {"username": "xieshuhong", "email": "xieshuhong@mathtasks.com", "password": "user123", "role": UserRole.USER},
            {"username": "sunjungxuan", "email": "sunjungxuan@mathtasks.com", "password": "user123", "role": UserRole.USER},
            {"username": "lifanghe123", "email": "lifanghe123@mathtasks.com", "password": "user123", "role": UserRole.USER},
            {"username": "gexinlin123", "email": "gexinlin123@mathtasks.com", "password": "user123", "role": UserRole.USER},
        ]

        AsyncSessionLocal = _get_session_local()
        async with AsyncSessionLocal() as session:
            created_count = 0
            skipped_count = 0
            
            for user_data in INITIAL_USERS:
                result = await session.execute(
                    select(User).where(User.username == user_data["username"])
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    skipped_count += 1
                    continue
                
                # 直接使用明文密码（不安全！）
                new_user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=user_data["password"],  # ⚠️ 明文存储
                    role=user_data["role"],
                    balance=0.0,
                    is_active=True,
                )
                
                session.add(new_user)
                created_count += 1
            
            await session.commit()
            
            print(f"✅ 用户初始化完成")
            print(f"   - 新建: {created_count} 个用户")
            print(f"   - 跳过: {skipped_count} 个已存在用户")
            
            if created_count > 0:
                print("\n📋 账户信息:")
                print("\n  【管理员账户】")
                print("    用户名: lifanghe        | 密码: admin123")
                print("    用户名: gexinlin        | 密码: admin123")
                print(f"\n  【普通用户账户】(13个)")
                print("    用户名: hewenze         | 密码: user123")
                print("    用户名: chenjinyi       | 密码: user123")
                print("    用户名: zhuzhijun       | 密码: user123")
                print("    ... 以及其他 10 个用户 (密码均为: user123)")
            
            return True
            
    except Exception as e:
        print(f"❌ 初始化用户失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def init_materials():
    """初始化资料库"""
    print_section("步骤 3/3: 初始化资料库数据")
    try:
        from sqlalchemy import select
        from app.database import _get_session_local
        from app.models import MaterialLibrary, MaterialCategory
        
        INITIAL_MATERIALS = [
            {
                "category": MaterialCategory.HIGH_SCHOOL_COMPREHENSIVE,
                "title": "高中数学联赛综合真题集",
                "description": "2010-2024年全国高中数学联赛真题及详解",
                "baidu_link": "https://pan.baidu.com/s/example1",
                "extract_code": "abc1",
            },
            {
                "category": MaterialCategory.HIGH_SCHOOL_ALGEBRA,
                "title": "高中代数专题训练",
                "description": "包含不等式、数列、函数等核心代数内容",
                "baidu_link": "https://pan.baidu.com/s/example2",
                "extract_code": "abc2",
            },
            {
                "category": MaterialCategory.HIGH_SCHOOL_GEOMETRY,
                "title": "高中几何专题训练",
                "description": "平面几何与立体几何经典题型",
                "baidu_link": "https://pan.baidu.com/s/example3",
                "extract_code": "abc3",
            },
            {
                "category": MaterialCategory.COLLEGE_COMPREHENSIVE,
                "title": "全国大学生数学竞赛真题集",
                "description": "2009-2024年数学竞赛(非数学类)真题",
                "baidu_link": "https://pan.baidu.com/s/example4",
                "extract_code": "xyz1",
            },
            {
                "category": MaterialCategory.COLLEGE_ANALYSIS,
                "title": "数学分析专题训练",
                "description": "极限、微分、积分、级数等核心内容",
                "baidu_link": "https://pan.baidu.com/s/example5",
                "extract_code": "xyz2",
            },
        ]
        
        AsyncSessionLocal = _get_session_local()
        async with AsyncSessionLocal() as session:
            created_count = 0
            skipped_count = 0
            
            for material_data in INITIAL_MATERIALS:
                result = await session.execute(
                    select(MaterialLibrary).where(
                        MaterialLibrary.title == material_data["title"]
                    )
                )
                existing_material = result.scalar_one_or_none()
                
                if existing_material:
                    skipped_count += 1
                    continue
                
                new_material = MaterialLibrary(
                    category=material_data["category"],
                    title=material_data["title"],
                    description=material_data["description"],
                    baidu_link=material_data["baidu_link"],
                    extract_code=material_data["extract_code"],
                    download_count=0,
                    is_active=True,
                )
                
                session.add(new_material)
                created_count += 1
            
            await session.commit()
            
            print(f"✅ 资料库初始化完成")
            print(f"   - 新建: {created_count} 条资料")
            print(f"   - 跳过: {skipped_count} 条已存在资料")
            
            return True
            
    except Exception as e:
        print(f"❌ 初始化资料库失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("\n" + "🚀 "*20)
    print("          数据库完整初始化脚本")
    print("          ⚠️  明文密码版本（仅开发测试）")
    print("🚀 "*20)
    
    if not run_alembic_upgrade():
        print("\n❌ 初始化失败：数据库迁移未成功")
        sys.exit(1)
    
    if not await init_users():
        print("\n❌ 初始化失败：用户创建未成功")
        sys.exit(1)
    
    if not await init_materials():
        print("\n⚠️  警告：资料库初始化失败（可以稍后手动运行）")
    
    print_section("✅ 初始化完成！")
    print("\n📌 下一步操作:")
    print("   1. 启动后端服务: uvicorn app.main:app --reload")
    print("   2. 启动前端服务: cd ../frontend && npm run dev")
    print("   3. 使用管理员账户登录测试")
    print("\n⚠️  严重警告：当前使用明文密码存储！")
    print("   生产环境前必须切换到加密密码版本！")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
