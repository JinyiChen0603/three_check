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


# ==================== 翻译 API ====================

class TranslateRequest(BaseModel):
    """翻译请求"""
    text: str = Field(..., description="需要翻译的文本")
    target_lang: str = Field(default="zh", description="目标语言：zh=中文, en=英文")
    source_lang: str = Field(default="auto", description="源语言：auto=自动检测")


@router.post("/translate", summary="翻译文本（支持数学公式）")
async def translate_text(request: TranslateRequest):
    """
    使用 OpenAI GPT-4o-mini 翻译文本
    
    特点：
    - 保留 LaTeX 数学公式格式
    - 支持中英互译
    - 自动识别源语言
    """
    try:
        from app.services.llm.clients import gpt4o_mini
        
        # 构建翻译提示词
        lang_map = {
            "zh": "简体中文",
            "en": "English",
            "ja": "日本語",
            "ko": "한국어",
            "fr": "Français",
            "de": "Deutsch",
            "es": "Español",
        }
        
        target_language = lang_map.get(request.target_lang, "简体中文")
        
        # 自动检测源语言
        if request.source_lang == "auto":
            # 简单检测：如果包含中文字符，则为中文，否则默认英文
            import re
            has_chinese = bool(re.search(r'[\u4e00-\u9fff]', request.text))
            source_hint = "（检测到中文内容）" if has_chinese else "（检测到英文内容）"
        else:
            source_language = lang_map.get(request.source_lang, "自动检测")
            source_hint = f"（源语言：{source_language}）"
        
        prompt = f"""请将以下文本翻译成{target_language}。

重要要求：
1. 保持 LaTeX 数学公式不变（如 $x^2$、\\frac{{a}}{{b}} 等）
2. 保持数学符号和公式的准确性
3. 翻译要自然、流畅、符合目标语言习惯
4. 只返回翻译结果，不要添加任何解释或说明

原文{source_hint}：
{request.text}"""

        messages = [
            {
                "role": "system",
                "content": "你是一位专业的数学内容翻译专家，擅长翻译包含数学公式的文本，能够准确保留 LaTeX 格式。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # 调用 OpenAI API（使用 gpt-4o-mini 更快更便宜）
        response = await gpt4o_mini.chat(
            messages=messages,
            temperature=0.3,  # 较低温度确保翻译准确性
            max_tokens=2000
        )
        
        # 提取翻译结果
        translated_text = gpt4o_mini.extract_content(response)
        
        if not translated_text:
            raise Exception("翻译结果为空")
        
        return {
            "success": True,
            "original": request.text,
            "translated": translated_text.strip(),
            "source_lang": request.source_lang,
            "target_lang": request.target_lang
        }
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"翻译失败: {error_detail}")
        
        return {
            "success": False,
            "error": str(e),
            "original": request.text,
            "translated": None
        }
