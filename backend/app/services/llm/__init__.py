"""LLM大模型API统一调用管理"""

from .clients import (
    # 基类
    LLMClient,
    ResponsesAPIClient,
    # 标准模型实例
    deepseek_math,
    gpt4o,
    doubao,
    # 带默认参数的模型实例
    glm46_thinking,
    glm47_thinking,
    gpt52_with_reasoning,
    # Responses API 模型实例（支持 web_search）
    gpt52_research,
    # 直接访问的模型
    gpt4o_vision,
    gemini3_pro,
)

__all__ = [
    # 基类
    "LLMClient",
    "ResponsesAPIClient",
    # 标准模型实例
    "deepseek_math",
    "gpt4o",
    "doubao",
    # 带默认参数的模型实例
    "glm46_thinking",
    "glm47_thinking",
    "gpt52_with_reasoning",
    # Responses API 模型实例（支持 web_search）
    "gpt52_research",
    # 直接访问的模型
    "gpt4o_vision",
    "gemini3_pro",
]
