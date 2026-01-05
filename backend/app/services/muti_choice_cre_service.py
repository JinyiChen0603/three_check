"""
AI 服务模块
集成 GPT-4o 用于生成相似答案（评分流程4选1）
"""

from typing import Dict, Any, List

from app.services.llm import gpt4o_mini, LLMClient


class GPTService:
    """
    GPT-4o 服务（用于生成相似答案）
    
    用于评分流程的4选1功能：生成看起来合理但实际错误的答案
    """
    
    def __init__(self, client: LLMClient = None):
        """
        初始化 GPT 服务
        
        Args:
            client: LLMClient 实例，默认使用 gpt4o_mini
        """
        self.client = client or gpt4o_mini
        self.model_name = "gpt-4o-mini"
    
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
                    "content": f"""给定答案：{correct_answer}

请生成{count}个与此答案相似但错误的答案。

要求：
1. 只输出答案数字或表达式，不要加任何说明文字
2. 不要加"正确答案是"、"答案："、"Answer:"等前缀
3. 每行一个答案
4. 保持与原答案相同的格式

示例：
- 如果原答案是 "42"，只输出 "41"、"43"、"44" 这样的纯数字
- 如果原答案是 "$$x=2$$"，只输出 "$$x=3$$"、"$$x=1$$" 这样的纯表达式"""
                }
            ]
            
            response = await self.client.chat(
                messages=messages,
                max_tokens=150,  # 降低token数
                temperature=0.3  # 降低温度提速
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

            # 去除"正确答案是："、"答案："等前缀
            processed_answers = []
            for answer in similar_answers:
                answer = answer.strip()
                # 定义需要移除的前缀列表
                prefixes_to_remove = [
                    "正确答案是：", "正确答案是:", "正确答案：", "正确答案:",
                    "答案是：", "答案是:", "答案：", "答案:",
                    "Answer:", "Answer is:", "answer:", "answer is:"
                ]
                # 尝试移除前缀
                for prefix in prefixes_to_remove:
                    if answer.startswith(prefix):
                        answer = answer[len(prefix):].strip()
                        break
                # 只添加非空答案
                if answer:
                    processed_answers.append(answer)
            
            return {
                "success": True,
                "similar_answers": processed_answers[:count],
                "ai_model": self.model_name
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"生成相似答案失败: {str(e)}"
            }


# 全局服务实例
gpt_service = GPTService()
