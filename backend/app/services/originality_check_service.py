"""
原创性检测服务模块
使用 GPT-5.2 Responses API + web_search 联网搜索判断题目原创性
"""

from typing import Dict, Any, List

from app.services.llm import gpt52_research, ResponsesAPIClient


class OriginalityCheckService:
    """
    原创性检测服务 - 使用 GPT-5.2 Responses API + web_search
    
    通过联网搜索判断题目是否在网络上已存在相同或高度相似的题目。
    """
    
    def __init__(self, client: ResponsesAPIClient = None):
        """
        初始化原创性检测服务
        
        Args:
            client: ResponsesAPIClient 实例，默认使用 gpt52_research
        """
        self.client = client or gpt52_research
        self.model_name = "gpt-5.2-research"
    
    async def check_originality(self, problem: str) -> Dict[str, Any]:
        """
        检查原创性（使用 GPT-5.2 Responses API + web_search 联网搜索）
        
        Args:
            problem: 题目内容
            
        Returns:
            Dict: {
                "success": bool,
                "is_original": bool,
                "details": str,
                "verdict": str,
                "ai_model": str,
                "citations": List[Dict],  # 引用来源
                "error": str  # 错误信息（如果失败）
            }
        """
        try:
            prompt = f"""请判断以下数学题目是否为原创题目。

请联网搜索，判断这道题目（不考虑具体的数字和语义环境）是否在网络上已经存在相同或高度相似的题目。

搜索时请注意：
1. 搜索题目的核心结构和解题思路
2. 忽略具体数字的差异
3. 关注题目类型和考查点是否相似

题目：
{problem}

请按照以下格式回答：
【判断结果】（原创/非原创）
【相似度】（如果找到相似题目，说明相似程度：高度相似/部分相似/无相似）
【搜索发现】（列出搜索到的相关题目或来源）
【依据】（说明判断依据）"""
            
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
            is_original = self._parse_originality_result(content)
            
            return {
                "success": True,
                "is_original": is_original,
                "details": content,
                "verdict": "原创性合格" if is_original else "可能存在相似题目",
                "ai_model": self.model_name,
                "citations": citations
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"原创性检测失败: {str(e)}"
            }
    
    def _parse_originality_result(self, content: str) -> bool:
        """
        解析原创性判断结果
        
        Args:
            content: AI 返回的内容
            
        Returns:
            bool: 是否原创
        """
        content_lower = content.lower()
        
        # 检查判断结果部分
        if "【判断结果】" in content:
            # 提取判断结果部分
            start = content.find("【判断结果】")
            end = content.find("【", start + 1) if "【" in content[start + 1:] else len(content)
            result_section = content[start:end]
            
            # 判断是否为原创
            if "非原创" in result_section or "不原创" in result_section:
                return False
            if "原创" in result_section:
                return True
        
        # 回退：检查相似度部分
        if "高度相似" in content:
            return False
        
        # 回退：简单判断
        if "非原创" in content or "不原创" in content:
            return False
        if "原创" in content:
            return True
        
        # 默认认为原创（保守策略）
        return True


# 全局服务实例
originality_check_service = OriginalityCheckService()

