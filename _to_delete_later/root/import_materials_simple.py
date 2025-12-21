"""
简单的资料导入脚本
从 materials_data.json 读取数据并导入到数据库
"""

import json
import asyncio
import sys
import os

# 添加backend目录到path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.database import async_session_maker
from backend.app.models import MaterialLibrary, MaterialCategory
from sqlalchemy import select


async def import_from_json(json_file='materials_data.json'):
    """从JSON文件导入资料"""
    
    print("=" * 70)
    print("📚 资料库数据导入工具")
    print("=" * 70)
    
    # 读取JSON文件
    print(f"\n📖 正在读取 {json_file}...")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            materials_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 错误：找不到文件 {json_file}")
        print(f"   请确保 {json_file} 文件存在于当前目录")
        return
    except json.JSONDecodeError as e:
        print(f"❌ 错误：JSON格式不正确 - {e}")
        return
    
    print(f"✅ 成功读取 {len(materials_data)} 条资料数据")
    
    # 检查是否有未填写的数据
    has_placeholder = False
    for idx, data in enumerate(materials_data, 1):
        if '请填写' in data.get('baidu_link', '') or '请填写' in data.get('extract_code', ''):
            print(f"⚠️  第 {idx} 条数据未完整填写：{data.get('title', '未命名')}")
            has_placeholder = True
    
    if has_placeholder:
        print("\n❌ 请先填写所有的百度网盘链接和提取码！")
        return
    
    # 连接数据库并导入
    async with async_session_maker() as db:
        try:
            imported_count = 0
            updated_count = 0
            skipped_count = 0
            
            print("\n" + "-" * 70)
            print("开始导入...")
            print("-" * 70)
            
            for data in materials_data:
                title = data['title']
                category_str = data['category']
                
                # 转换category字符串为枚举
                try:
                    category = MaterialCategory[category_str.upper()]
                except KeyError:
                    print(f"⚠️  跳过：未知类别 '{category_str}' - {title}")
                    skipped_count += 1
                    continue
                
                # 检查是否已存在
                stmt = select(MaterialLibrary).where(
                    MaterialLibrary.title == title,
                    MaterialLibrary.category == category
                )
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # 更新现有数据
                    existing.description = data.get('description', '')
                    existing.baidu_link = data['baidu_link']
                    existing.extract_code = data.get('extract_code', '')
                    existing.is_active = True
                    print(f"🔄 更新: {title}")
                    updated_count += 1
                else:
                    # 创建新资料
                    material = MaterialLibrary(
                        category=category,
                        title=title,
                        description=data.get('description', ''),
                        baidu_link=data['baidu_link'],
                        extract_code=data.get('extract_code', ''),
                        download_count=0,
                        is_active=True
                    )
                    db.add(material)
                    print(f"✅ 新增: {title}")
                    imported_count += 1
            
            # 提交事务
            await db.commit()
            
            print("\n" + "=" * 70)
            print("📊 导入结果：")
            print(f"   ✅ 新增资料: {imported_count} 条")
            print(f"   🔄 更新资料: {updated_count} 条")
            print(f"   ⏭️  跳过资料: {skipped_count} 条")
            print(f"   📚 总计: {imported_count + updated_count} 条资料可用")
            print("=" * 70)
            print("\n🎉 导入完成！用户现在可以在资料库中查看和下载这些资料了。")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ 导入失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    print("\n")
    
    # 检查JSON文件是否存在
    json_file = 'materials_data.json'
    if not os.path.exists(json_file):
        print("=" * 70)
        print("❌ 错误：找不到 materials_data.json 文件")
        print("=" * 70)
        print("\n💡 使用步骤：")
        print("1. 编辑 materials_data.json 文件")
        print("2. 将所有的'请填写百度网盘链接'替换为实际的链接")
        print("3. 将所有的'请填写提取码'替换为实际的提取码")
        print("4. 运行此脚本: python import_materials_simple.py")
        print("\n示例格式：")
        print("""
{
  "category": "high_school_algebra",
  "title": "高中数学联赛-代数专题",
  "description": "代数相关题目",
  "baidu_link": "https://pan.baidu.com/s/1abc123def456",
  "extract_code": "ab12"
}
        """)
        sys.exit(1)
    
    # 运行导入
    try:
        asyncio.run(import_from_json(json_file))
    except KeyboardInterrupt:
        print("\n\n⚠️  导入被用户中断")
        sys.exit(1)

