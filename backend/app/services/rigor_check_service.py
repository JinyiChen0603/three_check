"""
严谨性检测服务模块
使用 GPT-5.2 Responses API + web_search 联网搜索判断数学严谨性
"""

from typing import Dict, Any, Optional, List

from app.services.llm import gpt52_research, ResponsesAPIClient


class RigorCheckService:
    """
    数学严谨性检测服务 - 使用 GPT-5.2 Responses API + web_search
    
    通过联网搜索数学定理、公式等，判断题目的数学严谨性：
    - 题目表述是否清晰、无歧义
    - 数学符号使用是否规范
    - 题目条件是否充分
    - 答案是否唯一且正确
    """
    
    def __init__(self, client: ResponsesAPIClient = None):
        """
        初始化严谨性检测服务
        
        Args:
            client: ResponsesAPIClient 实例，默认使用 gpt52_research
        """
        self.client = client or gpt52_research
        self.model_name = "gpt-5.2-research"
    
    async def check_rigor(
        self,
        problem: str,
        answer: str,
        explanation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        检查数学严谨性（使用 GPT-5.2 Responses API + web_search 联网搜索）
        
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
                "citations": List[Dict],  # 引用来源
                "error": str  # 错误信息（如果失败）
            }
        """
        try:
            prompt = f"""请从数学专业的角度，判断以下题目在数学语境下是否严格、严谨。

请联网搜索相关的数学定理、公式、定义等，验证题目的数学正确性。

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
3. 题目条件是否充分（是否有遗漏或多余条件）
4. 答案是否唯一且正确（如有多解，是否都列出）
5. 解析（如有）是否逻辑严密
6. 涉及的数学定理或公式是否正确应用

请按照以下格式回答：
【判断结果】（严谨/不严谨）
【数学依据】（引用相关的数学定理或公式）
【问题说明】（如果不严谨，说明具体问题）
【建议】（如果有问题，给出修改建议）"""
            
            # 使用 Responses API + web_search 进行联网搜索
            response = await self.client.web_search(
                query=prompt,
                reasoning_effort="medium"
            )
            
            # 提取输出文本
            content = ResponsesAPIClient.extract_output_text(response)
            
            # 提取引用来源
            citations = ResponsesAPIClient.extract_citations(response)
            
            if not content:
                return {
                    "success": False,
                    "error": "AI 返回内容为空"
                }
            
            # 解析判断结果
            is_rigorous = self._parse_rigor_result(content)
            
            return {
                "success": True,
                "is_rigorous": is_rigorous,
                "details": content,
                "verdict": "数学严谨性合格" if is_rigorous else "存在严谨性问题",
                "ai_model": self.model_name,
                "citations": citations
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"严谨性检测失败: {str(e)}"
            }
    
    def _parse_rigor_result(self, content: str) -> bool:
        """
        解析严谨性判断结果
        
        Args:
            content: AI 返回的内容
            
        Returns:
            bool: 是否严谨
        """
        # 检查判断结果部分
        if "【判断结果】" in content:
            start = content.find("【判断结果】")
            end = content.find("【", start + 1) if "【" in content[start + 1:] else len(content)
            result_section = content[start:end]
            
            if "不严谨" in result_section:
                return False
            if "严谨" in result_section:
                return True
        
        # 回退：简单判断
        if "不严谨" in content:
            return False
        if "严谨" in content and "不严谨" not in content:
            return True
        
        # 默认认为严谨（保守策略）
        return True


# 全局服务实例
rigor_check_service = RigorCheckService()

