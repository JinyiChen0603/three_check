"""
题目三重质检API
提供难度、原创性、严谨性检测服务
"""

from typing import Optional
import uuid
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, Field
import asyncio
import json

from app.services.ocr_service import ocr_service
from app.services.difficulty_check_service import difficulty_check_service
from app.services.originality_check_service import originality_check_service
from app.services.rigor_check_service import rigor_check_service
from app.services.progress_service import progress_service


router = APIRouter()


# ==================== Pydantic 模型 ====================

class OCRRequest(BaseModel):
    """OCR识别请求"""
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    extract_answer: bool = True


class QualityCheckContentRequest(BaseModel):
    """内容质检请求"""
    content: str = Field(..., description="题目内容")
    answer: str = Field(..., description="标准答案")
    explanation: Optional[str] = Field(None, description="解析")


# ==================== API 路由 ====================

@router.post("/ocr", summary="OCR识别图片中的题目")
async def recognize_image(request: OCRRequest):
    """
    使用OCR识别图片中的数学题目
    
    支持：
    - image_url: 图片URL
    - image_base64: Base64编码的图片
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


# ====================== 三重质检 API ======================

@router.post("/check-difficulty-start", summary="启动难度检测（异步）")
async def start_difficulty_check(
    request: QualityCheckContentRequest,
    background_tasks: BackgroundTasks,
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
        
        # 执行检测
        result = await difficulty_check_service.validate_difficulty(
            problem=problem_content,
            answer=request.answer,
            explanation=request.explanation or "",
            progress_callback=lambda p: asyncio.create_task(on_progress(p))
        )
        
        # 存储最终结果（100% 进度 + 结果）
        await progress_service.update_progress(task_id, 100, result)
    
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
    
    Returns:
        {"progress": int, "result": dict|None}
    """
    data = await progress_service.get_progress(task_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在或已过期"
        )
    return data


@router.post("/check-originality", summary="检测原创性")
async def check_originality_only(
    request: QualityCheckContentRequest,
):
    """
    检测题目原创性（使用联网搜索）
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


@router.post("/check-rigor", summary="检测严谨性")
async def check_rigor_only(
    request: QualityCheckContentRequest,
):
    """
    检测数学严谨性
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
