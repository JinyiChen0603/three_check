"""
任务管理API
包含任务领取、提交、放弃、超时处理等功能
"""

from typing import List, Optional
from datetime import datetime, timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import (
    User, Problem, Task, TaskType, TaskStatus, ProblemStatus, ValidatedProblemExport
)
from app.api.deps import get_current_user
from app.config import settings


router = APIRouter()


# ==================== Pydantic 模型 ====================

class ClaimTasksRequest(BaseModel):
    """领取任务请求"""
    task_type: str = Field(..., description="任务类型：review_problem 或 create_problem")
    count: int = Field(..., ge=1, le=50, description="领取数量（最多50个）")


class TaskResponse(BaseModel):
    """任务响应模型"""
    id: int
    problem_id: Optional[int]
    task_type: str
    status: str
    claimed_at: Optional[datetime]
    expires_at: Optional[datetime]
    batch_id: Optional[str]
    total_count: int
    completed_count: int
    
    class Config:
        from_attributes = True


# ==================== 辅助函数 ====================

async def release_expired_tasks(db: AsyncSession):
    """释放超时的任务（后台任务）"""
    now = datetime.utcnow()
    
    # 查找所有超时的任务
    result = await db.execute(
        select(Task).where(
            and_(
                Task.status == TaskStatus.IN_PROGRESS,
                Task.expires_at < now
            )
        )
    )
    expired_tasks = result.scalars().all()
    
    for task in expired_tasks:
        task.status = TaskStatus.TIMEOUT
    
    await db.commit()
    
    return len(expired_tasks)


# ==================== API 路由 ====================

@router.post("/claim", summary="领取任务")
async def claim_tasks(
    request: ClaimTasksRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    领取任务
    
    规则：
    1. 每次最多领取50个任务
    2. 领取后12小时内必须完成，否则自动释放
    3. 评分任务不能包含自己出的题目
    4. 必须完成当前任务后才能继续领取
    """
    # 验证任务类型
    try:
        task_type_enum = TaskType(request.task_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的任务类型: {request.task_type}"
        )
    
    # 检查是否有进行中的任务
    result = await db.execute(
        select(func.count(Task.id))
        .where(
            and_(
                Task.user_id == current_user.id,
                Task.status == TaskStatus.IN_PROGRESS
            )
        )
    )
    in_progress_count = result.scalar()
    
    if in_progress_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"您还有 {in_progress_count} 个进行中的任务，请先完成后再领取新任务"
        )
    
    # 检查领取数量
    if request.count > settings.MAX_TASKS_PER_CLAIM:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"单次最多领取 {settings.MAX_TASKS_PER_CLAIM} 个任务"
        )
    
    # 生成批次ID
    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    claimed_at = datetime.utcnow()
    expires_at = claimed_at + timedelta(hours=settings.TASK_TIMEOUT_HOURS)
    
    if task_type_enum == TaskType.REVIEW_PROBLEM:
        # 评分任务：分配已发布的题目
        # 排除自己出的题目
        query = (
            select(Problem)
            .where(
                and_(
                    Problem.status.in_([ProblemStatus.PENDING_REVIEW, ProblemStatus.PUBLISHED]),
                    Problem.creator_id != current_user.id
                )
            )
            # 排除已经评分过的题目
            .outerjoin(
                Task,
                and_(
                    Task.problem_id == Problem.id,
                    Task.user_id == current_user.id,
                    Task.task_type == TaskType.REVIEW_PROBLEM
                )
            )
            .where(Task.id.is_(None))
            .limit(request.count)
        )
        
        result = await db.execute(query)
        available_problems = result.scalars().all()
        
        if len(available_problems) < request.count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"可用题目不足，当前只有 {len(available_problems)} 个题目可以评分"
            )
        
        # 创建任务
        tasks = []
        for problem in available_problems:
            task = Task(
                problem_id=problem.id,
                user_id=current_user.id,
                task_type=task_type_enum,
                batch_id=batch_id,
                total_count=request.count,
                completed_count=0,
                status=TaskStatus.IN_PROGRESS,
                claimed_at=claimed_at,
                expires_at=expires_at
            )
            tasks.append(task)
            db.add(task)
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"成功领取 {len(tasks)} 个评分任务",
            "batch_id": batch_id,
            "task_count": len(tasks),
            "expires_at": expires_at,
            "expires_in_hours": settings.TASK_TIMEOUT_HOURS,
            "tasks": [
                {
                    "task_id": t.id,
                    "problem_id": t.problem_id
                }
                for t in tasks
            ]
        }
    
    else:  # CREATE_PROBLEM
        # 出题任务：创建一个批次任务记录
        # 先查询该用户已创建但未关联任务的题目（DRAFT状态，且没有关联到任何进行中的任务）
        existing_problems_result = await db.execute(
            select(func.count(Problem.id))
            .where(
                and_(
                    Problem.creator_id == current_user.id,
                    Problem.status == ProblemStatus.DRAFT,
                    Problem.parent_problem_id.is_(None)  # 只统计母题，不包括变体
                )
            )
            .outerjoin(
                Task,
                and_(
                    Task.problem_id == Problem.id,
                    Task.task_type == TaskType.CREATE_PROBLEM,
                    Task.status == TaskStatus.IN_PROGRESS
                )
            )
            .where(Task.id.is_(None))  # 没有关联到进行中的任务
        )
        existing_problems_count = existing_problems_result.scalar() or 0
        
        # 查询该用户在导出列表中已保存的题目数量（这些题目也应该计入新任务进度）
        existing_exported_result = await db.execute(
            select(func.count(ValidatedProblemExport.id))
            .where(ValidatedProblemExport.user_id == current_user.id)
        )
        existing_exported_count = existing_exported_result.scalar() or 0
        
        # 总已创建题目数 = Problem表中的题目 + ValidatedProblemExport表中的题目
        existing_count = existing_problems_count + existing_exported_count
        
        # 将已出的题目并入新任务进度（但不能超过总数）
        initial_completed = min(existing_count, request.count)
        
        task = Task(
            problem_id=None,  # 出题任务没有关联的problem
            user_id=current_user.id,
            task_type=task_type_enum,
            batch_id=batch_id,
            total_count=request.count,
            completed_count=initial_completed,
            status=TaskStatus.IN_PROGRESS,
            claimed_at=claimed_at,
            expires_at=expires_at
        )
        
        db.add(task)
        await db.commit()
        
        message = f"成功领取 {request.count} 个出题任务"
        if initial_completed > 0:
            message += f"。已将您之前创建的 {initial_completed} 道题目并入当前任务进度"
            if existing_exported_count > 0:
                message += f"（包括导出列表中的 {existing_exported_count} 道题目）"
        
        return {
            "success": True,
            "message": message,
            "batch_id": batch_id,
            "task_count": request.count,
            "completed_count": initial_completed,
            "expires_at": expires_at,
            "expires_in_hours": settings.TASK_TIMEOUT_HOURS,
            "note": "请开始出题，每完成一个题目会自动更新进度"
        }


@router.get("/my-tasks", summary="查看我的任务")
async def get_my_tasks(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查看当前用户的任务列表
    
    可按状态筛选
    """
    query = select(Task).where(Task.user_id == current_user.id)
    
    if status:
        try:
            status_enum = TaskStatus(status)
            query = query.where(Task.status == status_enum)
        except ValueError:
            pass
    
    query = query.order_by(Task.created_at.desc())
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    # 按批次汇总
    batches = {}
    for task in tasks:
        if task.batch_id:
            if task.batch_id not in batches:
                batches[task.batch_id] = {
                    "batch_id": task.batch_id,
                    "task_type": task.task_type.value,
                    "status": task.status.value,
                    "total_count": task.total_count,
                    "completed_count": task.completed_count,
                    "claimed_at": task.claimed_at,
                    "expires_at": task.expires_at,
                    "tasks": []
                }
            batches[task.batch_id]["tasks"].append({
                "task_id": task.id,
                "problem_id": task.problem_id
            })
    
    return {
        "total_batches": len(batches),
        "batches": list(batches.values())
    }


@router.post("/{task_id}/submit", summary="提交任务")
async def submit_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    提交任务
    
    注意：评分任务在完成评分时自动提交，此接口主要用于出题任务
    """
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能提交他人的任务"
        )
    
    if task.status != TaskStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务状态为 {task.status.value}，无法提交"
        )
    
    # 检查是否过期
    if task.expires_at and datetime.utcnow() > task.expires_at:
        task.status = TaskStatus.TIMEOUT
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务已超时"
        )
    
    # 更新状态
    task.status = TaskStatus.SUBMITTED
    task.submitted_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "success": True,
        "message": "任务提交成功",
        "task_id": task.id,
        "submitted_at": task.submitted_at
    }


@router.post("/{task_id}/abandon", summary="放弃任务")
async def abandon_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    放弃任务
    
    可以放弃单个任务或整个批次
    """
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能放弃他人的任务"
        )
    
    if task.status != TaskStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务状态为 {task.status.value}，无法放弃"
        )
    
    # 更新状态
    task.status = TaskStatus.REJECTED  # 使用REJECTED表示主动放弃
    task.abandoned_count = 1
    
    await db.commit()
    
    return {
        "success": True,
        "message": "任务已放弃",
        "task_id": task.id
    }


@router.post("/abandon-batch/{batch_id}", summary="放弃整个批次的任务")
async def abandon_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    放弃整个批次的任务
    
    例如：领取了50个任务，但只想做10个，可以放弃整个批次
    """
    # 查询批次中的所有任务
    result = await db.execute(
        select(Task).where(
            and_(
                Task.batch_id == batch_id,
                Task.user_id == current_user.id,
                Task.status == TaskStatus.IN_PROGRESS
            )
        )
    )
    tasks = result.scalars().all()
    
    if not tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批次不存在或任务已完成"
        )
    
    # 放弃所有任务
    abandoned_count = 0
    for task in tasks:
        task.status = TaskStatus.REJECTED
        abandoned_count += 1
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"成功放弃 {abandoned_count} 个任务",
        "batch_id": batch_id,
        "abandoned_count": abandoned_count
    }


@router.get("/stats", summary="查看任务统计")
async def get_task_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查看当前用户的任务统计
    
    包括：进行中、已完成、已超时等数量
    """
    # 统计各状态的任务数
    result = await db.execute(
        select(
            Task.status,
            func.count(Task.id).label("count")
        )
        .where(Task.user_id == current_user.id)
        .group_by(Task.status)
    )
    
    stats = {status.value: 0 for status in TaskStatus}
    for row in result.all():
        stats[row.status.value] = row.count
    
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "stats": stats,
        "total_tasks": sum(stats.values())
    }


@router.post("/cleanup-expired", summary="清理超时任务（后台任务）")
async def cleanup_expired_tasks(
    db: AsyncSession = Depends(get_db)
):
    """
    清理超时的任务
    
    这是一个后台任务，可以定期调用
    """
    count = await release_expired_tasks(db)
    
    return {
        "success": True,
        "message": f"已释放 {count} 个超时任务"
    }

