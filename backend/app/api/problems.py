"""
题目管理API
包含完整的出题流程：
1. 母题验证（单题/批量）
2. 题目创建
3. 题目变形（DeepSeek）
4. 三维质检（难度+原创性+严谨性）
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel, Field
import asyncio
import json

from app.database import get_db
from app.models import (
    User, UserRole,
    Problem, ProblemStatus, ProblemSourceType,
    ProblemValidationStatus, HumanReviewStatus, MaterialCategory,
    ValidationRecord, Transaction, TransactionType, TransactionStatus,
    Task, TaskType, TaskStatus, ValidatedProblemExport
)
from app.api.deps import get_current_user
from app.services.ocr_service import ocr_service
from app.services.validation_service import validation_service, quality_check_service
from app.services.difficulty_check_service import difficulty_check_service
from app.services.originality_check_service import originality_check_service
from app.services.rigor_check_service import rigor_check_service
from app.services.deep_transformer_service import deep_transformer_service
from app.services.problem_storage import get_problem_storage_service
from app.services.export_service import export_service
from app.config import settings
from fastapi.responses import StreamingResponse


router = APIRouter()


async def _mark_create_task_progress(
    db: AsyncSession,
    user_id: int,
    problem_id: int
):
    """创建题目后，自动推进进行中的出题任务进度"""
    now = datetime.utcnow()
    result = await db.execute(
        select(Task).where(
            Task.user_id == user_id,
            Task.task_type == TaskType.CREATE_PROBLEM,
            Task.status == TaskStatus.IN_PROGRESS
        ).order_by(Task.claimed_at.asc())
    )
    task = result.scalars().first()
    if not task:
        return
    # 超时处理
    if task.expires_at and now > task.expires_at:
        task.status = TaskStatus.TIMEOUT
        await db.commit()
        return
    task.completed_count = (task.completed_count or 0) + 1
    # 记录最近创建的题目ID
    task.problem_id = problem_id
    if task.completed_count >= task.total_count:
        task.status = TaskStatus.SUBMITTED
        task.submitted_at = now
    await db.commit()


async def _rollback_create_task_progress(
    db: AsyncSession,
    user_id: int
) -> bool:
    """
    回退出题任务额度：
    - 找到该用户的出题任务（create_problem），状态为 IN_PROGRESS 或 SUBMITTED，且 completed_count > 0
    - completed_count -1，若原本是 SUBMITTED 则改回 IN_PROGRESS（撤销提交）
    """
    result = await db.execute(
        select(Task).where(
            Task.user_id == user_id,
            Task.task_type == TaskType.CREATE_PROBLEM,
            Task.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.SUBMITTED]),
            Task.completed_count > 0
        ).order_by(Task.claimed_at.desc())
    )
    task = result.scalars().first()
    if not task:
        return False
    task.completed_count = max(0, (task.completed_count or 0) - 1)
    if task.status == TaskStatus.SUBMITTED:
        task.status = TaskStatus.IN_PROGRESS
        task.submitted_at = None
    await db.commit()
    return True


# ==================== Pydantic 模型 ====================

class OCRRequest(BaseModel):
    """OCR识别请求"""
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    extract_answer: bool = True


class ValidateProblemRequest(BaseModel):
    """单题验证请求"""
    problem: str = Field(..., description="题目内容")
    answer: str = Field(..., description="标准答案")
    explanation: Optional[str] = Field(None, description="解析")


class BatchValidateRequest(BaseModel):
    """批量验证请求（最多10题）"""
    problems: List[ValidateProblemRequest] = Field(..., max_items=10)


class CreateProblemRequest(BaseModel):
    """创建题目请求"""
    title: str = Field(..., max_length=200)
    content: dict = Field(..., description="题目内容（JSON格式）")
    explanation: Optional[str] = None
    answer: str
    category: str
    source_type: str = "manual"
    ocr_image_url: Optional[str] = None
    parent_problem_id: Optional[int] = None


class GenerateVariantRequest(BaseModel):
    """生成变体请求"""
    custom_prompt: Optional[str] = Field(None, description="自定义变形prompt")


class QualityCheckContentRequest(BaseModel):
    """内容质检请求（无需题目ID）"""
    content: str = Field(..., description="题目内容")
    answer: str = Field(..., description="标准答案")
    explanation: Optional[str] = Field(None, description="解析")


class ProblemResponse(BaseModel):
    """题目响应模型"""
    id: int
    title: str
    content: dict
    explanation: Optional[str]
    answer: str
    category: str
    source_type: str
    status: str
    validation_status: str
    human_review_status: str
    variant_count: int
    quality_check: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== API 路由 ====================

@router.post("/ocr", summary="OCR识别图片中的题目")
async def recognize_image(
    request: OCRRequest,
    current_user: User = Depends(get_current_user)
):
    """
    使用OCR识别图片中的数学题目
    
    支持三种方式：
    - image_url: 图片URL
    - image_base64: Base64编码的图片
    - image_path: 本地图片路径（通过文件上传）
    """
    result = await ocr_service.recognize_image(
        image_url=request.image_url,
        image_base64=request.image_base64,
        extract_answer=request.extract_answer
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "OCR识别失败")
        )
    
    return result


@router.post("/validate", summary="单题验证（Doubao 8次对抗验证）")
async def validate_single_problem(
    request: ValidateProblemRequest,
    current_user: User = Depends(get_current_user)
):
    """
    验证单个题目的难度（Doubao对抗验证）
    
    验证逻辑：AI回答8次，正确次数≤4次认为难度合格
    
    返回：
    - is_passed: 是否通过验证
    - correct_count: 8次中正确的次数
    - verdict: "难度合格" 或 "题目太简单"
    """
    result = await validation_service.validate_difficulty(
        problem=request.problem,
        answer=request.answer,
        explanation=request.explanation,
        attempts=settings.VALIDATION_ATTEMPTS
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "验证失败")
        )
    
    # 返回验证结果和建议
    return {
        **result,
        "recommendation": (
            "✅ 这个题目难度合格，可以作为母题进行下一步创新"
            if result["is_passed"]
            else "⚠️ 这个题目可能偏简单，但也可以用作母题继续创新"
        )
    }


@router.post("/validate-batch", summary="批量验证（最多10题）")
async def validate_batch_problems(
    request: BatchValidateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    批量验证多个题目（最多10题）
    
    并发执行验证，提高效率
    """
    if len(request.problems) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="最多一次验证10个题目"
        )
    
    # 并发验证所有题目
    tasks = [
        validation_service.validate_difficulty(
            problem=p.problem,
            answer=p.answer,
            explanation=p.explanation,
            attempts=settings.VALIDATION_ATTEMPTS
        )
        for p in request.problems
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 整理结果
    validated_problems = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            validated_problems.append({
                "index": i + 1,
                "success": False,
                "error": str(result)
            })
        else:
            validated_problems.append({
                "index": i + 1,
                **result
            })
    
    # 统计通过情况
    passed_count = sum(1 for r in validated_problems if r.get("is_passed", False))
    
    return {
        "success": True,
        "total": len(request.problems),
        "passed": passed_count,
        "failed": len(request.problems) - passed_count,
        "results": validated_problems
    }


@router.post("/create", response_model=ProblemResponse, summary="创建题目")
async def create_problem(
    request: CreateProblemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新题目（母题或变体）
    
    如果指定了parent_problem_id，则作为变体题目创建
    """
    # 验证类别
    try:
        category_enum = MaterialCategory(request.category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的类别: {request.category}"
        )
    
    # 如果是变体，检查母题是否存在和变形次数
    parent_problem = None
    if request.parent_problem_id:
        result = await db.execute(
            select(Problem).where(Problem.id == request.parent_problem_id)
        )
        parent_problem = result.scalar_one_or_none()
        
        if not parent_problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="母题不存在"
            )
        
        if parent_problem.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能基于其他用户的题目创建变体"
            )
        
        if parent_problem.variant_count >= 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="母题已达到最大变形次数（10次）"
            )
    
    # 根据是否有 parent_problem_id 区分母题和变体的状态
    if request.parent_problem_id:
        # 变体：直接设为待审核状态，可被领取评分
        problem_status = ProblemStatus.PENDING_REVIEW
        problem_validation_status = ProblemValidationStatus.PASSED
    else:
        # 母题：保持草稿状态
        problem_status = ProblemStatus.DRAFT
        problem_validation_status = ProblemValidationStatus.NOT_VALIDATED
    
    # 使用ProblemStorageService创建题目（PostgreSQL + MongoDB）
    try:
        storage_service = get_problem_storage_service()
        
        # 分离元数据和内容
        problem_metadata = {
            "creator_id": current_user.id,
            "parent_problem_id": request.parent_problem_id,
            "title": request.title,
            "category": category_enum,
            "source_type": ProblemSourceType(request.source_type),
            "ocr_image_url": request.ocr_image_url,
            "status": problem_status,
            "validation_status": problem_validation_status,
            "human_review_status": HumanReviewStatus.PENDING,
            "variant_count": 0
        }
        
        problem_content = {
            "content": request.content,
            "explanation": request.explanation,
            "answer": request.answer,
            "validation_result": None,
            "quality_check_details": None
        }
        
        # 创建题目（同时写入PostgreSQL和MongoDB）
        problem_id, mongo_id = await storage_service.create_problem(
            db=db,
            problem_metadata=problem_metadata,
            problem_content=problem_content
        )
        await _mark_create_task_progress(db, current_user.id, problem_id)
        
        # 如果是变体，更新母题的变形次数和用户的出题计数
        if parent_problem:
            parent_problem.variant_count += 1
            current_user.problems_created_count += 1
            await db.commit()
        
        # 获取完整题目数据返回
        full_problem = await storage_service.get_problem(db, problem_id)
        
        return full_problem
        
    except RuntimeError:
        # MongoDB未配置，使用PostgreSQL存储（兼容模式）
        new_problem = Problem(
            creator_id=current_user.id,
            parent_problem_id=request.parent_problem_id,
            title=request.title,
            content=request.content,
            explanation=request.explanation,
            answer=request.answer,
            category=category_enum,
            source_type=ProblemSourceType(request.source_type),
            ocr_image_url=request.ocr_image_url,
            status=problem_status,
            validation_status=problem_validation_status,
            human_review_status=HumanReviewStatus.PENDING,
            variant_count=0
        )
        
        db.add(new_problem)
        
        if parent_problem:
            parent_problem.variant_count += 1
            current_user.problems_created_count += 1
        
        await db.commit()
        await db.refresh(new_problem)
        
        await _mark_create_task_progress(db, current_user.id, new_problem.id)
        
        return new_problem


@router.post("/{problem_id}/generate-variant", summary="生成题目变体")
async def generate_variant(
    problem_id: int,
    request: GenerateVariantRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    基于母题生成变体（使用Gemini API）
    
    要求：
    - 新题目与原题目必须有明显不同
    - 一个母题最多变形10次
    """
    # 查询母题
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    parent_problem = result.scalar_one_or_none()
    
    if not parent_problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="母题不存在"
        )
    
    if parent_problem.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能基于其他用户的题目生成变体"
        )
    
    if parent_problem.variant_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="母题已达到最大变形次数（10次）"
        )
    
    # 生成变体：优先从 MongoDB 读取完整内容，取不到再用 Postgres 字段
    try:
        storage_service = get_problem_storage_service()
        full_problem = await storage_service.get_problem(db, problem_id)
        problem_content = full_problem.get("content", {})
        problem_answer = full_problem.get("answer", "") or ""
        problem_explanation = full_problem.get("explanation", "") or ""
    except (RuntimeError, ValueError, Exception) as e:
        # MongoDB未配置或获取失败，使用Postgres字段作为后备
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"无法从MongoDB获取题目内容，使用Postgres后备: {str(e)}")
        problem_content = parent_problem.content if parent_problem.content else {}
        problem_answer = parent_problem.answer or ""
        problem_explanation = parent_problem.explanation or ""

    if isinstance(problem_content, dict):
        # 若有 text 字段，用 text；否则序列化整个内容
        problem_text = problem_content.get("text") or json.dumps(problem_content, ensure_ascii=False)
    else:
        problem_text = problem_content or ""

    try:
        # 调用 deep_transformer_service 生成变体（使用 Gemini API）
        variant_result = await deep_transformer_service.generate_problem_variant_with_explanation(
            original_content=problem_text,
            original_explanation=problem_explanation,
            original_answer=problem_answer,
            modification_requirement=request.custom_prompt or "",
            max_tokens=10000,
            temperature=0.7
        )
        
        # 验证返回的数据
        new_problem = variant_result.get("variant_content", "").strip()
        new_answer = variant_result.get("variant_answer", "").strip()
        new_explanation = variant_result.get("variant_explanation", "").strip()
        
        if not new_problem or not new_answer:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"生成变体失败：内容为空。new_problem={new_problem[:100] if new_problem else ''}, new_answer={new_answer[:100] if new_answer else ''}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="生成变体失败：AI返回的内容为空或格式不正确"
            )
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"生成变体时发生异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成变体失败: {str(e)}"
        )
    
    # 返回生成的变体内容给前端，用于创建题目
    return {
        "success": True,
        "new_problem": new_problem,
        "new_answer": new_answer,
        "new_explanation": new_explanation,
        "model": variant_result.get("model"),
        "tokens": variant_result.get("tokens"),
    }


@router.post("/quality-check-content", summary="内容质检（无需题目ID）")
async def quality_check_content(
    request: QualityCheckContentRequest,
    current_user: User = Depends(get_current_user),
):
    """
    对题目内容进行三维质检（无需先保存到数据库）
    用于变体生成后、写入数据库前的质检
    
    三个维度：
    1. 难度检测（Doubao 8次验证）
    2. 原创性检测（GPT-4o Research）
    3. 数学严谨性检测（GPT-4o）
    """
    # 处理内容格式
    problem_content = request.content
    if isinstance(problem_content, dict):
        problem_content = json.dumps(problem_content, ensure_ascii=False)
    
    # 执行质检
    check_result = await quality_check_service.full_quality_check(
        problem=problem_content,
        answer=request.answer,
        explanation=request.explanation or ""
    )
    
    if not check_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=check_result.get("error", "质检失败")
        )
    
    return {
        "success": True,
        "all_passed": check_result["all_passed"],
        **check_result,
        "next_step": (
            "✅ 质检全部通过！可以提交题目。"
            if check_result["all_passed"]
            else "❌ 质检未通过，请根据反馈修改题目或选择放弃。"
        )
    }


# ====================== 独立质检 API ======================

@router.post("/check-difficulty", summary="单独检测难度")
async def check_difficulty_only(
    request: QualityCheckContentRequest,
    current_user: User = Depends(get_current_user),
):
    """
    单独检测题目难度（豆包对抗验证 + GPT-4o 答案校验）
    比完整质检更快，适合单独调试难度
    """
    problem_content = request.content
    if isinstance(problem_content, dict):
        problem_content = json.dumps(problem_content, ensure_ascii=False)
    
    result = await difficulty_check_service.validate_difficulty(
        problem=problem_content,
        answer=request.answer,
        explanation=request.explanation or ""
    )
    
    return {
        "success": result.get("success", False),
        "difficulty": result,
        "is_passed": result.get("is_passed", False),
    }


@router.post("/check-originality", summary="单独检测原创性")
async def check_originality_only(
    request: QualityCheckContentRequest,
    current_user: User = Depends(get_current_user),
):
    """
    单独检测题目原创性（GPT-5.2 Responses API + web_search）
    """
    problem_content = request.content
    if isinstance(problem_content, dict):
        problem_content = json.dumps(problem_content, ensure_ascii=False)
    
    result = await originality_check_service.check_originality(problem=problem_content)
    
    return {
        "success": result.get("success", False),
        "originality": result,
        "is_original": result.get("is_original", False),
    }


@router.post("/check-rigor", summary="单独检测严谨性")
async def check_rigor_only(
    request: QualityCheckContentRequest,
    current_user: User = Depends(get_current_user),
):
    """
    单独检测数学严谨性（GPT-5.2）
    检查题目表述、条件完整性、答案正确性等
    """
    problem_content = request.content
    if isinstance(problem_content, dict):
        problem_content = json.dumps(problem_content, ensure_ascii=False)
    
    result = await rigor_check_service.check_rigor(
        problem=problem_content,
        answer=request.answer,
        explanation=request.explanation or ""
    )
    
    return {
        "success": result.get("success", False),
        "rigor": result,
        "is_rigorous": result.get("is_rigorous", False),
    }


@router.post("/{problem_id}/quality-check", summary="三维质检")
async def quality_check(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    对题目进行三维质检：
    1. 难度检测（Doubao 8次验证）
    2. 原创性检测（GPT-4o Research）
    3. 数学严谨性检测（GPT-4o）
    
    三个维度都通过才算合格
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
    
    if problem.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能质检自己创建的题目"
        )
    
    # 获取完整题目内容（从MongoDB）
    try:
        storage_service = get_problem_storage_service()
        full_problem = await storage_service.get_problem(db, problem_id)
        problem_content = full_problem.get("content", {})
        problem_answer = full_problem.get("answer", "")
        problem_explanation = full_problem.get("explanation", "")
    except RuntimeError:
        # MongoDB未配置，使用PostgreSQL数据（兼容模式）
        problem_content = problem.content if problem.content else {}
        problem_answer = problem.answer if problem.answer else ""
        problem_explanation = problem.explanation if problem.explanation else ""
    
    # 执行质检
    problem.validation_status = ProblemValidationStatus.VALIDATING
    await db.commit()
    
    check_result = await quality_check_service.full_quality_check(
        problem=json.dumps(problem_content) if isinstance(problem_content, dict) else problem_content,
        answer=problem_answer,
        explanation=problem_explanation
    )
    
    if not check_result["success"]:
        problem.validation_status = ProblemValidationStatus.FAILED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=check_result.get("error", "质检失败")
        )
    
    # 更新题目质检结果
    problem.quality_check = check_result["summary"]
    problem.validation_status = (
        ProblemValidationStatus.PASSED
        if check_result["all_passed"]
        else ProblemValidationStatus.FAILED
    )
    problem.validation_completed_at = datetime.utcnow()
    
    # 如果质检通过，更新状态为待审核
    if check_result["all_passed"]:
        problem.status = ProblemStatus.PENDING_REVIEW
    
    # 更新MongoDB中的质检详情
    try:
        storage_service = get_problem_storage_service()
        await storage_service.update_problem_content(
            db=db,
            problem_id=problem_id,
            updates={"quality_check_details": check_result}
        )
    except RuntimeError:
        # MongoDB未配置，使用PostgreSQL存储（兼容模式）
        problem.quality_check_details = check_result
    
    await db.commit()
    
    # 保存验证记录
    for check_type, check_data in [
        ("difficulty", check_result["difficulty"]),
        ("originality", check_result["originality"]),
        ("rigor", check_result["rigor"])
    ]:
        validation_record = ValidationRecord(
            problem_id=problem.id,
            validation_type=check_type,
            ai_model=check_data.get("ai_model", "unknown"),
            is_passed=check_data.get("is_passed", False) if check_type == "difficulty" else check_data.get(f"is_{check_type.replace('ity', 'al') if check_type.endswith('ity') else check_type}", False),
            result_data=check_data
        )
        db.add(validation_record)
    
    await db.commit()
    await db.refresh(problem)
    
    return {
        "success": True,
        "problem_id": problem.id,
        "all_passed": check_result["all_passed"],
        **check_result,
        "next_step": (
            "✅ 质检全部通过！题目已进入人工审核队列，请等待审核结果。"
            if check_result["all_passed"]
            else "❌ 质检未通过，请根据反馈修改题目或选择放弃。"
        )
    }


@router.post("/{problem_id}/submit-for-review", summary="提交题目到审核")
async def submit_for_review(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    提交题目到人工审核队列
    要求：
    - 题目存在
    - 仅创建者或管理员可提交
    - 状态必须是 DRAFT（或尚未进入审核）
    - 质检必须通过（validation_status == PASSED）
    """
    result = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = result.scalar_one_or_none()
    
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
    
    # 权限检查
    if problem.creator_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权提交该题目")
    
    if problem.status not in [ProblemStatus.DRAFT, ProblemStatus.PENDING_REVIEW]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前状态不可提交审核")
    
    if problem.validation_status != ProblemValidationStatus.PASSED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="质检未通过，无法提交审核")
    
    problem.status = ProblemStatus.PENDING_REVIEW
    await db.commit()
    await db.refresh(problem)
    return problem


@router.post("/{problem_id}/approve", summary="管理员审核通过")
async def approve_problem(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员审核通过：
    - 功能可通过配置关闭（ADMIN_APPROVAL_ENABLED=False 时拒绝调用）
    - 仅 admin 可操作
    - 状态更新为 PUBLISHED
    - 记录人工审核通过
    - 发放出题奖励
    """
    if not settings.ADMIN_APPROVAL_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="管理员审核功能当前已关闭"
        )

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可审核")
    
    result = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = result.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
    
    problem.status = ProblemStatus.PUBLISHED
    problem.human_review_status = HumanReviewStatus.APPROVED
    problem.human_review_note = None
    problem.published_at = datetime.utcnow()
    
    # 发放出题奖励
    transaction = Transaction(
        user_id=problem.creator_id,
        amount=settings.PROBLEM_REWARD,
        transaction_type=TransactionType.PROBLEM_REWARD,
        related_problem_id=problem.id,
        status=TransactionStatus.CONFIRMED,
        description=f"题目 #{problem.id} 审核通过奖励",
        confirmed_at=datetime.utcnow()
    )
    db.add(transaction)
    
    # 更新用户余额
    user_result = await db.execute(select(User).where(User.id == problem.creator_id))
    creator = user_result.scalar_one_or_none()
    if creator:
        creator.balance += settings.PROBLEM_REWARD
        transaction.balance_after = creator.balance
    
    await db.commit()
    await db.refresh(problem)
    return problem


@router.post("/{problem_id}/reject", summary="管理员审核拒绝")
async def reject_problem(
    problem_id: int,
    reason: str = Form(..., description="拒绝理由"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员审核拒绝：
    - 功能可通过配置关闭（ADMIN_APPROVAL_ENABLED=False 时拒绝调用）
    - 状态退回 DRAFT
    - 记录人工审核状态和理由
    """
    if not settings.ADMIN_APPROVAL_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="管理员审核功能当前已关闭"
        )

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可审核")
    
    result = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = result.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
    
    problem.status = ProblemStatus.DRAFT
    problem.human_review_status = HumanReviewStatus.REJECTED
    problem.human_review_note = reason
    await db.commit()
    await db.refresh(problem)
    return problem


@router.post("/{problem_id}/rollback-task", summary="回退出题任务进度（撤销额度）")
async def rollback_task_progress(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    回退出题任务额度：
    - 限创建者或管理员
    - 将该用户的出题任务 completed_count -1，若任务已 SUBMITTED 则改回 IN_PROGRESS
    - 不删除题目，仅用于额度回退
    """
    result = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = result.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
    if problem.creator_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该题目")
    
    success = await _rollback_create_task_progress(db, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有可回退的出题任务额度")
    
    return {"success": True, "message": "已回退出题任务额度，如有需要请自行处理题目状态/删除"}


@router.get("/my-variants", summary="查看我创建的变体题目")
async def get_my_variants(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户创建的所有变体题目（仅返回必要字段）
    查询条件：creator_id = 当前用户 AND parent_problem_id IS NOT NULL
    返回字段：id, parent_problem_id, created_at
    """
    from sqlalchemy import func
    
    # 查询总数
    count_query = select(func.count(Problem.id)).where(
        and_(
            Problem.creator_id == current_user.id,
            Problem.parent_problem_id.isnot(None)
        )
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # 只查询必要字段：id, parent_problem_id, created_at
    # TODO: 以后可以在这里扩展返回更多字段，如 title, status, category 等
    query = select(
        Problem.id,
        Problem.parent_problem_id,
        Problem.created_at
    ).where(
        and_(
            Problem.creator_id == current_user.id,
            Problem.parent_problem_id.isnot(None)
        )
    ).order_by(Problem.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    return {
        "total": total,
        "items": [
            {
                "id": row.id,
                "parent_problem_id": row.parent_problem_id,
                "created_at": row.created_at
            }
            for row in rows
        ]
    }


@router.get("/my-problems", summary="查看我创建的题目")
async def get_my_problems(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查看当前用户创建的所有题目
    
    可按状态筛选
    """
    query = select(Problem).where(Problem.creator_id == current_user.id)
    
    if status:
        try:
            status_enum = ProblemStatus(status)
            query = query.where(Problem.status == status_enum)
        except ValueError:
            pass
    
    query = query.order_by(Problem.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    problems = result.scalars().all()
    
    return {
        "total": len(problems),
        "problems": [
            {
                "id": p.id,
                "title": p.title,
                "category": p.category.value if p.category else None,
                "status": p.status.value,
                "validation_status": p.validation_status.value,
                "human_review_status": p.human_review_status.value,
                "variant_count": p.variant_count,
                "created_at": p.created_at
            }
            for p in problems
        ]
    }


# ==================== 新增：题目验证和导出相关API ====================

def _safe_bool(value) -> bool:
    """
    安全地将值转换为布尔值
    处理可能的字符串 "true"/"false" 或 "True"/"False"
    
    Args:
        value: 要转换的值
        
    Returns:
        bool: 转换后的布尔值
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    if isinstance(value, (int, float)):
        return bool(value)
    return False


@router.post("/validate-and-save", summary="验证并保存题目（用于批量导出）")
async def validate_and_save_problem(
    problem: str = Form(...),
    answer: str = Form(...),
    explanation: str = Form(...),
    include_difficulty: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    验证题目并保存到导出列表
    
    流程：
    1. 检查用户是否有进行中的出题任务
    2. 检查已保存题目数量是否超过任务数量
    3. 可选：验证难度
    4. 二维质检（原创性 + 严谨性）
    5. 保存到待导出列表并更新任务进度
    
    不会创建正式的Problem记录，只保存到ValidatedProblemExport表
    """
    try:
        # 1. 检查用户是否有进行中的出题任务
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请先在任务管理中领取出题任务"
            )
        
        # 检查任务是否过期
        if task.expires_at and now > task.expires_at:
            task.status = TaskStatus.TIMEOUT
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="任务已超时，请重新领取任务"
            )
        
        # 2. 检查已保存的题目数量（未导出的）
        saved_count_result = await db.execute(
            select(func.count(ValidatedProblemExport.id)).where(
                ValidatedProblemExport.user_id == current_user.id,
                ValidatedProblemExport.is_exported == False
            )
        )
        saved_count = saved_count_result.scalar() or 0
        
        # 检查是否超过任务数量
        if saved_count >= task.total_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"已保存 {saved_count} 道题目，已达到任务上限 {task.total_count} 道。如需继续出题，请先删除已保存的题目或领取新任务"
            )
        
        # 3. 验证难度（可选）
        difficulty_result = None
        if include_difficulty:
            try:
                difficulty_result = await validation_service.validate_difficulty(
                    problem=problem,
                    answer=answer,
                    explanation=explanation,
                    attempts=settings.VALIDATION_ATTEMPTS
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"难度验证失败: {str(e)}")
                difficulty_result = {"success": False, "error": str(e)}
        
        # 4. 二维质检
        try:
            check_result = await quality_check_service.two_dimension_check(
                problem=problem,
                answer=answer,
                explanation=explanation
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"质检失败: {str(e)}")
            check_result = {
                "success": False,
                "all_passed": False,
                "originality": {"success": False, "error": f"质检异常: {str(e)}"},
                "rigor": {"success": False, "error": f"质检异常: {str(e)}"}
            }
        
        # 即使质检失败也保存，用于记录 AI 分析结果供参考
        # 安全地获取质检结果，如果失败则使用空字典
        originality_check = check_result.get("originality", {"success": False, "error": "质检异常"})
        rigor_check = check_result.get("rigor", {"success": False, "error": "质检异常"})
        
        # 5. 保存到导出列表
        validated_problem = ValidatedProblemExport(
            user_id=current_user.id,
            content=problem,
            answer=answer,
            explanation=explanation,
            difficulty_validation=difficulty_result,
            originality_check=originality_check,
            rigor_check=rigor_check,
            is_exported=False
        )
        
        db.add(validated_problem)
        
        # 6. 更新任务进度
        task.completed_count = (task.completed_count or 0) + 1
        
        # 7. 更新用户的出题数统计（用于仪表盘显示）
        current_user.problems_created_count = (current_user.problems_created_count or 0) + 1
        
        await db.commit()
        await db.refresh(validated_problem)
        
        # 安全地获取 all_passed 状态
        all_passed = check_result.get("all_passed", False)
        
        return {
            "success": True,
            "id": validated_problem.id,
            "all_passed": all_passed,
            "message": "题目已保存到导出列表" if all_passed else "题目未通过质检但已保存",
            "task_progress": {
                "completed": task.completed_count,
                "total": task.total_count,
                "remaining": task.total_count - task.completed_count
            },
            **check_result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"保存题目失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存题目失败: {str(e)}"
        )


@router.get("/export-validated", summary="导出已验证的题目到Excel")
async def export_validated_problems(
    only_passed: int = 1,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    导出当前用户验证过的题目到Excel
    
    Args:
        only_passed: 是否只导出二维质检都通过的题目 (0=全部导出, 1=仅通过的)
    
    Returns:
        Excel文件下载
    """
    try:
        # 查询待导出的题目
        query = select(ValidatedProblemExport).where(
            ValidatedProblemExport.user_id == current_user.id,
            ValidatedProblemExport.is_exported == False
        ).order_by(ValidatedProblemExport.created_at.asc())
        
        result = await db.execute(query)
        validated_problems = result.scalars().all()
        
        if not validated_problems:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="没有待导出的题目"
            )
        
        # 转换为字典列表
        problems_data = []
        for p in validated_problems:
            try:
                # 判断是否通过 - 使用 _safe_bool 处理可能的字符串 "true"/"false"
                originality_passed = _safe_bool(p.originality_check.get("is_original", False)) if p.originality_check else False
                rigor_passed = _safe_bool(p.rigor_check.get("is_rigorous", False)) if p.rigor_check else False
                all_passed = originality_passed and rigor_passed
                
                # 如果只导出通过的题目，跳过未通过的 (only_passed: 1=仅通过, 0=全部)
                if only_passed == 1 and not all_passed:
                    continue
                
                problems_data.append({
                    "content": p.content,
                    "answer": p.answer,
                    "explanation": p.explanation,
                    "difficulty_validation": p.difficulty_validation,
                    "originality_check": p.originality_check,
                    "rigor_check": p.rigor_check,
                    "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else None
                })
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"处理导出题目失败 {p.id}: {str(e)}")
                continue
        
        if not problems_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="没有通过质检的题目可导出"
            )
        
        # 生成Excel
        excel_file = export_service.export_to_excel(problems_data)
        
        # 标记为已导出
        for p in validated_problems:
            p.is_exported = True
            p.exported_at = datetime.utcnow()
        await db.commit()
        
        # 返回文件下载
        filename = f"验证题目_{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
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


@router.delete("/export-list/{problem_id}", summary="删除单个已验证题目")
async def delete_validated_problem(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除单个已验证题目
    
    删除后，任务的completed_count会减1，用户可以继续出题
    """
    try:
        # 查找题目
        result = await db.execute(
            select(ValidatedProblemExport).where(
                ValidatedProblemExport.id == problem_id,
                ValidatedProblemExport.user_id == current_user.id,
                ValidatedProblemExport.is_exported == False
            )
        )
        problem = result.scalar_one_or_none()
        
        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在或已导出"
            )
        
        # 删除题目
        await db.delete(problem)
        
        # 更新任务进度（减1）
        now = datetime.utcnow()
        task_result = await db.execute(
            select(Task).where(
                Task.user_id == current_user.id,
                Task.task_type == TaskType.CREATE_PROBLEM,
                Task.status == TaskStatus.IN_PROGRESS
            ).order_by(Task.claimed_at.asc())
        )
        task = task_result.scalar_one_or_none()
        
        if task and task.completed_count > 0:
            task.completed_count = task.completed_count - 1
        
        # 更新用户的出题数统计（用于仪表盘显示）
        if current_user.problems_created_count > 0:
            current_user.problems_created_count = current_user.problems_created_count - 1
        
        await db.commit()
        
        return {
            "success": True,
            "message": "题目已删除",
            "task_progress": {
                "completed": task.completed_count if task else 0,
                "total": task.total_count if task else 0,
                "remaining": (task.total_count - task.completed_count) if task else 0
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"删除题目失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除题目失败: {str(e)}"
        )


@router.delete("/clear-export-list", summary="清空导出列表")
async def clear_export_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    清空当前用户的待导出列表
    
    清空后，任务的completed_count会重置为0
    """
    try:
        result = await db.execute(
            select(ValidatedProblemExport).where(
                ValidatedProblemExport.user_id == current_user.id,
                ValidatedProblemExport.is_exported == False
            )
        )
        problems = result.scalars().all()
        
        deleted_count = len(problems)
        
        # 删除所有题目
        for p in problems:
            await db.delete(p)
        
        # 更新任务进度（重置为0）
        now = datetime.utcnow()
        task_result = await db.execute(
            select(Task).where(
                Task.user_id == current_user.id,
                Task.task_type == TaskType.CREATE_PROBLEM,
                Task.status == TaskStatus.IN_PROGRESS
            ).order_by(Task.claimed_at.asc())
        )
        task = task_result.scalar_one_or_none()
        
        if task:
            task.completed_count = 0
        
        # 更新用户的出题数统计（用于仪表盘显示）
        # 注意：这里只减少待导出列表中的题目数，不影响已导出的题目
        # 如果用户之前已经导出过题目，那些题目的统计不会减少
        # 这里只减少当前待导出列表中的题目数
        if current_user.problems_created_count >= deleted_count:
            current_user.problems_created_count = current_user.problems_created_count - deleted_count
        else:
            # 如果统计数小于删除数，说明可能有些题目已经导出过了，只减少到0
            current_user.problems_created_count = 0
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"已清空 {deleted_count} 道题目"
        }
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"清空列表失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清空列表失败: {str(e)}"
        )


@router.get("/export-list", summary="查看待导出列表")
async def get_export_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查看当前用户的待导出题目列表
    """
    try:
        result = await db.execute(
            select(ValidatedProblemExport).where(
                ValidatedProblemExport.user_id == current_user.id,
                ValidatedProblemExport.is_exported == False
            ).order_by(ValidatedProblemExport.created_at.desc())
        )
        problems = result.scalars().all()
        
        # 统计通过情况
        passed_count = 0
        for p in problems:
            originality_passed = _safe_bool(p.originality_check.get("is_original", False)) if p.originality_check else False
            rigor_passed = _safe_bool(p.rigor_check.get("is_rigorous", False)) if p.rigor_check else False
            if originality_passed and rigor_passed:
                passed_count += 1
        
        # 构建返回数据，添加更安全的错误处理
        problems_list = []
        for p in problems:
            try:
                # 安全地提取难度检测结果
                difficulty_passed = None
                if p.difficulty_validation and isinstance(p.difficulty_validation, dict):
                    difficulty_passed = _safe_bool(p.difficulty_validation.get("is_passed", None)) if p.difficulty_validation.get("is_passed") is not None else None
                
                # 安全地提取原创性检测结果
                originality_passed = False
                if p.originality_check and isinstance(p.originality_check, dict):
                    originality_passed = _safe_bool(p.originality_check.get("is_original", False))
                
                # 安全地提取严谨性检测结果
                rigor_passed = False
                if p.rigor_check and isinstance(p.rigor_check, dict):
                    rigor_passed = _safe_bool(p.rigor_check.get("is_rigorous", False))
                
                # 安全地处理时间
                created_at_str = None
                if p.created_at:
                    try:
                        created_at_str = p.created_at.isoformat()
                    except:
                        created_at_str = str(p.created_at)
                
                problems_list.append({
                    "id": p.id,
                    "difficulty_passed": difficulty_passed,
                    "originality_passed": originality_passed,
                    "rigor_passed": rigor_passed,
                    "created_at": created_at_str
                })
            except Exception as e:
                # 如果单条记录有问题，记录错误但继续处理其他记录
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"处理题目记录失败 {p.id}: {str(e)}")
                continue
        
        return {
            "total": len(problems_list),
            "passed": passed_count,
            "failed": len(problems_list) - passed_count,
            "problems": problems_list
        }
    
    except Exception as e:
        # 捕获所有异常（包括表不存在、数据库连接失败等）
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"加载导出列表失败: {str(e)}")
        
        # 返回空数据而不是抛出异常
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "problems": []
        }


# ==================== 动态路由（必须放在最后）====================

@router.get("/{problem_id}", response_model=ProblemResponse, summary="获取题目详情")
async def get_problem(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定题目的详细信息（从PostgreSQL和MongoDB合并）"""
    # 先检查权限
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    problem_meta = result.scalar_one_or_none()
    
    if not problem_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    # 只有创建者或管理员可以查看题目详情
    if problem_meta.creator_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看该题目"
        )
    
    # 使用ProblemStorageService获取完整数据
    try:
        storage_service = get_problem_storage_service()
        full_problem = await storage_service.get_problem(db, problem_id)
        return full_problem
    except RuntimeError:
        # MongoDB未配置，返回PostgreSQL数据（兼容模式）
        return problem_meta

