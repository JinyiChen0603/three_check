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
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
import asyncio
import json

from app.database import get_db
from app.models import (
    User, Problem, ProblemStatus, ProblemSourceType,
    ProblemValidationStatus, HumanReviewStatus, MaterialCategory,
    ValidationRecord, Transaction, TransactionType, TransactionStatus
)
from app.api.deps import get_current_user
from app.services.ocr_service import ocr_service
from app.services.validation_service import validation_service, quality_check_service
from app.services.ai_service import deepseek_service
from app.config import settings


router = APIRouter()


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
    
    # 创建题目
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
        status=ProblemStatus.DRAFT,
        validation_status=ProblemValidationStatus.NOT_VALIDATED,
        human_review_status=HumanReviewStatus.PENDING,
        variant_count=0
    )
    
    db.add(new_problem)
    
    # 如果是变体，更新母题的变形次数
    if parent_problem:
        parent_problem.variant_count += 1
    
    await db.commit()
    await db.refresh(new_problem)
    
    return new_problem


@router.post("/{problem_id}/generate-variant", summary="生成题目变体")
async def generate_variant(
    problem_id: int,
    request: GenerateVariantRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    基于母题生成变体（使用DeepSeek Math-V2）
    
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
    
    # 生成变体
    variant_result = await deepseek_service.generate_variant(
        original_problem=json.dumps(parent_problem.content) if isinstance(parent_problem.content, dict) else parent_problem.content,
        original_answer=parent_problem.answer,
        original_explanation=parent_problem.explanation,
        custom_prompt=request.custom_prompt
    )
    
    if not variant_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=variant_result.get("error", "生成变体失败")
        )
    
    return {
        "success": True,
        "parent_problem_id": problem_id,
        "variant_count": parent_problem.variant_count + 1,
        **variant_result,
        "note": "请检查生成的变体，确认无误后可以创建为新题目"
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
    
    # 执行质检
    problem.validation_status = ProblemValidationStatus.VALIDATING
    await db.commit()
    
    check_result = await quality_check_service.full_quality_check(
        problem=json.dumps(problem.content) if isinstance(problem.content, dict) else problem.content,
        answer=problem.answer,
        explanation=problem.explanation
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
    problem.quality_check_details = check_result
    problem.validation_status = (
        ProblemValidationStatus.PASSED
        if check_result["all_passed"]
        else ProblemValidationStatus.FAILED
    )
    problem.validation_completed_at = datetime.utcnow()
    
    # 如果质检通过，更新状态为待审核
    if check_result["all_passed"]:
        problem.status = ProblemStatus.PENDING_REVIEW
    
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
                "category": p.category.value,
                "status": p.status.value,
                "validation_status": p.validation_status.value,
                "human_review_status": p.human_review_status.value,
                "variant_count": p.variant_count,
                "created_at": p.created_at
            }
            for p in problems
        ]
    }


@router.get("/{problem_id}", response_model=ProblemResponse, summary="获取题目详情")
async def get_problem(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定题目的详细信息"""
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    problem = result.scalar_one_or_none()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    # 只有创建者或管理员可以查看题目详情
    if problem.creator_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看该题目"
        )
    
    return problem

