"""
资料库管理API
提供12个类别的资料查看和下载
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.models import MaterialLibrary, MaterialCategory, User
from app.api.deps import get_current_user


router = APIRouter()


# ==================== Pydantic 模型 ====================

class MaterialResponse(BaseModel):
    """资料响应模型"""
    id: int
    category: str
    category_display: str
    title: str
    description: Optional[str]
    baidu_link: str
    extract_code: Optional[str]
    download_count: int
    
    class Config:
        from_attributes = True


class CategorySummary(BaseModel):
    """类别汇总模型"""
    category: str
    category_display: str
    material_count: int
    total_downloads: int


# 类别显示名称映射
CATEGORY_DISPLAY_NAMES = {
    "high_school_comprehensive": "高中数学联赛综合",
    "college_comprehensive": "大学数学竞赛综合",
    "high_school_algebra": "高中数学联赛 - 代数",
    "high_school_geometry": "高中数学联赛 - 几何",
    "high_school_number_theory": "高中数学联赛 - 数论",
    "high_school_combinatorics": "高中数学联赛 - 组合",
    "college_algebra": "大学数学竞赛 - 代数",
    "college_number_theory": "大学数学竞赛 - 数论",
    "college_analysis": "大学数学竞赛 - 分析和方程",
    "college_combinatorics": "大学数学竞赛 - 组合和概率",
    "college_geometry": "大学数学竞赛 - 几何和拓扑",
    "college_optimization": "大学数学竞赛 - 最优化方法",
}


# ==================== API 路由 ====================

@router.get("/categories", response_model=List[CategorySummary], summary="获取所有类别汇总")
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有资料库类别的汇总信息
    
    返回每个类别的资料数量和总下载次数
    """
    # 按类别分组统计
    result = await db.execute(
        select(
            MaterialLibrary.category,
            func.count(MaterialLibrary.id).label("material_count"),
            func.sum(MaterialLibrary.download_count).label("total_downloads")
        )
        .where(MaterialLibrary.is_active == True)
        .group_by(MaterialLibrary.category)
    )
    
    categories = result.all()
    
    return [
        {
            "category": cat.category,
            "category_display": CATEGORY_DISPLAY_NAMES.get(cat.category, cat.category),
            "material_count": cat.material_count,
            "total_downloads": cat.total_downloads or 0
        }
        for cat in categories
    ]


@router.get("/list", response_model=List[MaterialResponse], summary="获取资料列表")
async def list_materials(
    category: Optional[str] = Query(None, description="按类别筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取资料库列表
    
    - **category**: 可选，按类别筛选
    - **skip**: 分页偏移
    - **limit**: 每页数量（最多100）
    """
    query = select(MaterialLibrary).where(MaterialLibrary.is_active == True)
    
    # 按类别筛选
    if category:
        try:
            category_enum = MaterialCategory(category)
            query = query.where(MaterialLibrary.category == category_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的类别: {category}"
            )
    
    # 分页
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    materials = result.scalars().all()
    
    return [
        {
            "id": m.id,
            "category": m.category,
            "category_display": CATEGORY_DISPLAY_NAMES.get(m.category, m.category),
            "title": m.title,
            "description": m.description,
            "baidu_link": m.baidu_link,
            "extract_code": m.extract_code,
            "download_count": m.download_count
        }
        for m in materials
    ]


@router.get("/{material_id}", response_model=MaterialResponse, summary="获取资料详情")
async def get_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定资料的详细信息
    
    - **material_id**: 资料ID
    """
    result = await db.execute(
        select(MaterialLibrary).where(
            MaterialLibrary.id == material_id,
            MaterialLibrary.is_active == True
        )
    )
    material = result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="资料不存在"
        )
    
    return {
        "id": material.id,
        "category": material.category,
        "category_display": CATEGORY_DISPLAY_NAMES.get(material.category, material.category),
        "title": material.title,
        "description": material.description,
        "baidu_link": material.baidu_link,
        "extract_code": material.extract_code,
        "download_count": material.download_count
    }


@router.post("/{material_id}/download", summary="记录资料下载")
async def record_download(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    记录资料下载（增加下载计数）
    
    - **material_id**: 资料ID
    """
    result = await db.execute(
        select(MaterialLibrary).where(
            MaterialLibrary.id == material_id,
            MaterialLibrary.is_active == True
        )
    )
    material = result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="资料不存在"
        )
    
    # 增加下载计数
    material.download_count += 1
    await db.commit()
    
    return {
        "success": True,
        "message": "下载记录成功",
        "material": {
            "id": material.id,
            "title": material.title,
            "baidu_link": material.baidu_link,
            "extract_code": material.extract_code,
            "download_count": material.download_count
        }
    }


@router.get("/guide/info", summary="获取资料库使用指南")
async def get_guide(
    current_user: User = Depends(get_current_user)
):
    """
    获取资料库使用指南和注意事项
    """
    return {
        "title": "资料库使用指南",
        "description": "欢迎使用MathTasks资料库！这里提供了丰富的数学竞赛资料供您出题参考。",
        "categories": [
            {
                "name": "大类",
                "items": [
                    "高中数学联赛综合",
                    "大学数学竞赛综合"
                ]
            },
            {
                "name": "高中数学联赛 - 小类",
                "items": [
                    "代数",
                    "几何",
                    "数论",
                    "组合"
                ]
            },
            {
                "name": "大学数学竞赛 - 小类",
                "items": [
                    "代数",
                    "数论",
                    "分析和方程",
                    "组合和概率",
                    "几何和拓扑",
                    "最优化方法"
                ]
            }
        ],
        "requirements": [
            "我们需要有明确答案的解答题",
            "不要证明题、判断题或选择题",
            "可以通过修改把其他题型改为解答题",
            "题目必须有明确答案"
        ],
        "tips": [
            "可以从资料库下载资料作为母题",
            "也可以上传自己的题目",
            "使用OCR工具可以快速识别图片中的题目",
            "每个母题最多可以变形10次"
        ]
    }

