"""
管理员API
包含用户管理、题目审核等管理员功能
"""

from typing import List, Optional
from datetime import datetime
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.database import get_db
from app.models import (
    User, 
    ValidatedProblemExport, 
    AdminReviewStatus,
    Review,
    Task,
    TaskStatus,
    Transaction,
    TransactionType,
    TransactionStatus
)
from app.api.deps import get_current_admin_user
from app.services.export_service import export_service
from app.config import settings


router = APIRouter()


# ==================== Pydantic 模型 ====================

class ProblemReviewListItem(BaseModel):
    """题目审核列表项"""
    id: int
    user_id: int
    username: str
    content: str
    answer: str
    explanation: str
    difficulty_passed: Optional[bool] = None
    originality_passed: bool
    rigor_passed: bool
    admin_review_status: str
    created_at: str
    
    # 人工评分信息
    review_count: int = 0
    avg_innovation_score: Optional[float] = None
    avg_rigor_score: Optional[float] = None
    veto_count: int = 0  # 一票否决的数量
    
    # 任务状态
    task_status: Optional[str] = None  # submitted/in_progress/timeout等
    
    class Config:
        from_attributes = True


class ReviewDetail(BaseModel):
    """单个评分记录详情"""
    id: int
    reviewer_id: int
    reviewer_username: str
    is_answer_correct: bool
    innovation_score: Optional[int] = None
    rigor_score: Optional[int] = None
    comment: Optional[str] = None
    is_vetoed: bool
    veto_reason: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True


class ProblemReviewDetail(BaseModel):
    """题目审核详情"""
    id: int
    user_id: int
    username: str
    content: str
    answer: str
    explanation: str
    
    # 三重质检结果
    difficulty_validation: Optional[dict] = None
    originality_check: dict
    rigor_check: dict
    
    # 人工评分详情
    reviews: List[ReviewDetail]
    
    # 审核状态
    admin_review_status: str
    admin_review_note: Optional[str] = None
    admin_reviewed_at: Optional[str] = None
    admin_reviewer_username: Optional[str] = None
    
    created_at: str
    
    class Config:
        from_attributes = True


class AdminReviewRequest(BaseModel):
    """管理员审核请求"""
    problem_id: int
    approved: bool
    note: Optional[str] = None


# ==================== API 路由 ====================

@router.get("/problems/pending-review", response_model=dict, summary="获取待审核题目列表")
async def get_pending_review_problems(
    status_filter: Optional[str] = Query(None, description="审核状态筛选: pending/approved/rejected"),
    skip: int = 0,
    limit: int = 50,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取待审核题目列表（管理员）
    
    - 只显示已提交的题目（排除in_progress状态的任务）
    - 只显示有人工评分记录的题目
    - 包含用户信息、题目内容、三重质检结果
    - 包含人工评分的统计信息
    """
    # 构建查询
    query = select(ValidatedProblemExport).join(
        User, ValidatedProblemExport.user_id == User.id
    )
    
    # 只显示已提交的题目（排除in_progress状态）
    # 查找所有关联的任务，如果任务不是in_progress状态，则显示
    subquery = select(Task.validated_problem_id).where(
        and_(
            Task.validated_problem_id == ValidatedProblemExport.id,
            Task.status == TaskStatus.IN_PROGRESS
        )
    )
    
    query = query.where(
        or_(
            ValidatedProblemExport.task_id.is_(None),  # 没有关联任务
            ~ValidatedProblemExport.id.in_(subquery)  # 或者没有in_progress的任务
        )
    )
    
    # 状态筛选
    if status_filter:
        if status_filter == "pending":
            query = query.where(ValidatedProblemExport.admin_review_status == AdminReviewStatus.PENDING)
        elif status_filter == "approved":
            query = query.where(ValidatedProblemExport.admin_review_status == AdminReviewStatus.APPROVED)
        elif status_filter == "rejected":
            query = query.where(ValidatedProblemExport.admin_review_status == AdminReviewStatus.REJECTED)
    
    # 按创建时间倒序
    query = query.order_by(ValidatedProblemExport.created_at.desc())
    
    # 分页
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    problems = result.scalars().all()
    
    # 获取每个题目的用户信息和评分统计
    problem_list = []
    for problem in problems:
        # 获取用户名
        user_result = await db.execute(
            select(User).where(User.id == problem.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        # 获取关联的出题任务状态
        task_status = None
        if problem.task_id:
            task_result = await db.execute(
                select(Task).where(Task.id == problem.task_id)
            )
            task = task_result.scalar_one_or_none()
            if task:
                task_status = task.status.value
        
        # 统计一票否决的数量
        veto_count_result = await db.execute(
            select(func.count(Review.id)).where(
                Review.validated_problem_id == problem.id,
                Review.is_vetoed == True
            )
        )
        veto_count = veto_count_result.scalar() or 0
        
        # 解析三重质检结果
        difficulty_passed = None
        if problem.difficulty_validation:
            difficulty_passed = problem.difficulty_validation.get('passed', None)
        
        originality_passed = problem.originality_check.get('passed', False) if problem.originality_check else False
        rigor_passed = problem.rigor_check.get('passed', False) if problem.rigor_check else False
        
        problem_list.append({
            "id": problem.id,
            "user_id": problem.user_id,
            "username": user.username if user else "未知用户",
            "content": problem.content,
            "answer": problem.answer,
            "explanation": problem.explanation,
            "difficulty_passed": difficulty_passed,
            "originality_passed": originality_passed,
            "rigor_passed": rigor_passed,
            "admin_review_status": problem.admin_review_status.value,
            "created_at": problem.created_at.isoformat(),
            # 直接使用表中的字段
            "review_count": problem.review_count,
            "avg_innovation_score": round(problem.avg_innovation_score, 2) if problem.avg_innovation_score else None,
            "avg_rigor_score": round(problem.avg_rigor_score, 2) if problem.avg_rigor_score else None,
            "veto_count": veto_count,  # 一票否决的数量
            # 任务状态信息
            "task_status": task_status  # submitted/in_progress/timeout等
        })
    
    return {
        "total": len(problem_list),
        "problems": problem_list
    }


@router.get("/problems/{problem_id}/detail", response_model=ProblemReviewDetail, summary="获取题目审核详情")
async def get_problem_review_detail(
    problem_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取题目审核详情（管理员）
    
    包含：
    - 题目完整信息
    - 三重质检详细结果
    - 所有人工评分记录
    - 审核状态和备注
    """
    # 查询题目
    result = await db.execute(
        select(ValidatedProblemExport).where(ValidatedProblemExport.id == problem_id)
    )
    problem = result.scalar_one_or_none()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    # 获取用户信息
    user_result = await db.execute(
        select(User).where(User.id == problem.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    # 获取所有评分记录
    review_query = select(Review).where(Review.validated_problem_id == problem.id)
    review_result = await db.execute(review_query)
    reviews = review_result.scalars().all()
    
    # 构建评分详情列表
    review_details = []
    for review in reviews:
        reviewer_result = await db.execute(
            select(User).where(User.id == review.reviewer_id)
        )
        reviewer = reviewer_result.scalar_one_or_none()
        
        review_details.append({
            "id": review.id,
            "reviewer_id": review.reviewer_id,
            "reviewer_username": reviewer.username if reviewer else "未知用户",
            "is_answer_correct": review.is_answer_correct,
            "innovation_score": review.innovation_score,
            "rigor_score": review.rigor_score,
            "comment": review.comment,
            "is_vetoed": review.is_vetoed,
            "veto_reason": review.veto_reason,
            "created_at": review.created_at.isoformat()
        })
    
    # 获取审核管理员用户名
    admin_reviewer_username = None
    if problem.admin_reviewer_id:
        admin_reviewer_result = await db.execute(
            select(User).where(User.id == problem.admin_reviewer_id)
        )
        admin_reviewer = admin_reviewer_result.scalar_one_or_none()
        if admin_reviewer:
            admin_reviewer_username = admin_reviewer.username
    
    return {
        "id": problem.id,
        "user_id": problem.user_id,
        "username": user.username if user else "未知用户",
        "content": problem.content,
        "answer": problem.answer,
        "explanation": problem.explanation,
        "difficulty_validation": problem.difficulty_validation,
        "originality_check": problem.originality_check,
        "rigor_check": problem.rigor_check,
        "reviews": review_details,
        "admin_review_status": problem.admin_review_status.value,
        "admin_review_note": problem.admin_review_note,
        "admin_reviewed_at": problem.admin_reviewed_at.isoformat() if problem.admin_reviewed_at else None,
        "admin_reviewer_username": admin_reviewer_username,
        "created_at": problem.created_at.isoformat()
    }


@router.post("/problems/review", summary="审核题目")
async def review_problem(
    request: AdminReviewRequest,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员审核题目
    
    - approved=True: 通过审核，用户余额会更新
    - approved=False: 不通过审核
    """
    # 查询题目
    result = await db.execute(
        select(ValidatedProblemExport).where(ValidatedProblemExport.id == request.problem_id)
    )
    problem = result.scalar_one_or_none()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    # 更新审核状态
    problem.admin_review_status = AdminReviewStatus.APPROVED if request.approved else AdminReviewStatus.REJECTED
    problem.admin_reviewer_id = admin_user.id
    problem.admin_review_note = request.note
    problem.admin_reviewed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(problem)
    
    return {
        "success": True,
        "message": "审核成功",
        "problem_id": problem.id,
        "status": problem.admin_review_status.value
    }


@router.get("/problems/export", summary="导出题目（管理员）")
async def export_admin_problems(
    status_filter: Optional[str] = Query(None, description="审核状态筛选: pending/approved/rejected，不传则导出全部"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    导出题目到Excel（管理员）
    
    Args:
        status_filter: 审核状态筛选 (pending=待审核, approved=已通过, rejected=已拒绝, 不传=全部)
    
    Returns:
        Excel文件下载
    """
    try:
        # 查询所有题目，并加载用户信息
        query = (
            select(ValidatedProblemExport)
            .options(selectinload(ValidatedProblemExport.user))
            .order_by(ValidatedProblemExport.created_at.desc())
        )
        
        # 只显示已提交的题目（排除in_progress状态）
        subquery = select(Task.validated_problem_id).where(
            and_(
                Task.validated_problem_id == ValidatedProblemExport.id,
                Task.status == TaskStatus.IN_PROGRESS
            )
        )
        
        query = query.where(
            or_(
                ValidatedProblemExport.task_id.is_(None),
                ~ValidatedProblemExport.id.in_(subquery)
            )
        )
        
        # 状态筛选（简化逻辑）
        if status_filter:
            if status_filter == "pending":
                query = query.where(ValidatedProblemExport.admin_review_status == AdminReviewStatus.PENDING)
            elif status_filter == "approved":
                query = query.where(ValidatedProblemExport.admin_review_status == AdminReviewStatus.APPROVED)
            elif status_filter == "rejected":
                query = query.where(ValidatedProblemExport.admin_review_status == AdminReviewStatus.REJECTED)
        # 如果 status_filter 为 None，则导出全部题目
        
        result = await db.execute(query)
        problems = result.scalars().all()
        
        if not problems:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="没有可导出的题目"
            )
        
        # 转换为字典列表
        problems_data = []
        for p in problems:
            try:
                # 解析三重质检结果
                difficulty_passed = None
                if p.difficulty_validation and isinstance(p.difficulty_validation, dict):
                    difficulty_passed = p.difficulty_validation.get('passed', None)
                
                originality_passed = p.originality_check.get('passed', False) if p.originality_check else False
                rigor_passed = p.rigor_check.get('passed', False) if p.rigor_check else False
                
                # 统计一票否决的数量
                veto_count_result = await db.execute(
                    select(func.count(Review.id)).where(
                        Review.validated_problem_id == p.id,
                        Review.is_vetoed == True
                    )
                )
                veto_count = veto_count_result.scalar() or 0
                
                # 获取任务状态
                task_status = ""
                if p.task_id:
                    task_result = await db.execute(
                        select(Task).where(Task.id == p.task_id)
                    )
                    task = task_result.scalar_one_or_none()
                    if task:
                        task_status = {
                            "in_progress": "进行中",
                            "submitted": "已提交",
                            "timeout": "已超时",
                            "approved": "已批准",
                            "rejected": "已驳回"
                        }.get(task.status.value, task.status.value)
                
                problems_data.append({
                    "id": p.id,
                    "user_id": p.user_id,
                    "username": p.user.username if p.user else "",
                    "content": p.content,
                    "answer": p.answer,
                    "explanation": p.explanation,
                    "difficulty_passed": "通过" if difficulty_passed else "未通过" if difficulty_passed is False else "未检测",
                    "originality_passed": "通过" if originality_passed else "未通过",
                    "rigor_passed": "通过" if rigor_passed else "未通过",
                    "review_count": p.review_count,  # 直接使用表中的字段
                    "avg_innovation_score": round(p.avg_innovation_score, 2) if p.avg_innovation_score else None,
                    "avg_rigor_score": round(p.avg_rigor_score, 2) if p.avg_rigor_score else None,
                    "veto_count": veto_count,  # 一票否决的数量
                    "task_status": task_status,  # 任务状态
                    "admin_review_status": {
                        "pending": "待审核",
                        "approved": "通过",
                        "rejected": "未通过"
                    }.get(p.admin_review_status.value, "待审核"),
                    "admin_reviewer": p.admin_reviewer.username if p.admin_reviewer else "",
                    "admin_review_note": p.admin_review_note or "",
                    "admin_reviewed_at": p.admin_reviewed_at.isoformat() if p.admin_reviewed_at else "",
                    "created_at": p.created_at.isoformat() if p.created_at else None
                })
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"处理导出题目失败 {p.id}: {str(e)}")
                continue
        
        if not problems_data:
            status_text = {
                "pending": "待审核",
                "approved": "已通过",
                "rejected": "已拒绝"
            }.get(status_filter, "")
            detail = f"没有{status_text}的题目可导出" if status_text else "没有可导出的题目"
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail
            )
        
        # 生成Excel
        excel_file = export_service.export_to_excel(problems_data)
        
        # 返回文件下载
        filename = f"管理员题目审核_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        # 使用 RFC 5987 格式编码文件名，支持中文
        encoded_filename = quote(filename, safe='')
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"导出题目失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出题目失败: {str(e)}"
        )

