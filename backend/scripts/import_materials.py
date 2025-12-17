"""
资料库数据导入脚本
用于批量导入百度网盘资料链接
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker
from app.models import MaterialLibrary, MaterialCategory


# 资料数据 - 请填写12个资料的信息
MATERIALS_DATA = [
    # 高中数学联赛 - 综合
    {
        "category": MaterialCategory.HIGH_SCHOOL_COMPREHENSIVE,
        "title": "高中数学联赛综合资料",
        "description": "包含历年高中数学联赛综合试题及解析",
        "baidu_link": "https://pan.baidu.com/s/xxxxxxxxxx",  # 请替换为实际链接
        "extract_code": "xxxx"  # 请替换为实际提取码
    },
    
    # 大学数学竞赛 - 综合
    {
        "category": MaterialCategory.COLLEGE_COMPREHENSIVE,
        "title": "大学数学竞赛综合资料",
        "description": "包含历年大学数学竞赛综合试题及解析",
        "baidu_link": "https://pan.baidu.com/s/xxxxxxxxxx",
        "extract_code": "xxxx"
    },
    
    # 高中数学联赛 - 代数
    {
        "category": MaterialCategory.HIGH_SCHOOL_ALGEBRA,
        "title": "高中数学联赛-代数专题",
        "description": "代数相关题目，包括方程、不等式、函数等",
        "baidu_link": "https://pan.baidu.com/s/xxxxxxxxxx",
        "extract_code": "xxxx"
    },
    
    # 高中数学联赛 - 几何
    {
        "category": MaterialCategory.HIGH_SCHOOL_GEOMETRY,
        "title": "高中数学联赛-几何专题",
        "description": "几何相关题目，包括平面几何、立体几何等",
        "baidu_link": "https://pan.baidu.com/s/xxxxxxxxxx",
        "extract_code": "xxxx"
    },
    
    # 高中数学联赛 - 数论
    {
        "category": MaterialCategory.HIGH_SCHOOL_NUMBER_THEORY,
        "title": "高中数学联赛-数论专题",
        "description": "数论相关题目，包括整除、同余、素数等",
        "baidu_link": "https://pan.baidu.com/s/xxxxxxxxxx",
        "extract_code": "xxxx"
    },
    
    # 高中数学联赛 - 组合
    {
        "category": MaterialCategory.HIGH_SCHOOL_COMBINATORICS,
        "title": "高中数学联赛-组合专题",
        "description": "组合数学相关题目，包括排列组合、概率等",
        "baidu_link": "https://pan.baidu.com/s/xxxxxxxxxx",
        "extract_code": "xxxx"
    },
    
    # 大学数学竞赛 - 代数
    {
        "category": MaterialCategory.COLLEGE_ALGEBRA,
        "title": "大学数学竞赛-代数专题",
        "description": "高等代数相关题目，包括线性代数、抽象代数等",
        "baidu_link": "https://pan.baidu.com/s/xxxxxxxxxx",
        "extract_code": "xxxx"
    },
    
    # 大学数学竞赛 - 数论
    {
        "category": MaterialCategory.COLLEGE_NUMBER_THEORY,
        "title": "大学数学竞赛-数论专题",
        "description": "高等数论相关题目",
        "baidu_link": "https://pan.baidu.com/s/xxxxxxxxxx",
        "extract_code": "xxxx"
    },
    
    # 大学数学竞赛 - 分析和方程
    {
        "category": MaterialCategory.COLLEGE_ANALYSIS,
        "title": "大学数学竞赛-分析和方程专题",
        "description": "数学分析、微分方程相关题目",
        "baidu_link": "https://pan.baidu.com/s/xxxxxxxxxx",
        "extract_code": "xxxx"
    },
    
    # 大学数学竞赛 - 组合和概率
    {
        "category": MaterialCategory.COLLEGE_COMBINATORICS,
        "title": "大学数学竞赛-组合和概率专题",
        "description": "组合数学、概率论相关题目",
        "baidu_link": "https://pan.baidu.com/s/xxxxxxxxxx",
        "extract_code": "xxxx"
    },
    
    # 大学数学竞赛 - 几何和拓扑
    {
        "category": MaterialCategory.COLLEGE_GEOMETRY,
        "title": "大学数学竞赛-几何和拓扑专题",
        "description": "高等几何、拓扑学相关题目",
        "baidu_link": "https://pan.baidu.com/s/xxxxxxxxxx",
        "extract_code": "xxxx"
    },
    
    # 大学数学竞赛 - 最优化方法
    {
        "category": MaterialCategory.COLLEGE_OPTIMIZATION,
        "title": "大学数学竞赛-最优化方法专题",
        "description": "最优化理论与方法相关题目",
        "baidu_link": "https://pan.baidu.com/s/xxxxxxxxxx",
        "extract_code": "xxxx"
    },
]


async def clear_existing_materials(db: AsyncSession):
    """清空现有资料（可选）"""
    print("⚠️  是否清空现有资料？(y/n): ", end='')
    # 这里简化处理，实际使用时可以取消注释
    # choice = input().strip().lower()
    # if choice == 'y':
    #     await db.execute("DELETE FROM material_library")
    #     await db.commit()
    #     print("✅ 已清空现有资料")
    pass


async def import_materials():
    """导入资料数据"""
    print("=" * 60)
    print("📚 资料库数据导入")
    print("=" * 60)
    
    async with async_session_maker() as db:
        try:
            # 可选：清空现有数据
            # await clear_existing_materials(db)
            
            # 导入新数据
            imported_count = 0
            skipped_count = 0
            
            for data in MATERIALS_DATA:
                # 检查是否已存在（根据标题和类别）
                from sqlalchemy import select
                stmt = select(MaterialLibrary).where(
                    MaterialLibrary.title == data['title'],
                    MaterialLibrary.category == data['category']
                )
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    print(f"⏭️  跳过已存在: {data['title']}")
                    skipped_count += 1
                    continue
                
                # 创建新资料
                material = MaterialLibrary(
                    category=data['category'],
                    title=data['title'],
                    description=data['description'],
                    baidu_link=data['baidu_link'],
                    extract_code=data['extract_code'],
                    download_count=0,
                    is_active=True
                )
                
                db.add(material)
                print(f"✅ 导入: {data['title']}")
                imported_count += 1
            
            # 提交事务
            await db.commit()
            
            print("\n" + "=" * 60)
            print(f"📊 导入完成！")
            print(f"   成功导入: {imported_count} 条")
            print(f"   跳过重复: {skipped_count} 条")
            print("=" * 60)
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ 导入失败: {str(e)}")
            raise


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("📚 资料库批量导入工具")
    print("=" * 60)
    print("\n💡 使用说明：")
    print("1. 编辑本文件，填写 MATERIALS_DATA 中的链接和提取码")
    print("2. 运行命令: python scripts/import_materials.py")
    print("3. 或在容器中运行: docker exec mathtasks-api python scripts/import_materials.py")
    print("\n⚠️  注意：请确保所有链接和提取码都已填写！")
    print("=" * 60)
    print()
    
    # 检查是否所有数据都已填写
    has_placeholder = False
    for data in MATERIALS_DATA:
        if 'xxxxxxxxxx' in data['baidu_link'] or data['extract_code'] == 'xxxx':
            has_placeholder = True
            break
    
    if has_placeholder:
        print("⚠️  检测到未填写的占位符（xxxxxxxxxx 或 xxxx）")
        print("📝 请先编辑本文件，填写实际的百度网盘链接和提取码")
        print()
        print("按回车键查看需要填写的数据格式...")
        input()
        print("\n示例格式：")
        print("""
{
    "category": MaterialCategory.HIGH_SCHOOL_ALGEBRA,
    "title": "高中数学联赛-代数专题",
    "description": "代数相关题目，包括方程、不等式、函数等",
    "baidu_link": "https://pan.baidu.com/s/1abc123def456",  # 实际的百度网盘链接
    "extract_code": "ab12"  # 实际的提取码
}
        """)
        sys.exit(0)
    
    # 运行导入
    asyncio.run(import_materials())

