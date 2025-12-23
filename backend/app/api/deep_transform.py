"""
深度变形API
提供题目深度变形功能，无时间和token限制
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.api.deps import get_current_user
from app.services.deep_transformer_service import deep_transformer_service


router = APIRouter()


# ==================== Pydantic 模型 ====================

class GenerateModifiedProblemRequest(BaseModel):
    """生成修改后的题目请求"""
    original_problem: str = Field(..., description="原题目")
    original_answer: str = Field(..., description="原答案")
    modification_requirement: str = Field(..., description="修改要求")
    max_tokens: int = Field(8000, description="最大token数（会自动续写）")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    use_stream: bool = Field(True, description="是否使用流式传输")


class GenerateVariantRequest(BaseModel):
    """生成题目变体请求（完整版：题目+解析+答案）"""
    original_content: str = Field(..., description="原题目")
    original_explanation: str = Field(..., description="原解析")
    original_answer: str = Field(..., description="原答案")
    modification_requirement: str = Field("", description="修改要求（可为空）")
    max_tokens: int = Field(10000, description="最大token数（会自动续写）")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    use_stream: bool = Field(True, description="是否使用流式传输")


class GenerateMultipleVariantsRequest(BaseModel):
    """批量生成变体请求"""
    original_content: str = Field(..., description="原题目")
    original_explanation: str = Field(..., description="原解析")
    original_answer: str = Field(..., description="原答案")
    modification_requirement: str = Field("", description="修改要求（可为空）")
    count: int = Field(..., ge=1, le=50, description="生成数量（最多50个）")
    max_tokens: int = Field(10000, description="最大token数")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    use_stream: bool = Field(True, description="是否使用流式传输")


class ModifiedProblemResponse(BaseModel):
    """修改后的题目响应"""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None


class VariantResponse(BaseModel):
    """变体响应"""
    success: bool
    variant_content: Optional[str] = None
    variant_explanation: Optional[str] = None
    variant_answer: Optional[str] = None
    error: Optional[str] = None


class MultipleVariantsResponse(BaseModel):
    """批量变体响应"""
    success: bool
    count: Optional[int] = None
    total: Optional[int] = None
    variants: Optional[List[dict]] = None
    error: Optional[str] = None


# ==================== API 路由 ====================

@router.post("/generate-modified", 
             summary="根据修改要求生成新题目",
             response_model=ModifiedProblemResponse)
async def generate_modified_problem(
    request: GenerateModifiedProblemRequest,
    current_user: User = Depends(get_current_user)
):
    """
    根据原题目、原答案和修改要求，生成新的题目
    
    特点：
    - 无时间限制：允许AI长时间运行
    - 无token限制：自动续写，最多20轮
    - 支持流式/非流式传输
    
    返回JSON格式：
    ```json
    {
        "new_question": "优化后的题目",
        "new_answer": "完整解答，含步骤"
    }
    ```
    """
    try:
        result = await deep_transformer_service.generate_modified_problem(
            original_problem=request.original_problem,
            original_answer=request.original_answer,
            modification_requirement=request.modification_requirement,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            use_stream=request.use_stream
        )
        
        return ModifiedProblemResponse(
            success=True,
            result=result
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        return ModifiedProblemResponse(
            success=False,
            error=f"生成失败: {str(e)}"
        )


@router.post("/generate-variant",
             summary="生成完整的题目变体（题目+解析+答案）",
             response_model=VariantResponse)
async def generate_variant(
    request: GenerateVariantRequest,
    current_user: User = Depends(get_current_user)
):
    """
    生成题目变体（包含题目、解析、答案）
    
    这是深度变形的主要接口
    
    特点：
    - 无时间限制：允许AI长时间运行
    - 无token限制：自动续写，最多20轮
    - 支持流式/非流式传输
    - 可自定义修改要求或使用默认规则
    
    返回：
    ```json
    {
        "variant_content": "变体题目内容",
        "variant_explanation": "详细的解题步骤和分析",
        "variant_answer": "最终答案"
    }
    ```
    """
    try:
        result = await deep_transformer_service.generate_problem_variant_with_explanation(
            original_content=request.original_content,
            original_explanation=request.original_explanation,
            original_answer=request.original_answer,
            modification_requirement=request.modification_requirement,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            use_stream=request.use_stream
        )
        
        return VariantResponse(
            success=True,
            variant_content=result["variant_content"],
            variant_explanation=result["variant_explanation"],
            variant_answer=result["variant_answer"]
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        return VariantResponse(
            success=False,
            error=f"生成变体失败: {str(e)}"
        )


@router.post("/generate-multiple-variants",
             summary="批量生成多个变体题目",
             response_model=MultipleVariantsResponse)
async def generate_multiple_variants(
    request: GenerateMultipleVariantsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    批量生成多个变体题目（最多50个）
    
    特点：
    - 无时间限制：允许AI长时间运行
    - 无token限制：每个变体自动续写
    - 支持流式/非流式传输
    - 失败的变体会记录错误但不影响其他变体
    
    返回：
    ```json
    {
        "success": true,
        "count": 5,  // 成功生成的数量
        "total": 5,  // 请求的总数量
        "variants": [
            {
                "index": 1,
                "success": true,
                "variant_content": "...",
                "variant_explanation": "...",
                "variant_answer": "..."
            },
            ...
        ]
    }
    ```
    """
    try:
        result = await deep_transformer_service.generate_multiple_variants(
            original_content=request.original_content,
            original_explanation=request.original_explanation,
            original_answer=request.original_answer,
            modification_requirement=request.modification_requirement,
            count=request.count,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            use_stream=request.use_stream
        )
        
        return MultipleVariantsResponse(
            success=result["success"],
            count=result.get("count"),
            total=result.get("total"),
            variants=result.get("variants"),
            error=result.get("error")
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        return MultipleVariantsResponse(
            success=False,
            error=f"批量生成失败: {str(e)}"
        )


@router.get("/health",
            summary="深度变形服务健康检查")
async def health_check():
    """
    检查深度变形服务是否正常
    
    返回服务配置信息
    """
    return {
        "status": "healthy",
        "service": "深度变形服务",
        "model": deep_transformer_service.model,
        "api_url": deep_transformer_service.api_url,
        "features": {
            "no_timeout": True,
            "auto_continue": True,
            "max_rounds": 20,
            "max_batch_size": 50
        }
    }
