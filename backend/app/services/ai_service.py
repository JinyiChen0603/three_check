"""
AI 服务模块
集成 GPT-4o 用于生成相似答案（评分流程4选1）
"""

from typing import Dict, Any, List

from app.services.llm import gpt4o, LLMClient


class GPTService:
    """
    GPT-4o 服务（用于生成相似答案）
    
    用于评分流程的4选1功能：生成看起来合理但实际错误的答案
    """
    
    def __init__(self, client: LLMClient = None):
        """
        初始化 GPT 服务
        
        Args:
            client: LLMClient 实例，默认使用 gpt4o
        """
        self.client = client or gpt4o
        self.model_name = "gpt-4o"
    
    async def generate_similar_answers(
        self,
        problem: str,
        correct_answer: str,
        count: int = 3
    ) -> Dict[str, Any]:
        """
        生成相似的错误答案（用于评分流程的4选1）
        
        Args:
            problem: 题目内容
            correct_answer: 正确答案
            count: 生成数量（默认3个）
            
        Returns:
            Dict: {
                "success": bool,
                "similar_answers": List[str],
                "error": str
            }
        """
        try:
            messages = [
                {
                    "role": "user",
                    "content": f"""请为以下数学题目生成{count}个相似但错误的答案。

题目：
{problem}

正确答案：
{correct_answer}

要求：
1. 生成的答案看起来合理，但实际是错误的
2. 错误答案要足够相似，能迷惑做题者
3. 每个答案单独一行

请直接列出{count}个答案，每行一个："""
                }
            ]
            
            response = await self.client.chat(
                messages=messages,
                max_tokens=500,
                temperature=0.9
            )
            
            content = LLMClient.extract_content(response)
            
            # 解析答案列表
            similar_answers = [
                line.strip()
                for line in content.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]
            
            # 去除编号
            similar_answers = [
                answer.split(".", 1)[-1].strip() if "." in answer else answer
                for answer in similar_answers
            ]
            
            return {
                "success": True,
                "similar_answers": similar_answers[:count],
                "ai_model": self.model_name
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"生成相似答案失败: {str(e)}"
            }


# 全局服务实例
gpt_service = GPTService()
