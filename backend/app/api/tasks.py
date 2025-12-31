"""
任务管理API
包含任务领取、提交、放弃、超时处理等功能
"""

from typing import List, Optional
from datetime import datetime, timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, exists
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import (
    User, Problem, Task, TaskType, TaskStatus, ProblemStatus, ValidatedProblemExport, Review,
    Transaction, TransactionType, TransactionStatus
)
from app.api.deps import get_current_user
from app.config import settings


router = APIRouter()


# ==================== Pydantic 模型 ====================

class ClaimTasksRequest(BaseModel):
    """领取任务请求"""
    task_type: str = Field(..., description="任务类型：review_problem 或 create_problem")
    count: int = Field(..., ge=1, description="领取数量（上限由配置决定）")


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
    # 先自动清理超时任务
    await release_expired_tasks(db)
    
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
        # 评分任务：从已验证题目导出表分配题目
        # 只分配已提交的出题任务的题目（in_progress 的题目不进入评分）
        
        # 创建子查询：找出所有已提交的出题任务的题目ID
        submitted_creation_tasks_subquery = (
            select(Task.id)
            .where(
                Task.task_type == TaskType.CREATE_PROBLEM,
                Task.status == TaskStatus.SUBMITTED
            )
        )
        
        # 查询可用题目数量
        available_count_result = await db.execute(
            select(func.count(ValidatedProblemExport.id))
            .where(
                # 排除己出的自题目
                ValidatedProblemExport.user_id != current_user.id,
                # 只选择已提交的出题任务的题目
                ValidatedProblemExport.task_id.in_(submitted_creation_tasks_subquery),
                # 评分数量还没达到上限（3个评分）
                ValidatedProblemExport.review_count < 3,
                # 排除当前用户已经评分过的题目
                ~exists(
                    select(1)
                    .where(
                        Review.validated_problem_id == ValidatedProblemExport.id,
                        Review.reviewer_id == current_user.id
                    )
                )
            )
        )
        available_count = available_count_result.scalar() or 0
        
        if available_count < request.count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"可用题目不足，当前只有 {available_count} 个题目可以评分（只有已提交的题目才能被评分）"
            )
        
        # 创建1个评分任务（新设计：1个Task = n道题目）
        task = Task(
            user_id=current_user.id,
            task_type=task_type_enum,
            batch_id=batch_id,
            total_count=request.count,  # 批次总数
            completed_count=0,
            status=TaskStatus.IN_PROGRESS,
            claimed_at=claimed_at,
            expires_at=expires_at
        )
        db.add(task)
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"成功领取 {request.count} 个评分任务",
            "batch_id": batch_id,
            "task_count": request.count,
            "expires_at": expires_at,
            "expires_in_hours": settings.TASK_TIMEOUT_HOURS
        }
    
    else:  # CREATE_PROBLEM
        # 出题任务：创建一个批次任务记录，从0开始计数
        task = Task(
            problem_id=None,  # 出题任务没有关联的problem
            user_id=current_user.id,
            task_type=task_type_enum,
            batch_id=batch_id,
            total_count=request.count,
            completed_count=0,
            status=TaskStatus.IN_PROGRESS,
            claimed_at=claimed_at,
            expires_at=expires_at
        )
        
        db.add(task)
        await db.commit()
        
        return {
            "success": True,
            "message": f"成功领取 {request.count} 个出题任务",
            "batch_id": batch_id,
            "task_count": request.count,
            "completed_count": 0,
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
    
    注意：对于出题任务，completed_count 从数据库实时查询（ValidatedProblemExport）
    
    返回数据中包含：
    - batches: 任务批次列表
    - total_problems_created: 用户的累计出题总数（所有题目，不限任务状态）
    - total_reviews_completed: 用户的累计评分总数
    """
    # 先自动清理超时任务
    await release_expired_tasks(db)
    
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
    batch_tasks_status = {}  # 记录每个批次的所有Task状态，用于判断批次整体状态
    
    for task in tasks:
        if task.batch_id:
            if task.batch_id not in batches:
                # 初始化批次信息
                batches[task.batch_id] = {
                    "batch_id": task.batch_id,
                    "task_type": task.task_type.value,
                    "status": task.status.value,  # 初始状态，后面会更新
                    "total_count": 0,  # 批次总数，累加计算
                    "completed_count": 0,  # 批次完成数，累加计算
                    "claimed_at": task.claimed_at,
                    "expires_at": task.expires_at,
                    "submitted_at": task.submitted_at,
                    "tasks": []
                }
                batch_tasks_status[task.batch_id] = []
            
            # 添加任务到批次（新设计：评分任务不关联具体题目）
            batches[task.batch_id]["tasks"].append({
                "task_id": task.id,
                "validated_problem_id": task.validated_problem_id,  # 出题任务的题目ID（评分任务为None）
                "status": task.status.value  # 返回Task状态
            })
            
            # 记录Task状态（用于后续判断批次状态）
            batch_tasks_status[task.batch_id].append(task.status)
            
            # 累加批次的total_count和completed_count
            if task.task_type == TaskType.CREATE_PROBLEM:
                # 出题任务：从数据库实时查询题目数
                count_result = await db.execute(
                    select(func.count(ValidatedProblemExport.id))
                    .where(ValidatedProblemExport.task_id == task.id)
                )
                task_completed = count_result.scalar() or 0
                batches[task.batch_id]["total_count"] = task.total_count or 0
                batches[task.batch_id]["completed_count"] = task_completed
                batches[task.batch_id]["status"] = task.status.value
            else:
                # 评分任务：从数据库实时查询评分记录数（新设计：1个Task=n个题目）
                review_result = await db.execute(
                    select(func.count(Review.id))
                    .where(Review.task_id == task.id)
                )
                task_completed = review_result.scalar() or 0
                batches[task.batch_id]["total_count"] = task.total_count or 0
                batches[task.batch_id]["completed_count"] = task_completed
                batches[task.batch_id]["status"] = task.status.value
    
    # 新设计：评分任务只有1个Task，批次状态已经在上面设置，这里不需要额外处理
    
    # 查询用户的累计出题总数（所有题目，不限任务状态）
    problems_count_result = await db.execute(
        select(func.count(ValidatedProblemExport.id))
        .where(ValidatedProblemExport.user_id == current_user.id)
    )
    total_problems_created = problems_count_result.scalar() or 0
    
    # 查询用户的累计评分总数
    reviews_count_result = await db.execute(
        select(func.count(Review.id))
        .where(Review.reviewer_id == current_user.id)
    )
    total_reviews_completed = reviews_count_result.scalar() or 0
    
    return {
        "total_batches": len(batches),
        "batches": list(batches.values()),
        "total_problems_created": total_problems_created,  # 用户累计出题总数
        "total_reviews_completed": total_reviews_completed  # 用户累计评分总数
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
    
    # 对于出题任务，检查题目数量是否超过任务数量
    if task.task_type == TaskType.CREATE_PROBLEM:
        completed_count = task.completed_count or 0
        total_count = task.total_count or 0
        if completed_count > total_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"题目数量({completed_count})超过任务数量({total_count})，无法提交"
            )
        if completed_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="至少需要完成1道题目才能提交"
            )
    
    # 更新状态
    task.status = TaskStatus.SUBMITTED
    task.submitted_at = datetime.utcnow()
    
    # 如果是出题任务，立即发放奖励（新逻辑：提交即奖励）
    if task.task_type == TaskType.CREATE_PROBLEM:
        completed_count = task.completed_count or 0
        reward_per_problem = settings.PROBLEM_REWARD  # 每道题50元
        total_reward = reward_per_problem * completed_count
        
        # 计算交易后余额
        current_balance = await current_user.calculate_balance(db)
        new_balance = current_balance + total_reward
        
        # 创建交易记录
        transaction = Transaction(
            user_id=current_user.id,
            amount=total_reward,
            transaction_type=TransactionType.PROBLEM_REWARD,
            related_task_id=task.id,
            status=TransactionStatus.CONFIRMED,  # 提交即到账
            description=f"出题任务提交奖励（{completed_count}道题目）",
            balance_after=new_balance,
            confirmed_at=datetime.utcnow()
        )
        db.add(transaction)
        
        # 更新用户统计
        current_user.problems_created_count += completed_count
        
        # 刷新余额缓存
        await db.flush()
        await current_user.refresh_balance(db)
    
    await db.commit()
    
    return {
        "success": True,
        "message": "任务提交成功" + (f"，获得奖励 {total_reward}元" if task.task_type == TaskType.CREATE_PROBLEM else ""),
        "task_id": task.id,
        "submitted_at": task.submitted_at,
        "reward": total_reward if task.task_type == TaskType.CREATE_PROBLEM else None
    }


@router.post("/{task_id}/abandon", summary="放弃任务")
async def abandon_task(
    task_id: int,
    confirmed: bool = False,  # 是否已确认放弃（前端通过query参数传递）
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    放弃任务
    
    规则：
    1. 出题任务：如果任务下有已完成的题目，会一并删除（需要确认）
    2. 评分任务：自动放弃整个批次的所有任务（不需要确认）
    3. 首次调用时如果有题目，返回警告要求确认
    4. 确认后再次调用（confirmed=true）才真正执行
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
    
    # 评分任务：自动放弃整个批次
    if task.task_type == TaskType.REVIEW_PROBLEM and task.batch_id:
        # 查询同批次的所有进行中的任务
        batch_tasks_result = await db.execute(
            select(Task).where(
                and_(
                    Task.batch_id == task.batch_id,
                    Task.user_id == current_user.id,
                    Task.status == TaskStatus.IN_PROGRESS
                )
            )
        )
        batch_tasks = batch_tasks_result.scalars().all()
        
        # 放弃整个批次
        for batch_task in batch_tasks:
            batch_task.status = TaskStatus.REJECTED
            batch_task.abandoned_count = 1
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"已放弃整个评分批次（共 {len(batch_tasks)} 个任务）",
            "batch_id": task.batch_id,
            "abandoned_count": len(batch_tasks)
        }
    
    # 出题任务：检查是否有已完成的题目
    problem_count = 0
    if task.task_type == TaskType.CREATE_PROBLEM:
        count_result = await db.execute(
            select(func.count(ValidatedProblemExport.id)).where(
                ValidatedProblemExport.task_id == task_id
            )
        )
        problem_count = count_result.scalar() or 0
    
    # 如果有题目且未确认，返回警告
    if problem_count > 0 and not confirmed:
        return {
            "success": False,
            "requires_confirmation": True,
            "problem_count": problem_count,
            "message": f"该任务下有 {problem_count} 道已完成的题目，放弃任务将会删除这些题目。是否确认放弃？",
            "warning": "⚠️ 此操作不可撤销！题目一旦删除将无法恢复。"
        }
    
    # 确认后执行放弃操作
    # 1. 删除关联的题目（数据库的 CASCADE 会自动删除相关的 Task 和 Review 记录）
    if problem_count > 0:
        problems_result = await db.execute(
            select(ValidatedProblemExport).where(
                ValidatedProblemExport.task_id == task_id
            )
        )
        problems = problems_result.scalars().all()
        
        for problem in problems:
            await db.delete(problem)
    
    # 2. 更新任务状态
    task.status = TaskStatus.REJECTED  # 使用REJECTED表示主动放弃
    task.abandoned_count = 1
    
    await db.commit()
    
    return {
        "success": True,
        "message": "任务已放弃" + (f"，已删除 {problem_count} 道题目" if problem_count > 0 else ""),
        "task_id": task.id,
        "deleted_problem_count": problem_count
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

