"""
变体题目管理 API
处理变体的保存、查看和提交验证
"""

from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.models import (
    User, ValidatedProblemExport, ValidatedProblemSourceType,
    Task, TaskType, TaskStatus
)
from app.api.deps import get_current_user


router = APIRouter()


# ==================== Pydantic 模型 ====================

class SaveVariantRequest(BaseModel):
    """保存变体请求"""
    content: str
    answer: str
    explanation: str


class VariantDraftResponse(BaseModel):
    """变体草稿响应"""
    id: int
    content: str
    answer: str
    explanation: str
    created_at: str


# ==================== API 路由 ====================

@router.post("/save-draft", summary="保存变体为草稿")
async def save_variant_as_draft(
    content: str = Form(...),
    answer: str = Form(...),
    explanation: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    保存变体为草稿
    - 不执行质检
    - 不关联任务
    - source_type='variant', task_id=NULL
    """
    validated_problem = ValidatedProblemExport(
        user_id=current_user.id,
        task_id=None,  # 草稿不关联任务
        content=content,
        answer=answer,
        explanation=explanation,
        source_type=ValidatedProblemSourceType.VARIANT,
        originality_check=None,  # 草稿暂不质检
        rigor_check=None
    )
    
    db.add(validated_problem)
    await db.commit()
    await db.refresh(validated_problem)
    
    return {
        "success": True,
        "id": validated_problem.id,
        "message": "变体已保存"
    }


@router.post("/save-batch", summary="批量保存变体")
async def save_variants_batch(
    variants: List[SaveVariantRequest],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量保存多个变体为草稿"""
    saved_ids = []
    
    for variant in variants:
        validated_problem = ValidatedProblemExport(
            user_id=current_user.id,
            task_id=None,
            content=variant.content,
            answer=variant.answer,
            explanation=variant.explanation,
            source_type=ValidatedProblemSourceType.VARIANT,
            originality_check=None,
            rigor_check=None
        )
        db.add(validated_problem)
        await db.flush()  # 获取ID
        saved_ids.append(validated_problem.id)
    
    await db.commit()
    
    return {
        "success": True,
        "count": len(saved_ids),
        "ids": saved_ids,
        "message": f"已保存 {len(saved_ids)} 个变体"
    }


@router.get("/my-variants", summary="获取我的变体草稿列表")
async def get_my_variant_drafts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取我的变体草稿列表
    筛选条件：source_type='variant' AND task_id IS NULL
    """
    result = await db.execute(
        select(ValidatedProblemExport).where(
            ValidatedProblemExport.user_id == current_user.id,
            ValidatedProblemExport.source_type == ValidatedProblemSourceType.VARIANT,
            ValidatedProblemExport.task_id.is_(None)  # 未关联任务的
        ).order_by(ValidatedProblemExport.created_at.desc())
    )
    drafts = result.scalars().all()
    
    return {
        "total": len(drafts),
        "variants": [
            {
                "id": d.id,
                "content": d.content,
                "answer": d.answer,
                "explanation": d.explanation,
                "created_at": d.created_at.isoformat()
            }
            for d in drafts
        ]
    }


@router.get("/variant/{variant_id}", summary="获取单个变体详情")
async def get_variant_detail(
    variant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单个变体的详细信息"""
    result = await db.execute(
        select(ValidatedProblemExport).where(
            ValidatedProblemExport.id == variant_id,
            ValidatedProblemExport.user_id == current_user.id,
            ValidatedProblemExport.source_type == ValidatedProblemSourceType.VARIANT
        )
    )
    variant = result.scalar_one_or_none()
    
    if not variant:
        raise HTTPException(404, "变体不存在")
    
    return {
        "id": variant.id,
        "content": variant.content,
        "answer": variant.answer,
        "explanation": variant.explanation,
        "task_id": variant.task_id,
        "created_at": variant.created_at.isoformat()
    }


@router.delete("/variant/{variant_id}", summary="删除变体草稿")
async def delete_variant_draft(
    variant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除变体草稿
    只能删除自己的、未关联任务的变体
    """
    result = await db.execute(
        select(ValidatedProblemExport).where(
            ValidatedProblemExport.id == variant_id,
            ValidatedProblemExport.user_id == current_user.id,
            ValidatedProblemExport.source_type == ValidatedProblemSourceType.VARIANT,
            ValidatedProblemExport.task_id.is_(None)  # 只能删除未验证的
        )
    )
    variant = result.scalar_one_or_none()
    
    if not variant:
        raise HTTPException(404, "变体不存在或已提交验证")
    
    await db.delete(variant)
    await db.commit()
    
    return {"success": True, "message": "变体已删除"}


@router.post("/variant/{variant_id}/prepare-validate", summary="准备验证变体")
async def prepare_validate_variant(
    variant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    准备验证变体
    - 检查用户是否有进行中的出题任务
    - 返回变体内容，供前端跳转到验证页面
    
    注意：这个接口只是准备数据，实际的质检和关联任务在"题目验证导出"页面的保存接口完成
    """
    # 1. 检查变体是否存在
    result = await db.execute(
        select(ValidatedProblemExport).where(
            ValidatedProblemExport.id == variant_id,
            ValidatedProblemExport.user_id == current_user.id,
            ValidatedProblemExport.source_type == ValidatedProblemSourceType.VARIANT,
            ValidatedProblemExport.task_id.is_(None)
        )
    )
    variant = result.scalar_one_or_none()
    
    if not variant:
        raise HTTPException(404, "变体不存在或已提交验证")
    
    # 2. 检查用户是否有进行中的出题任务
    now = datetime.utcnow()
    task_result = await db.execute(
        select(Task).where(
            Task.user_id == current_user.id,
            Task.task_type == TaskType.CREATE_PROBLEM,
            Task.status == TaskStatus.IN_PROGRESS
        ).order_by(Task.claimed_at.asc())
    )
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=400,
            detail="请先在任务管理中领取出题任务"
        )
    
    # 检查任务是否过期
    if task.expires_at and now > task.expires_at:
        task.status = TaskStatus.TIMEOUT
        await db.commit()
        raise HTTPException(
            status_code=400,
            detail="任务已超时，请重新领取任务"
        )
    
    # 3. 检查当前任务已保存的题目数量
    saved_count_result = await db.execute(
        select(func.count(ValidatedProblemExport.id)).where(
            ValidatedProblemExport.task_id == task.id
        )
    )
    saved_count = saved_count_result.scalar() or 0
    
    if saved_count >= task.total_count:
        raise HTTPException(
            status_code=400,
            detail=f"当前任务已保存 {saved_count} 道题目，已达到任务上限。请先提交任务或删除已保存的题目"
        )
    
    # 4. 返回变体内容和任务信息
    return {
        "success": True,
        "variant": {
            "id": variant.id,
            "content": variant.content,
            "answer": variant.answer,
            "explanation": variant.explanation
        },
        "task": {
            "id": task.id,
            "total_count": task.total_count,
            "completed_count": saved_count,
            "remaining": task.total_count - saved_count
        },
        "message": "可以继续验证"
    }


@router.post("/variant/{variant_id}/link-to-task", summary="将变体关联到任务（内部使用）")
async def link_variant_to_task(
    variant_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    将变体关联到任务
    注意：这个接口通常由"题目验证导出"的保存接口内部调用
    """
    # 查询变体
    result = await db.execute(
        select(ValidatedProblemExport).where(
            ValidatedProblemExport.id == variant_id,
            ValidatedProblemExport.user_id == current_user.id,
            ValidatedProblemExport.source_type == ValidatedProblemSourceType.VARIANT,
            ValidatedProblemExport.task_id.is_(None)
        )
    )
    variant = result.scalar_one_or_none()
    
    if not variant:
        raise HTTPException(404, "变体不存在或已关联任务")
    
    # 关联任务
    variant.task_id = task_id
    await db.commit()
    
    return {"success": True, "message": "变体已关联到任务"}

