"""
严谨性检测服务模块
使用 GPT-4o 判断数学严谨性
"""

from typing import Dict, Any, Optional
import httpx

from app.config import settings


class RigorCheckService:
    """数学严谨性检测服务 - 使用 GPT-4o"""
    
    def __init__(self):
        # 使用 OpenRouter API Key
        self.openai_api_key = settings.OPENROUTER_API_KEY
        self.gpt4_model = settings.OPENAI_GPT_rigorous_MODEL  # OpenRouter 格式
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    async def check_rigor(
        self,
        problem: str,
        answer: str,
        explanation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        检查数学严谨性（使用GPT-4o）
        
        Args:
            problem: 题目内容
            answer: 标准答案
            explanation: 解析
            
        Returns:
            Dict: {
                "success": bool,
                "is_rigorous": bool,
                "details": str,
                "verdict": str,
                "ai_model": str,
                "error": str  # 错误信息（如果失败）
            }
        """
    #     # 🔴 临时：跳过严谨性检测，直接返回通过
    #     return {
    #     "success": True,
    #     "is_rigorous": True,
    #     "details": "【临时模式】已跳过严谨性检测",
    #     "verdict": "数学严谨性合格（跳过检测）",
    #     "ai_model": "skipped"
    # }
        try:
            prompt = f"""请从数学专业的角度，判断以下题目在数学语境下是否严格、严谨。

题目：
{problem}

答案：
{answer}"""
            
            if explanation:
                prompt += f"\n\n解析：\n{explanation}"
            
            prompt += """

请检查：
1. 题目表述是否清晰、无歧义
2. 数学符号使用是否规范
3. 题目条件是否充分
4. 答案是否唯一且正确
5. 解析（如有）是否逻辑严密

请按照以下格式回答：
【判断结果】（严谨/不严谨）
【问题说明】（如果不严谨，说明具体问题）
【建议】（如果有问题，给出修改建议）"""
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.gpt4_model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.2,
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                content = result["choices"][0]["message"]["content"]
                
                # 简单解析判断结果
                is_rigorous = "严谨" in content and "不严谨" not in content
                
                return {
                    "success": True,
                    "is_rigorous": is_rigorous,
                    "details": content,
                    "verdict": "数学严谨性合格" if is_rigorous else "存在严谨性问题",
                    "ai_model": self.gpt4_model
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"严谨性检测失败: {str(e)}"
            }


# 全局服务实例
rigor_check_service = RigorCheckService()

