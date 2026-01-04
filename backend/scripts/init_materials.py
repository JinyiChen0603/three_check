"""
初始化资料库脚本
创建12个类别的资料库数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import MaterialLibrary, MaterialCategory


# 12个类别的资料库数据
INITIAL_MATERIALS = [
    # 大类 - 高中数学联赛综合
    {
        "category": MaterialCategory.HIGH_SCHOOL_COMPREHENSIVE,
        "title": "高中数学联赛综合资料包",
        "description": "包含历年高中数学联赛真题及详解，涵盖代数、几何、数论、组合等各个模块",
        "baidu_link": "https://pan.baidu.com/s/example_high_school_comp",
        "extract_code": "hs01",
    },
    
    # 大类 - 大学数学竞赛综合
    {
        "category": MaterialCategory.COLLEGE_COMPREHENSIVE,
        "title": "大学数学竞赛综合资料包",
        "description": "包含全国大学生数学竞赛历年真题及详解，涵盖所有模块",
        "baidu_link": "https://pan.baidu.com/s/example_college_comp",
        "extract_code": "cl01",
    },
    
    # 高中数学联赛 - 代数
    {
        "category": MaterialCategory.HIGH_SCHOOL_ALGEBRA,
        "title": "高中数学联赛 - 代数专题",
        "description": "包括函数、方程、不等式、数列等代数问题的系统训练资料",
        "baidu_link": "https://pan.baidu.com/s/example_hs_algebra",
        "extract_code": "alg1",
    },
    
    # 高中数学联赛 - 几何
    {
        "category": MaterialCategory.HIGH_SCHOOL_GEOMETRY,
        "title": "高中数学联赛 - 几何专题",
        "description": "平面几何、解析几何、立体几何等几何问题专项训练",
        "baidu_link": "https://pan.baidu.com/s/example_hs_geometry",
        "extract_code": "geo1",
    },
    
    # 高中数学联赛 - 数论
    {
        "category": MaterialCategory.HIGH_SCHOOL_NUMBER_THEORY,
        "title": "高中数学联赛 - 数论专题",
        "description": "整除、同余、不定方程等数论问题的系统训练",
        "baidu_link": "https://pan.baidu.com/s/example_hs_number",
        "extract_code": "num1",
    },
    
    # 高中数学联赛 - 组合
    {
        "category": MaterialCategory.HIGH_SCHOOL_COMBINATORICS,
        "title": "高中数学联赛 - 组合专题",
        "description": "排列组合、图论、组合计数等组合问题专项训练",
        "baidu_link": "https://pan.baidu.com/s/example_hs_combo",
        "extract_code": "cmb1",
    },
    
    # 大学数学竞赛 - 代数
    {
        "category": MaterialCategory.COLLEGE_ALGEBRA,
        "title": "大学数学竞赛 - 代数专题",
        "description": "线性代数、抽象代数、群论等高等代数问题训练",
        "baidu_link": "https://pan.baidu.com/s/example_cl_algebra",
        "extract_code": "alg2",
    },
    
    # 大学数学竞赛 - 数论
    {
        "category": MaterialCategory.COLLEGE_NUMBER_THEORY,
        "title": "大学数学竞赛 - 数论专题",
        "description": "初等数论、解析数论等大学数论问题系统训练",
        "baidu_link": "https://pan.baidu.com/s/example_cl_number",
        "extract_code": "num2",
    },
    
    # 大学数学竞赛 - 分析和方程
    {
        "category": MaterialCategory.COLLEGE_ANALYSIS,
        "title": "大学数学竞赛 - 分析和方程",
        "description": "数学分析、实分析、复分析、微分方程等问题专项训练",
        "baidu_link": "https://pan.baidu.com/s/example_cl_analysis",
        "extract_code": "ana2",
    },
    
    # 大学数学竞赛 - 组合和概率
    {
        "category": MaterialCategory.COLLEGE_COMBINATORICS,
        "title": "大学数学竞赛 - 组合和概率",
        "description": "组合数学、图论、概率论、随机过程等问题系统训练",
        "baidu_link": "https://pan.baidu.com/s/example_cl_combo",
        "extract_code": "cmb2",
    },
    
    # 大学数学竞赛 - 几何和拓扑
    {
        "category": MaterialCategory.COLLEGE_GEOMETRY,
        "title": "大学数学竞赛 - 几何和拓扑",
        "description": "微分几何、拓扑学、代数拓扑等高等几何问题训练",
        "baidu_link": "https://pan.baidu.com/s/example_cl_geometry",
        "extract_code": "geo2",
    },
    
    # 大学数学竞赛 - 最优化方法
    {
        "category": MaterialCategory.COLLEGE_OPTIMIZATION,
        "title": "大学数学竞赛 - 最优化方法",
        "description": "线性规划、非线性优化、凸优化等最优化问题系统训练",
        "baidu_link": "https://pan.baidu.com/s/example_cl_optimization",
        "extract_code": "opt2",
    },
]


async def create_initial_materials():
    """创建初始资料库数据"""
    async with AsyncSessionLocal() as session:
        try:
            for material_data in INITIAL_MATERIALS:
                # 使用 title 检查资料是否已存在（避免枚举比较问题）
                result = await session.execute(
                    select(MaterialLibrary).where(
                        MaterialLibrary.title == material_data["title"]
                    )
                )
                existing_material = result.scalar_one_or_none()
                
                if existing_material:
                    print(f"⏭️  资料 {material_data['title']} 已存在，跳过")
                    continue
                
                # 创建新资料（使用字符串值）
                new_material = MaterialLibrary(
                    category=material_data["category"],
                    title=material_data["title"],
                    description=material_data["description"],
                    baidu_link=material_data["baidu_link"],
                    extract_code=material_data["extract_code"],
                    is_active=True,
                )
                
                session.add(new_material)
                print(f"✅ 创建资料: {material_data['title']} ({material_data['category']})")
            
            await session.commit()
            print("\n🎉 资料库初始化完成！")
            
            # 打印资料库信息
            print("\n" + "="*80)
            print("资料库类别清单（共12个）：")
            print("="*80)
            print("\n【大类】")
            print("  1. 高中数学联赛综合")
            print("  2. 大学数学竞赛综合")
            print("\n【高中数学联赛 - 小类】")
            print("  3. 代数")
            print("  4. 几何")
            print("  5. 数论")
            print("  6. 组合")
            print("\n【大学数学竞赛 - 小类】")
            print("  7. 代数")
            print("  8. 数论")
            print("  9. 分析和方程")
            print("  10. 组合和概率")
            print("  11. 几何和拓扑")
            print("  12. 最优化方法")
            print("\n💡 用户可以从以上类别下载资料，辅助出题")
            print("="*80)
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 创建资料失败: {e}")
            raise


async def main():
    """主函数"""
    print("🚀 开始初始化资料库...")
    await create_initial_materials()


if __name__ == "__main__":
    asyncio.run(main())

