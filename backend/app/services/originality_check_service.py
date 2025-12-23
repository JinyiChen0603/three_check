"""
原创性检测服务模块
使用 GPT-4o Research 联网搜索判断题目原创性
"""

from typing import Dict, Any
import httpx

from app.config import settings


class OriginalityCheckService:
    """原创性检测服务 - 使用 GPT-4o Research 联网搜索"""#现改用
    
    def __init__(self):
        # 使用 OpenRouter API Key
        self.openai_api_key = settings.OPENROUTER_API_KEY
        self.ORIGINALITY_MODEL = settings.OPENAI_GPT_ORIGINALITY_MODEL  # OpenRouter 格式
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    async def check_originality(self, problem: str) -> Dict[str, Any]:
        
        # #临时测试：直接返回通过
        # return {
        #     "success": True,
        #     "is_original": True,
        #     "details": "【测试模式】自动通过",
        #     "verdict": "原创性合格（测试模式）",
        #     "ai_model": "test_mode"
        # }
        """
        检查原创性（使用GPT-4o Research联网搜索）
        
        Args:
            problem: 题目内容
            
        Returns:
            Dict: {
                "success": bool,
                "is_original": bool,
                "details": str,
                "verdict": str,
                "ai_model": str,
                "error": str  # 错误信息（如果失败）
            }
        """
        try:
            prompt = f"""请判断以下数学题目是否为原创题目。

请联网搜索，判断这道题目（不考虑具体的数字和语义环境）是否在网络上已经存在相同或高度相似的题目。

题目：
{problem}

请按照以下格式回答：
【判断结果】（原创/非原创）
【相似度】（如果找到相似题目，说明相似度）
【依据】（说明判断依据）"""
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.ORIGINALITY_MODEL,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1000,
                        "temperature": 0.3,
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                content = result["choices"][0]["message"]["content"]
                
                # 简单解析判断结果
                is_original = "原创" in content and "非原创" not in content
                
                return {
                    "success": True,
                    "is_original": is_original,
                    "details": content,
                    "verdict": "原创性合格" if is_original else "可能存在相似题目",
                    "ai_model": self.ORIGINALITY_MODEL
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"原创性检测失败: {str(e)}"
            }


# 全局服务实例
originality_check_service = OriginalityCheckService()

