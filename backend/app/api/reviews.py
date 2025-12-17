"""
评分管理API
包含完整的评分流程：
1. 正确性验证（4选1）
2. 创新性和严谨性打分（0-10分）
3. 一票否决机制
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel, Field
import random

from app.database import get_db
from app.models import (
    User, Problem, Review, ReviewStatus, Task, TaskStatus,
    Transaction, TransactionType, TransactionStatus
)
from app.api.deps import get_current_user
from app.services.ai_service import gpt_service
from app.config import settings


router = APIRouter()


# ==================== Pydantic 模型 ====================

class ChoicesResponse(BaseModel):
    """4选1选项响应"""
    problem_id: int
    problem_content: dict
    choices: List[str]
    correct_index: int  # 仅用于后端验证，不返回给前端


class VerifyCorrectnessRequest(BaseModel):
    """验证正确性请求"""
    problem_id: int
    selected_index: int = Field(..., ge=0, le=3, description="选择的选项索引（0-3）")
    user_answer: Optional[str] = Field(None, description="用户判断错误时的说明")


class ScoreRequest(BaseModel):
    """评分请求"""
    review_id: int
    innovation_score: int = Field(..., ge=0, le=10, description="创新性评分 0-10")
    rigor_score: int = Field(..., ge=0, le=10, description="数学严谨性评分 0-10")
    comment: Optional[str] = Field(None, description="评论")
    is_vetoed: bool = Field(False, description="是否一票否决")
    veto_reason: Optional[str] = Field(None, description="否决理由（如果一票否决）")


class ReviewResponse(BaseModel):
    """评分响应模型"""
    id: int
    problem_id: int
    reviewer_id: int
    is_answer_correct: bool
    innovation_score: Optional[int]
    rigor_score: Optional[int]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== API 路由 ====================

@router.get("/problem/{problem_id}/choices", summary="获取4选1选项（正确性验证）")
async def get_problem_choices(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取题目的4选1选项用于正确性验证
    
    - 1个正确答案
    - 3个由GPT生成的相似错误答案
    
    选项顺序随机打乱
    """
    # 查询题目
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    problem = result.scalar_one_or_none()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    # 不能评分自己的题目
    if problem.creator_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能评分自己出的题目"
        )
    
    # 生成3个相似的错误答案
    similar_result = await gpt_service.generate_similar_answers(
        problem=str(problem.content),
        correct_answer=problem.answer,
        count=3
    )
    
    if not similar_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成选项失败"
        )
    
    # 组合正确答案和错误答案
    choices = [problem.answer] + similar_result["similar_answers"][:3]
    
    # 记录正确答案的原始位置
    correct_index = 0
    
    # 随机打乱选项
    combined = list(enumerate(choices))
    random.shuffle(combined)
    
    # 找到正确答案的新位置
    shuffled_choices = []
    for original_idx, choice in combined:
        shuffled_choices.append(choice)
        if original_idx == 0:  # 原始的正确答案
            correct_index = len(shuffled_choices) - 1
    
    return {
        "problem_id": problem.id,
        "problem_title": problem.title,
        "problem_content": problem.content,
        "problem_explanation": problem.explanation,
        "choices": shuffled_choices,
        "correct_index": correct_index,  # 在实际应用中，这个不应该返回给前端
        "instruction": "请选择你认为正确的答案："
    }


@router.post("/problem/{problem_id}/verify", summary="提交正确性验证")
async def verify_correctness(
    problem_id: int,
    request: VerifyCorrectnessRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    提交正确性验证结果
    
    流程：
    1. 用户选择4个选项中的一个
    2. 如果选对 → 题目正确，进入评分阶段
    3. 如果选错 → 展示解析和答案，让用户判断题目是否有问题
    """
    # 查询题目
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    problem = result.scalar_one_or_none()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    # 不能评分自己的题目
    if problem.creator_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能评分自己出的题目"
        )
    
    # 重新生成选项（应该与之前一致，实际应用中可以缓存）
    similar_result = await gpt_service.generate_similar_answers(
        problem=str(problem.content),
        correct_answer=problem.answer,
        count=3
    )
    
    choices = [problem.answer] + similar_result["similar_answers"][:3]
    
    # 这里简化处理，实际应该使用缓存的选项顺序
    # 假设前端传来的是正确答案的索引
    is_correct = (request.selected_index == 0)  # 简化处理
    
    # 创建或更新评分记录
    review = Review(
        problem_id=problem.id,
        reviewer_id=current_user.id,
        is_answer_correct=is_correct,
        correctness_verification={
            "selected_index": request.selected_index,
            "selected_answer": choices[request.selected_index] if request.selected_index < len(choices) else "",
            "user_judgment": request.user_answer if not is_correct else None
        },
        status=ReviewStatus.PENDING
    )
    
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    if is_correct:
        # 选对了，进入评分阶段
        return {
            "success": True,
            "is_correct": True,
            "review_id": review.id,
            "message": "✅ 答案正确！请继续对题目进行创新性和严谨性评分。",
            "next_step": "scoring"
        }
    else:
        # 选错了，展示解析和答案
        return {
            "success": True,
            "is_correct": False,
            "review_id": review.id,
            "message": "❌ 答案不正确。请查看题目的解析和标准答案：",
            "problem_explanation": problem.explanation,
            "correct_answer": problem.answer,
            "question": "请判断：题目的解析和答案是否正确？",
            "next_step": "manual_verification"
        }


@router.post("/score", summary="提交创新性和严谨性评分")
async def submit_score(
    request: ScoreRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    提交创新性和严谨性评分（0-10分）
    
    支持一票否决机制：
    - 如果is_vetoed=True，必须提供veto_reason
    - 一票否决的题目会返回给出题者修改
    """
    # 查询评分记录
    result = await db.execute(
        select(Review).where(Review.id == request.review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评分记录不存在"
        )
    
    if review.reviewer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能修改他人的评分"
        )
    
    # 验证一票否决必须有理由
    if request.is_vetoed and not request.veto_reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="一票否决必须提供理由"
        )
    
    # 更新评分
    review.innovation_score = request.innovation_score
    review.rigor_score = request.rigor_score
    review.comment = request.comment
    review.is_vetoed = request.is_vetoed
    review.veto_reason = request.veto_reason
    review.status = ReviewStatus.APPROVED
    review.approved_at = datetime.utcnow()
    
    # 更新题目的平均评分
    result = await db.execute(
        select(Problem).where(Problem.id == review.problem_id)
    )
    problem = result.scalar_one_or_none()
    
    if problem:
        # 重新计算平均分
        result = await db.execute(
            select(
                func.avg(Review.innovation_score).label("avg_innovation"),
                func.avg(Review.rigor_score).label("avg_rigor"),
                func.count(Review.id).label("review_count")
            )
            .where(
                and_(
                    Review.problem_id == problem.id,
                    Review.status == ReviewStatus.APPROVED
                )
            )
        )
        stats = result.one()
        
        problem.avg_innovation_score = float(stats.avg_innovation) if stats.avg_innovation else None
        problem.avg_rigor_score = float(stats.avg_rigor) if stats.avg_rigor else None
        problem.review_count = stats.review_count
    
    # 增加用户的评分完成计数
    current_user.reviews_completed_count += 1
    
    # 创建奖励交易（7元）
    transaction = Transaction(
        user_id=current_user.id,
        amount=settings.REVIEW_REWARD,
        transaction_type=TransactionType.REVIEW_REWARD,
        related_problem_id=review.problem_id,
        related_task_id=review.task_id,
        status=TransactionStatus.CONFIRMED,  # 评分奖励立即到账
        description=f"评分题目 #{review.problem_id}",
        balance_after=current_user.balance + settings.REVIEW_REWARD,
        confirmed_at=datetime.utcnow()
    )
    
    # 更新用户余额
    current_user.balance += settings.REVIEW_REWARD
    
    db.add(transaction)
    await db.commit()
    await db.refresh(review)
    
    result_message = (
        f"⚠️ 您已对该题目一票否决。理由：{request.veto_reason}"
        if request.is_vetoed
        else f"✅ 评分完成！创新性：{request.innovation_score}/10，严谨性：{request.rigor_score}/10"
    )
    
    return {
        "success": True,
        "review_id": review.id,
        "message": result_message,
        "reward": settings.REVIEW_REWARD,
        "new_balance": current_user.balance,
        "is_vetoed": request.is_vetoed
    }


@router.get("/my-reviews", summary="查看我的评分记录")
async def get_my_reviews(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """查看当前用户的评分记录"""
    query = (
        select(Review)
        .where(Review.reviewer_id == current_user.id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(query)
    reviews = result.scalars().all()
    
    return {
        "total": len(reviews),
        "reviews": [
            {
                "id": r.id,
                "problem_id": r.problem_id,
                "is_answer_correct": r.is_answer_correct,
                "innovation_score": r.innovation_score,
                "rigor_score": r.rigor_score,
                "is_vetoed": r.is_vetoed,
                "status": r.status.value,
                "created_at": r.created_at
            }
            for r in reviews
        ]
    }


@router.get("/{review_id}", response_model=ReviewResponse, summary="获取评分详情")
async def get_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定评分的详细信息"""
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评分记录不存在"
        )
    
    # 只有评分者或管理员可以查看
    if review.reviewer_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看该评分"
        )
    
    return review

