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
from sqlalchemy import select, and_, or_, func, exists
from pydantic import BaseModel, Field
import random
import re

from app.database import get_db
from app.models import (
    User, Problem, ProblemStatus, HumanReviewStatus,
    Review, ReviewStatus, Task, TaskStatus, TaskType,
    Transaction, TransactionType, TransactionStatus,
    ValidatedProblemExport  # 新增：已验证题目导出表
)
from app.api.deps import get_current_user
from app.services.muti_choice_cre_service import gpt_service
from app.services.problem_storage import get_problem_storage_service
from app.config import settings


router = APIRouter()


# ==================== 辅助函数 ====================

def auto_wrap_latex(text: str) -> str:
    """
    自动检测并包裹LaTeX公式
    
    如果文本包含LaTeX命令但没有用$...$包裹，自动包裹
    """
    if not text:
        return text
    
    text_str = str(text).strip()
    
    # 检测常见的LaTeX命令
    latex_patterns = [
        r'\\frac', r'\\sqrt', r'\\pi', r'\\theta', r'\\alpha', r'\\beta',
        r'\\gamma', r'\\delta', r'\\sum', r'\\int', r'\\lim', r'\\sin',
        r'\\cos', r'\\tan', r'\\log', r'\\ln', r'\\exp'
    ]
    
    has_latex = any(re.search(pattern, text_str) for pattern in latex_patterns)
    
    if has_latex and '$' not in text_str:
        # 自动包裹整个文本
        return f'${text_str}$'
    
    return text_str


async def _get_review_task_or_error(
    db: AsyncSession,
    user_id: int
) -> Task:
    """
    获取用户当前的进行中评分任务（新设计：不关联具体题目）
    """
    now = datetime.utcnow()
    
    # 先查找 IN_PROGRESS 的任务
    result = await db.execute(
        select(Task).where(
            Task.user_id == user_id,
            Task.task_type == TaskType.REVIEW_PROBLEM,
            Task.status == TaskStatus.IN_PROGRESS
        ).order_by(Task.claimed_at.asc())
    )
    
    task = result.scalars().first()
    
    # 如果没有 IN_PROGRESS 的任务，检查是否有被错误标记为 SUBMITTED 的任务
    if not task:
        # 查找 SUBMITTED 状态的任务
        result = await db.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.task_type == TaskType.REVIEW_PROBLEM,
                Task.status == TaskStatus.SUBMITTED
            ).order_by(Task.claimed_at.desc())
        )
        submitted_task = result.scalars().first()
        
        if submitted_task:
            # 检查是否有未完成的评分
            review_count_result = await db.execute(
                select(func.count(Review.id))
                .where(
                    and_(
                        Review.task_id == submitted_task.id,
                        Review.innovation_score.isnot(None),
                        Review.rigor_score.isnot(None)
                    )
                )
            )
            completed_reviews = review_count_result.scalar() or 0
            
            # 如果还有未完成的评分，将任务状态改回 IN_PROGRESS
            if completed_reviews < submitted_task.total_count:
                submitted_task.status = TaskStatus.IN_PROGRESS
                submitted_task.submitted_at = None
                await db.commit()
                task = submitted_task
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您没有进行中的评分任务，请先领取任务"
        )
    
    if task.expires_at and now > task.expires_at:
        task.status = TaskStatus.TIMEOUT
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务已超时"
        )
    return task


# ==================== Pydantic 模型 ====================

class ChoicesResponse(BaseModel):
    """4选1选项响应"""
    problem_id: int
    problem_content: dict
    choices: List[str]
    correct_index: int  # 仅用于后端验证，不返回给前端


class VerifyCorrectnessRequest(BaseModel):
    """验证正确性请求"""
    selected_index: int = Field(..., ge=0, le=10, description="选择的选项索引")
    selected_answer: Optional[str] = Field(None, description="选择的答案文本（用于确保顺序一致）")
    correct_index: Optional[int] = Field(None, description="正确答案的索引（来自获取选项接口）")
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

@router.get("/next-problem", summary="获取下一个待评分题目及其选项")
async def get_next_problem(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取下一个待评分题目及其4选1选项（新设计API）
    
    - 自动查询当前任务下一个可评分的题目
    - 返回题目选项和正确答案索引
    
    如果没有可评分的题目，返回404
    """
    # 1. 校验用户有进行中的评分任务
    task = await _get_review_task_or_error(db, current_user.id)
    
    # 2. 查询该任务下的Review记录（新逻辑：领取任务时已创建）
    # 优先返回已领取但未完成的题目
    pending_review_result = await db.execute(
        select(Review, ValidatedProblemExport)
        .join(ValidatedProblemExport, Review.validated_problem_id == ValidatedProblemExport.id)
        .where(
            and_(
                Review.task_id == task.id,
                Review.reviewer_id == current_user.id,
                # 还没完成评分（两种情况：1.还没验证正确性 2.验证了但还没打分）
                or_(
                    Review.innovation_score.is_(None),
                    Review.rigor_score.is_(None)
                )
            )
        )
        .limit(1)
    )
    result_row = pending_review_result.first()
    
    if not result_row:
        # 没有待评分的题目了，任务完成
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有可评分的题目了，您的评分任务已完成"
        )
    
    review, problem = result_row
    
    # 3. 计算进度（查询已完成的评分数量）
    completed_count_result = await db.execute(
        select(func.count(Review.id))
        .where(
            and_(
                Review.task_id == task.id,
                Review.innovation_score.isnot(None),
                Review.rigor_score.isnot(None)
            )
        )
    )
    completed_count = completed_count_result.scalar() or 0
    
    # 4. 生成3个相似的错误答案
    try:
        similar_result = await gpt_service.generate_similar_answers(
            problem=str(problem.content) if problem.content else "",
            correct_answer=problem.answer or "",
            count=3
        )
        
        if similar_result["success"]:
            choices = [f"正确答案是：{problem.answer}"] + similar_result["similar_answers"][:3]
        else:
            raise Exception("GPT调用失败")
    except Exception as e:
        # GPT调用失败时使用mock数据（保持LaTeX格式）
        import re
        # 提取答案中的数字
        answer_str = str(problem.answer)
        # 生成相似但错误的答案
        mock_wrong_answers = []
        
        # 尝试提取数字并生成相似答案
        numbers = re.findall(r'-?\d+\.?\d*', answer_str)
        if numbers:
            base_num = float(numbers[0])
            mock_wrong_answers = [
                answer_str.replace(str(numbers[0]), str(base_num + 1)),
                answer_str.replace(str(numbers[0]), str(base_num - 1)),
                answer_str.replace(str(numbers[0]), str(base_num * 2))
            ]
        else:
            # 如果没有数字，使用通用错误答案
            mock_wrong_answers = [
                f"{answer_str} + 1",
                f"{answer_str} - 1", 
                f"2{answer_str}"
            ]
        
        # 6. 组合正确答案和错误答案
        choices = [problem.answer] + mock_wrong_answers[:3]
    
    # 7. 自动包裹LaTeX公式
    choices = [auto_wrap_latex(choice) for choice in choices]
    
    # 8. 随机打乱选项
    correct_index = 0
    combined = list(enumerate(choices))
    random.shuffle(combined)
    
    shuffled_choices = []
    for original_idx, choice in combined:
        shuffled_choices.append(choice)
        if original_idx == 0:
            correct_index = len(shuffled_choices) - 1
    
    return {
        "validated_problem_id": problem.id,
        "problem_content": problem.content,
        "problem_explanation": problem.explanation,
        "choices": shuffled_choices,
        "correct_index": correct_index,
        "instruction": "请选择你认为正确的答案：",
        "progress": {
            "completed": completed_count,
            "current": min(completed_count + 1, task.total_count),  # 当前正在评第几题
            "total": task.total_count
        }
    }


@router.get("/problem/{validated_problem_id}/choices", summary="获取4选1选项（正确性验证）")
async def get_problem_choices(
    validated_problem_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取题目的4选1选项用于正确性验证（新设计：动态查询可评分题目）
    
    - 1个正确答案
    - 3个由GPT生成的相似错误答案
    
    选项顺序随机打乱
    """
    # 1. 校验用户有进行中的评分任务
    task = await _get_review_task_or_error(db, current_user.id)
    
    # 2. 查询该任务下已评分的题目ID列表
    reviewed_ids_result = await db.execute(
        select(Review.validated_problem_id)
        .where(Review.task_id == task.id)
    )
    reviewed_ids = [row[0] for row in reviewed_ids_result.fetchall()]
    
    # 3. 查询已提交的出题任务
    submitted_creation_tasks_subquery = (
        select(Task.id)
        .where(
            Task.task_type == TaskType.CREATE_PROBLEM,
            Task.status == TaskStatus.SUBMITTED
        )
    )
    
    # 4. 验证请求的题目是否可评分（review_count 实时更新，直接使用）
    problem_query = (
        select(ValidatedProblemExport)
        .where(
            ValidatedProblemExport.id == validated_problem_id,
            # 排除自己出的题目
            ValidatedProblemExport.user_id != current_user.id,
            # 只选择已提交的题目
            ValidatedProblemExport.task_id.in_(submitted_creation_tasks_subquery),
            # 评分数量还没达到上限（review_count 实时更新，直接使用）
            ValidatedProblemExport.review_count < 3
        )
    )
    
    result = await db.execute(problem_query)
    problem = result.scalar_one_or_none()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在或不可评分"
        )
    
    # 5. 检查是否已评分过
    if validated_problem_id in reviewed_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已经评分过这道题目了"
        )
    
    # 6. 检查用户在其他任务中是否评分过此题
    already_reviewed = await db.execute(
        select(func.count(Review.id))
        .where(
            Review.validated_problem_id == validated_problem_id,
            Review.reviewer_id == current_user.id
        )
    )
    if already_reviewed.scalar() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已经评分过这道题目了"
        )
    
    # ValidatedProblemExport 的数据直接在 PostgreSQL 中
    problem_content = problem.content
    problem_answer = problem.answer
    problem_explanation = problem.explanation
    
    # 生成3个相似的错误答案
    similar_result = await gpt_service.generate_similar_answers(
        problem=str(problem_content) if problem_content else "",
        correct_answer=problem_answer or "",
        count=3
    )
    
    if not similar_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成选项失败"
        )
    
    # 组合正确答案和错误答案
    choices = [f"正确答案是：{problem_answer}"] + similar_result["similar_answers"][:3]
    
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
        "validated_problem_id": problem.id,
        "problem_content": problem_content,
        "problem_explanation": problem_explanation,
        "choices": shuffled_choices,
        "correct_index": correct_index,  # 在实际应用中，这个不应该返回给前端
        "instruction": "请选择你认为正确的答案："
    }


@router.post("/problem/{validated_problem_id}/verify", summary="提交正确性验证")
async def verify_correctness(
    validated_problem_id: int,
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
    # 查询题目（从 ValidatedProblemExport 表）
    result = await db.execute(
        select(ValidatedProblemExport).where(ValidatedProblemExport.id == validated_problem_id)
    )
    problem = result.scalar_one_or_none()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    # 不能评分自己的题目
    if problem.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能评分自己出的题目"
        )

    # 校验并获取对应的评分任务（新设计：不需要传入题目ID）
    task = await _get_review_task_or_error(db, current_user.id)
    
    # 检查该题目在当前任务中是否已有评分记录（防止重复提交）
    existing_review_result = await db.execute(
        select(Review).where(
            and_(
                Review.task_id == task.id,
                Review.validated_problem_id == validated_problem_id
            )
        )
    )
    existing_review = existing_review_result.scalar_one_or_none()
    
    # ValidatedProblemExport 的数据直接在 PostgreSQL 中
    problem_answer = problem.answer
    problem_explanation = problem.explanation
    
    # ⭐ 新逻辑：Review记录已在领取任务时创建，这里只需更新
    if not existing_review:
        # 如果没有Review记录，说明用户没有通过正常流程领取任务
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未找到评分记录，请先领取评分任务"
        )
    
    # 如果已经完成过正确性验证，直接返回
    if existing_review.is_answer_correct is not None:
        if existing_review.is_answer_correct:
            return {
                "success": True,
                "is_correct": True,
                "review_id": existing_review.id,
                "message": "✅ 该题目已完成正确性验证，请继续评分。",
                "next_step": "scoring"
            }
        else:
            return {
                "success": True,
                "is_correct": False,
                "review_id": existing_review.id,
                "message": "❌ 该题目已完成正确性验证。",
                "problem_explanation": problem_explanation,
                "correct_answer": problem_answer,
                "question": "请判断：题目的解析和答案是否正确？",
                "next_step": "manual_verification"
            }
    
    # 判定正确性（使用传回的选项文本优先，避免顺序不一致）
    is_correct = False
    if request.selected_answer is not None:
        is_correct = str(request.selected_answer).strip() == str(problem_answer).strip()
    elif request.correct_index is not None:
        is_correct = (request.selected_index == request.correct_index)
    
    # 更新现有的Review记录
    existing_review.is_answer_correct = is_correct
    existing_review.correctness_verification = {
        "selected_index": request.selected_index,
        "selected_answer": request.selected_answer,
        "correct_index": request.correct_index,
        "user_judgment": request.user_answer if not is_correct else None
    }
    
    await db.commit()
    await db.refresh(existing_review)
    
    review = existing_review  # 使用现有记录
    
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
            "problem_explanation": problem_explanation,
            "correct_answer": problem_answer,
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
    
    # 校验任务存在且未过期
    task = None
    if review.task_id:
        task_result = await db.execute(select(Task).where(Task.id == review.task_id))
        task = task_result.scalar_one_or_none()
    if not task:
        # 尝试获取当前用户的进行中评分任务
        try:
            task = await _get_review_task_or_error(db, current_user.id)
            review.task_id = task.id
        except HTTPException:
            task = None
    
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
    
    # ⚠️ 重要：flush 确保后续查询能看到 review 状态的更改
    await db.flush()
    
    # 更新题目的平均评分（新设计：使用ValidatedProblemExport）
    # 使用 FOR UPDATE 锁定行，防止并发问题
    validated_problem_id = review.validated_problem_id
    if validated_problem_id:
        result = await db.execute(
            select(ValidatedProblemExport)
            .where(ValidatedProblemExport.id == validated_problem_id)
            .with_for_update()  # 添加行锁，防止并发更新
        )
        validated_problem = result.scalar_one_or_none()
        
        if validated_problem:
            # 检查是否已经达到3人评分上限（防止并发导致超过3人）
            current_review_count = await db.execute(
                select(func.count(Review.id))
                .where(
                    and_(
                        Review.validated_problem_id == validated_problem.id,
                        Review.status == ReviewStatus.APPROVED
                    )
                )
            )
            actual_count = current_review_count.scalar() or 0
            
            if actual_count > 3:
                # 如果已经超过3人评分，拒绝本次评分
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该题目已达到评分人数上限（3人）"
                )
            
            # 重新计算平均分（只计算已完成评分的）
            avg_result = await db.execute(
                select(
                    func.avg(Review.innovation_score).label("avg_innovation"),
                    func.avg(Review.rigor_score).label("avg_rigor")
                )
                .where(
                    and_(
                        Review.validated_problem_id == validated_problem.id,
                        Review.status == ReviewStatus.APPROVED
                    )
                )
            )
            avg_stats = avg_result.one()
            
            # 计算所有评分人数（包括PENDING和APPROVED，用于限制3人上限）
            count_result = await db.execute(
                select(func.count(Review.id))
                .where(Review.validated_problem_id == validated_problem.id)
            )
            total_review_count = count_result.scalar() or 0
            
            validated_problem.avg_innovation_score = float(avg_stats.avg_innovation) if avg_stats.avg_innovation else None
            validated_problem.avg_rigor_score = float(avg_stats.avg_rigor) if avg_stats.avg_rigor else None
            validated_problem.review_count = total_review_count  # 使用所有Review的数量，而不只是APPROVED的
    
    # 增加用户的评分完成计数
    current_user.reviews_completed_count += 1
    
    # 检查任务是否完成（修正：只统计已完成评分的Review）
    if task:
        review_count_result = await db.execute(
            select(func.count(Review.id))
            .where(
                and_(
                    Review.task_id == task.id,
                    Review.innovation_score.isnot(None),
                    Review.rigor_score.isnot(None)
                )
            )
        )
        completed_reviews = review_count_result.scalar() or 0
        
        if completed_reviews >= task.total_count:
            task.status = TaskStatus.SUBMITTED
            task.submitted_at = datetime.utcnow()
    
    # 创建奖励交易（评分奖励）
    # 计算交易后余额
    current_balance = await current_user.calculate_balance(db)
    new_balance = current_balance + settings.REVIEW_REWARD
    
    transaction = Transaction(
        user_id=current_user.id,
        amount=settings.REVIEW_REWARD,
        transaction_type=TransactionType.REVIEW_REWARD,
        related_problem_id=review.problem_id,
        related_task_id=review.task_id,
        status=TransactionStatus.CONFIRMED,  # 评分奖励立即到账
        description=f"评分题目 #{review.validated_problem_id}",
        balance_after=new_balance,
        confirmed_at=datetime.utcnow()
    )
    
    db.add(transaction)
    await db.flush()  # 确保transaction已保存
    
    # 刷新用户余额缓存
    await current_user.refresh_balance(db)
    
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
                "validated_problem_id": r.validated_problem_id,  # 使用新字段
                "is_answer_correct": r.is_answer_correct,
                "innovation_score": r.innovation_score,
                "rigor_score": r.rigor_score,
                "is_vetoed": r.is_vetoed,
                "status": r.status.value,
                "created_at": r.created_at.isoformat() if r.created_at else None
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


# ==================== 新评分流程 API（基于 validated_problem_exports）====================

@router.get("/export/{export_id}/choices", summary="获取4选1选项（新评分流程）")
async def get_export_choices(
    export_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取已验证题目的4选1选项用于正确性验证（新评分流程）
    
    - 从 validated_problem_exports 表获取题目
    - 1个正确答案
    - 3个由GPT生成的相似错误答案
    """
    # 查询已验证题目
    result = await db.execute(
        select(ValidatedProblemExport).where(ValidatedProblemExport.id == export_id)
    )
    export = result.scalar_one_or_none()
    
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    # 不能评分自己的题目
    if export.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能评分自己出的题目"
        )
    
    # 校验任务（评分任务必须存在且未超时）
    task = await _get_review_task_or_error(db, current_user.id, validated_problem_id=export.id)
    
    # 生成3个相似的错误答案
    similar_result = await gpt_service.generate_similar_answers(
        problem=export.content,
        correct_answer=export.answer,
        count=3
    )
    
    if not similar_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成选项失败"
        )
    
    # 组合正确答案和错误答案
    choices = [f"正确答案是：{export.answer}"] + similar_result["similar_answers"][:3]
    
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
        "export_id": export.id,
        "problem_content": export.content,
        "problem_explanation": export.explanation,
        "choices": shuffled_choices,
        "correct_index": correct_index,
        "instruction": "请选择你认为正确的答案："
    }


@router.post("/export/{export_id}/verify", summary="提交正确性验证（新评分流程）")
async def verify_export_correctness(
    export_id: int,
    request: VerifyCorrectnessRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    提交正确性验证结果（新评分流程）
    
    流程：
    1. 用户选择4个选项中的一个
    2. 如果选对 → 题目正确，进入评分阶段
    3. 如果选错 → 展示解析和答案，让用户判断题目是否有问题
    """
    # 查询已验证题目
    result = await db.execute(
        select(ValidatedProblemExport).where(ValidatedProblemExport.id == export_id)
    )
    export = result.scalar_one_or_none()
    
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    # 不能评分自己的题目
    if export.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能评分自己出的题目"
        )
    
    # 校验任务（新设计：不需要传入题目ID）
    task = await _get_review_task_or_error(db, current_user.id)
    
    # 检查是否已经评分过
    existing_review_result = await db.execute(
        select(Review).where(
            and_(
                Review.validated_problem_id == export.id,
                Review.reviewer_id == current_user.id
            )
        )
    )
    existing_review = existing_review_result.scalar_one_or_none()
    
    if existing_review:
        # 已经完成验证，返回之前的结果
        if existing_review.is_answer_correct:
            return {
                "success": True,
                "is_correct": True,
                "review_id": existing_review.id,
                "message": "✅ 该题目已完成正确性验证（答案正确）",
                "next_step": "scoring"
            }
        else:
            return {
                "success": True,
                "is_correct": False,
                "review_id": existing_review.id,
                "message": "❌ 该题目已完成正确性验证。",
                "problem_explanation": export.explanation,
                "correct_answer": export.answer,
                "question": "请判断：题目的解析和答案是否正确？",
                "next_step": "manual_verification"
            }
    
    # 判定正确性
    is_correct = False
    if request.selected_answer is not None:
        is_correct = str(request.selected_answer).strip() == str(export.answer).strip()
    elif request.correct_index is not None:
        is_correct = (request.selected_index == request.correct_index)
    
    # 创建评分记录
    review = Review(
        validated_problem_id=export.id,  # 使用新字段
        reviewer_id=current_user.id,
        task_id=task.id,
        is_answer_correct=is_correct,
        correctness_verification={
            "selected_index": request.selected_index,
            "selected_answer": request.selected_answer,
            "correct_index": request.correct_index,
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
            "problem_explanation": export.explanation,
            "correct_answer": export.answer,
            "question": "请判断：题目的解析和答案是否正确？",
            "next_step": "manual_verification"
        }

