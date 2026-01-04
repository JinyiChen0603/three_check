"""
题目验证和导出API
包含题目验证、质检和导出相关功能
"""

from typing import Optional
from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Form, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
import asyncio
import json
from urllib.parse import quote

from app.database import get_db
from app.models import (
    User,
    ValidationRecord, Transaction, TransactionType, TransactionStatus,
    Task, TaskType, TaskStatus, ValidatedProblemExport
)
from app.api.deps import get_current_user
from app.services.ocr_service import ocr_service
from app.services.validation_service import validation_service, quality_check_service
from app.services.difficulty_check_service import difficulty_check_service
from app.services.originality_check_service import originality_check_service
from app.services.rigor_check_service import rigor_check_service
from app.services.export_service import export_service
from app.services.progress_service import progress_service
from app.config import settings


router = APIRouter()


# ==================== Pydantic 模型 ====================

class OCRRequest(BaseModel):
    """OCR识别请求"""
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    extract_answer: bool = True


class QualityCheckContentRequest(BaseModel):
    """内容质检请求（无需题目ID）"""
    content: str = Field(..., description="题目内容")
    answer: str = Field(..., description="标准答案")
    explanation: Optional[str] = Field(None, description="解析")


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


# ====================== 独立质检 API ======================

@router.post("/check-difficulty-start", summary="启动难度检测（异步）")
async def start_difficulty_check(
    request: QualityCheckContentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    启动异步难度检测，返回 task_id
    
    前端通过 task_id 连接 SSE 端点获取实时进度
    
    Returns:
        {"task_id": "uuid-xxx"}
    """
    task_id = str(uuid.uuid4())
    
    problem_content = request.content
    if isinstance(problem_content, dict):
        problem_content = json.dumps(problem_content, ensure_ascii=False)
    
    async def run_check():
        """后台执行难度检测"""
        # 定义回调：更新 Redis 进度
        async def on_progress(p: dict):
            await progress_service.update_progress(task_id, p["progress"])
        
        # 执行检测，使用 lambda 包装异步回调
        result = await difficulty_check_service.validate_difficulty(
            problem=problem_content,
            answer=request.answer,
            explanation=request.explanation or "",
            progress_callback=lambda p: asyncio.create_task(on_progress(p))
        )
        
        # 存储最终结果（100% 进度 + 结果）
        await progress_service.update_progress(task_id, 100, result)
        
        # 保存完整的8次检测结果到数据库
        if result.get("success", False):
            try:
                async for db in get_db():
                    validation_record = ValidationRecord(
                        validated_problem_id=None,  # 内容质检暂不关联题目，导出后再关联
                        validation_type="difficulty",
                        ai_model=result.get("ai_model", "豆包"),
                        attempts=result.get("attempts", 16),
                        correct_count=result.get("correct_count", 0),
                        is_passed=result.get("is_passed", False),
                        result_data=result  # 存储完整结果，包含8次详细输出
                    )
                    db.add(validation_record)
                    await db.commit()
                    print(f"✅ 难度检测结果已保存到数据库，task_id={task_id}")
                    break
            except Exception as e:
                print(f"⚠️ 保存验证记录到数据库失败: {str(e)}")
    
    background_tasks.add_task(run_check)
    
    return {"task_id": task_id}


@router.get("/check-difficulty-stream/{task_id}", summary="SSE进度流")
async def stream_difficulty_progress(task_id: str):
    """
    SSE 实时推送难度检测进度
    
    - 连接时先发送当前进度（支持刷新恢复）
    - 然后持续推送进度更新
    - 收到 progress=100 且包含 result 时表示完成
    
    SSE 数据格式：
        data: {"progress": 6}
        data: {"progress": 12}
        ...
        data: {"progress": 100, "result": {...}}
    """
    async def event_generator():
        # 超时时间从默认 600 秒改为 3600 秒（1 小时）
        async for data in progress_service.subscribe_progress(
            task_id,
            timeout=3600.0  # 1 小时
        ):
            yield {"data": json.dumps(data, ensure_ascii=False)}
    
    return EventSourceResponse(event_generator())


@router.get("/check-difficulty-progress/{task_id}", summary="查询当前进度")
async def get_difficulty_progress(task_id: str):
    """
    查询难度检测的当前进度
    
    用于非 SSE 场景或手动查询
    
    Returns:
        {"progress": int, "result": dict|None}
        如果任务不存在返回 None
    """
    data = await progress_service.get_progress(task_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在或已过期"
        )
    return data


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
    difficulty_result_json: Optional[str] = Form(None),  # 前端已完成的难度检测结果（JSON字符串）
    originality_result_json: Optional[str] = Form(None),  # 前端已完成的原创性检测结果（JSON字符串）
    rigor_result_json: Optional[str] = Form(None),  # 前端已完成的严谨性检测结果（JSON字符串）
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
        
        # 2. 检查当前任务已保存的题目数量（只统计当前进行中任务的题目）
        saved_count_result = await db.execute(
            select(func.count(ValidatedProblemExport.id)).where(
                ValidatedProblemExport.task_id == task.id  # 只统计当前任务的题目
            )
        )
        saved_count = saved_count_result.scalar() or 0
        
        # 检查是否超过当前任务数量
        if saved_count >= task.total_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"当前任务已保存 {saved_count} 道题目，已达到任务上限 {task.total_count} 道。如需继续出题，请先删除已保存的题目或提交当前任务后领取新任务"
            )
        
        # 3. 验证难度（可选）
        difficulty_result = None
        # 优先使用前端传递的检测结果
        if difficulty_result_json:
            try:
                import json
                difficulty_result = json.loads(difficulty_result_json)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"解析前端传递的难度检测结果失败: {str(e)}")
                # 如果解析失败，继续执行后端检测
                difficulty_result = None
        
        # 如果前端没有传递结果，且需要检测，则执行后端检测
        if difficulty_result is None and include_difficulty:
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
        
        # 4. 二维质检（优先使用前端传递的结果）
        originality_check = None
        rigor_check = None
        
        # 优先使用前端传递的原创性检测结果
        if originality_result_json:
            try:
                originality_check = json.loads(originality_result_json)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"解析前端传递的原创性检测结果失败: {str(e)}")
                originality_check = None
        
        # 优先使用前端传递的严谨性检测结果
        if rigor_result_json:
            try:
                rigor_check = json.loads(rigor_result_json)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"解析前端传递的严谨性检测结果失败: {str(e)}")
                rigor_check = None
        
        # 如果前端没有传递结果，则调用后端检测
        if originality_check is None or rigor_check is None:
            try:
                check_result = await quality_check_service.two_dimension_check(
                    problem=problem,
                    answer=answer,
                    explanation=explanation
                )
                # 仅使用后端检测结果填充缺失的项
                if originality_check is None:
                    originality_check = check_result.get("originality", {"success": False, "error": "质检异常"})
                if rigor_check is None:
                    rigor_check = check_result.get("rigor", {"success": False, "error": "质检异常"})
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"质检失败: {str(e)}")
                if originality_check is None:
                    originality_check = {"success": False, "error": f"质检异常: {str(e)}"}
                if rigor_check is None:
                    rigor_check = {"success": False, "error": f"质检异常: {str(e)}"}
        
        # 5. 保存到导出列表
        validated_problem = ValidatedProblemExport(
            user_id=current_user.id,
            task_id=task.id,  # 关联任务ID
            content=problem,
            answer=answer,
            explanation=explanation,
            difficulty_validation=difficulty_result,
            originality_check=originality_check,
            rigor_check=rigor_check
        )
        
        db.add(validated_problem)
        await db.commit()
        await db.refresh(validated_problem)
        
        # 5.1 创建验证记录
        validation_checks = []
        if difficulty_result:
            validation_checks.append(("difficulty", difficulty_result))
        if originality_check:
            validation_checks.append(("originality", originality_check))
        if rigor_check:
            validation_checks.append(("rigor", rigor_check))
        
        for check_type, check_data in validation_checks:
            if check_data and check_data.get("success"):
                # 判断是否通过
                if check_type == "difficulty":
                    is_passed = check_data.get("is_passed", False)
                elif check_type == "originality":
                    is_passed = check_data.get("is_original", False)
                elif check_type == "rigor":
                    is_passed = check_data.get("is_rigorous", False)
                else:
                    is_passed = False
                
                validation_record = ValidationRecord(
                    validated_problem_id=validated_problem.id,
                    validation_type=check_type,
                    ai_model=check_data.get("ai_model", "unknown"),
                    attempts=check_data.get("attempts") if check_type == "difficulty" else None,
                    correct_count=check_data.get("correct_count") if check_type == "difficulty" else None,
                    is_passed=is_passed,
                    result_data=check_data
                )
                db.add(validation_record)
        
        await db.commit()
        
        # 6. 实时统计当前任务的题目数量，更新任务进度
        saved_count_result = await db.execute(
            select(func.count(ValidatedProblemExport.id)).where(
                ValidatedProblemExport.task_id == task.id
            )
        )
        current_saved_count = saved_count_result.scalar() or 0
        task.completed_count = current_saved_count
        
        await db.commit()
        
        # 基于原创性和严谨性检测结果计算 all_passed
        originality_passed = originality_check.get("is_original", False) if originality_check else False
        rigor_passed = rigor_check.get("is_rigorous", False) if rigor_check else False
        all_passed = originality_passed and rigor_passed
        
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
            "originality": originality_check,
            "rigor": rigor_check,
            "difficulty": difficulty_result
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
    only_passed: int = Query(1, ge=0, le=1, description="是否只导出通过的题目 (0=全部, 1=仅通过的)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    导出当前用户验证过的题目到Excel
    
    Args:
        only_passed: 是否只导出三个检测都通过的题目 (0=全部导出, 1=仅通过的)
    
    Returns:
        Excel文件下载
    """
    try:
        # 查询所有题目，并加载用户信息
        query = (
            select(ValidatedProblemExport)
            .options(selectinload(ValidatedProblemExport.user))
            .where(ValidatedProblemExport.user_id == current_user.id)
            .order_by(ValidatedProblemExport.created_at.asc())
        )
        
        result = await db.execute(query)
        validated_problems = result.scalars().all()
        
        if not validated_problems:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="没有可导出的题目"
            )
        
        # 转换为字典列表
        problems_data = []
        for p in validated_problems:
            try:
                if only_passed == 1:
                    # 判断三个检测是否都通过
                    # 难度检测
                    difficulty_passed = False
                    if p.difficulty_validation and isinstance(p.difficulty_validation, dict):
                        difficulty_passed = _safe_bool(p.difficulty_validation.get("is_passed", False))
                    
                    # 原创性检测
                    originality_passed = False
                    if p.originality_check and isinstance(p.originality_check, dict):
                        # 检查是否有 is_original 字段
                        if "is_original" in p.originality_check:
                            originality_passed = _safe_bool(p.originality_check.get("is_original", False))
                    
                    # 严谨性检测
                    rigor_passed = False
                    if p.rigor_check and isinstance(p.rigor_check, dict):
                        # 检查是否有 is_rigorous 字段
                        if "is_rigorous" in p.rigor_check:
                            rigor_passed = _safe_bool(p.rigor_check.get("is_rigorous", False))
                    
                    # 三个检测都必须通过
                    all_passed = difficulty_passed and originality_passed and rigor_passed
                    
                    # 如果只导出通过的题目，跳过未通过的
                    if not all_passed:
                        continue
                
                # 导出所有列的所有内容（JSON全部导出）
                problems_data.append({
                    "id": p.id,
                    "user_id": p.user_id,
                    "username": p.user.username if p.user else "",  # 添加用户名
                    "content": p.content,
                    "answer": p.answer,
                    "explanation": p.explanation,
                    "difficulty_validation": p.difficulty_validation,  # JSON完整内容
                    "originality_check": p.originality_check,  # JSON完整内容
                    "rigor_check": p.rigor_check,  # JSON完整内容
                    "created_at": p.created_at.isoformat() if p.created_at else None
                })
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"处理导出题目失败 {p.id}: {str(e)}")
                continue
        
        if not problems_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="没有通过质检的题目可导出" if only_passed == 1 else "没有可导出的题目"
            )
        
        # 生成Excel
        excel_file = export_service.export_to_excel(problems_data)
        
        # 返回文件下载
        filename = f"验证题目_{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
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
                ValidatedProblemExport.user_id == current_user.id
            )
        )
        problem = result.scalar_one_or_none()
        
        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在"
            )
        
        # 获取题目关联的任务
        task = None
        if problem.task_id:
            task_result = await db.execute(
                select(Task).where(Task.id == problem.task_id)
            )
            task = task_result.scalar_one_or_none()
            
            # ⭐ 检查任务状态：已提交的任务不能删除题目
            if task and task.status == TaskStatus.SUBMITTED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="任务已提交，题目无法删除。已提交的题目不能删除或放弃"
                )
        
        # 删除题目
        await db.delete(problem)
        await db.commit()
        
        # 更新任务进度：实时统计该任务的题目数量
        if task:
            saved_count_result = await db.execute(
                select(func.count(ValidatedProblemExport.id)).where(
                    ValidatedProblemExport.task_id == task.id
                )
            )
            current_saved_count = saved_count_result.scalar() or 0
            task.completed_count = current_saved_count
            
            # 如果任务是SUBMITTED状态且题目数量小于总数，改回IN_PROGRESS
            if task.status == TaskStatus.SUBMITTED and task.completed_count < task.total_count:
                task.status = TaskStatus.IN_PROGRESS
                task.submitted_at = None
            
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
                ValidatedProblemExport.user_id == current_user.id
            )
        )
        problems = result.scalars().all()
        
        deleted_count = len(problems)
        
        # 收集所有受影响的任务ID
        affected_task_ids = set()
        for p in problems:
            if p.task_id:
                affected_task_ids.add(p.task_id)
        
        # ⭐ 检查是否有已提交的任务
        if affected_task_ids:
            submitted_tasks_result = await db.execute(
                select(Task).where(
                    and_(
                        Task.id.in_(affected_task_ids),
                        Task.status == TaskStatus.SUBMITTED
                    )
                )
            )
            submitted_tasks = submitted_tasks_result.scalars().all()
            
            if submitted_tasks:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"有 {len(submitted_tasks)} 个任务已提交，无法清空列表。已提交的题目不能删除或放弃"
                )
        
        # 删除所有题目
        for p in problems:
            await db.delete(p)
        
        await db.commit()
        
        # 更新所有受影响任务的进度：实时统计每个任务的题目数量
        for task_id in affected_task_ids:
            task_result = await db.execute(
                select(Task).where(Task.id == task_id)
            )
            task = task_result.scalar_one_or_none()
            
            if task:
                # 统计该任务的题目数量
                saved_count_result = await db.execute(
                    select(func.count(ValidatedProblemExport.id)).where(
                        ValidatedProblemExport.task_id == task_id
                    )
                )
                current_saved_count = saved_count_result.scalar() or 0
                task.completed_count = current_saved_count
                
                # 如果任务是SUBMITTED状态且题目数量小于总数，改回IN_PROGRESS
                if task.status == TaskStatus.SUBMITTED and task.completed_count < task.total_count:
                    task.status = TaskStatus.IN_PROGRESS
                    task.submitted_at = None
        
        await db.commit()
        
        # 获取最近的任务信息用于返回
        task_result = await db.execute(
            select(Task).where(
                Task.user_id == current_user.id,
                Task.task_type == TaskType.CREATE_PROBLEM,
                Task.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.SUBMITTED])
            ).order_by(Task.claimed_at.desc())
        )
        task = task_result.scalar_one_or_none()
        
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
                ValidatedProblemExport.user_id == current_user.id
            ).order_by(ValidatedProblemExport.created_at.desc())
        )
        problems = result.scalars().all()
        
        # 统计通过情况（三个检测都通过才算通过）
        passed_count = 0
        for p in problems:
            # 难度检测
            difficulty_passed = False
            if p.difficulty_validation and isinstance(p.difficulty_validation, dict):
                difficulty_passed = _safe_bool(p.difficulty_validation.get("is_passed", False))
            
            # 原创性检测
            originality_passed = False
            if p.originality_check and isinstance(p.originality_check, dict):
                # 检查是否有 is_original 字段
                if "is_original" in p.originality_check:
                    originality_passed = _safe_bool(p.originality_check.get("is_original", False))
            
            # 严谨性检测
            rigor_passed = False
            if p.rigor_check and isinstance(p.rigor_check, dict):
                # 检查是否有 is_rigorous 字段
                if "is_rigorous" in p.rigor_check:
                    rigor_passed = _safe_bool(p.rigor_check.get("is_rigorous", False))
            
            # 三个检测都通过才算通过
            if difficulty_passed and originality_passed and rigor_passed:
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
                originality_passed = None
                if p.originality_check and isinstance(p.originality_check, dict):
                    # 检查是否有 is_original 字段
                    if "is_original" in p.originality_check:
                        originality_passed = _safe_bool(p.originality_check.get("is_original"))
                    # 如果检测成功但没有 is_original 字段，可能是数据格式问题
                    elif p.originality_check.get("success") is True:
                        # 检测成功但缺少字段，记录警告
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"题目 {p.id} 原创性检测成功但缺少 is_original 字段，可用字段: {list(p.originality_check.keys())}")
                        # 默认为未通过（因为无法确定）
                        originality_passed = False
                
                # 安全地提取严谨性检测结果
                rigor_passed = None
                if p.rigor_check and isinstance(p.rigor_check, dict):
                    # 检查是否有 is_rigorous 字段
                    if "is_rigorous" in p.rigor_check:
                        rigor_passed = _safe_bool(p.rigor_check.get("is_rigorous"))
                    # 如果检测成功但没有 is_rigorous 字段，可能是数据格式问题
                    elif p.rigor_check.get("success") is True:
                        # 检测成功但缺少字段，记录警告
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"题目 {p.id} 严谨性检测成功但缺少 is_rigorous 字段，可用字段: {list(p.rigor_check.keys())}")
                        # 默认为未通过（因为无法确定）
                        rigor_passed = False
                
                # 安全地处理时间
                created_at_str = None
                if p.created_at:
                    try:
                        created_at_str = p.created_at.isoformat()
                    except:
                        created_at_str = str(p.created_at)
                
                problems_list.append({
                    "id": p.id,
                    "content": p.content,  # 添加题目内容
                    "answer": p.answer,  # 添加答案
                    "explanation": p.explanation,  # 添加解析
                    "difficulty_passed": difficulty_passed,
                    "originality_passed": originality_passed,
                    "rigor_passed": rigor_passed,
                    "difficulty_validation": p.difficulty_validation,  # 完整的难度检测结果
                    "originality_check": p.originality_check,  # 完整的原创性检测结果
                    "rigor_check": p.rigor_check,  # 完整的严谨性检测结果
                    "admin_review_status": p.admin_review_status if p.admin_review_status else "pending",  # 管理员审核状态
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
