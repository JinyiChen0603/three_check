"""
深度变形服务模块
基于 Gemini 3 Pro 实现题目深度变形功能
支持自动续写和无限制运行
"""

import re
from typing import Dict, Any, Optional

from app.services.llm import gemini3_pro, LLMClient


class DeepTransformerService:
    """
    深度变形服务 - 无时间和token限制
    
    使用 Gemini 3 Pro（通过 OpenRouter）进行题目深度变形
    """
    
    def __init__(self, client: LLMClient = None):
        """
        初始化深度变形服务
        
        Args:
            client: LLMClient 实例，默认使用 gemini3_pro
        """
        self.client = client or gemini3_pro
        self.model_name = "gemini-3-pro"
    
    async def generate_modified_problem(
        self,
        original_problem: str,
        original_answer: str,
        modification_requirement: str,
        max_tokens: int = None,
        temperature: float = 0.7,
        max_rounds: int = 20
    ) -> str:
        """
        根据原题目、原答案和修改要求，生成新的题目或内容
        
        Args:
            original_problem: 原题目
            original_answer: 原答案
            modification_requirement: 修改要求
            max_tokens: 每轮最大token数（会自动续写）
            temperature: 温度参数
            max_rounds: 最大续写轮数
            
        Returns:
            str: JSON格式的结果字符串
        """
        # 参数校验
        if not original_problem.strip():
            raise ValueError("original_problem 不能为空")
        if not original_answer.strip():
            raise ValueError("original_answer 不能为空")
        if not modification_requirement.strip():
            raise ValueError("modification_requirement 不能为空")

        messages = [
            {
                "role": "system",
                "content": """你是数学出题专家。根据用户的修改要求生成一道新题目和答案。

必须按此格式返回（不要包含思考过程，不需要处理换行操作）：
{
    "new_question": "优化后的题目",
    "new_answer": "完整解答，含步骤"
}

文字描述用文本格式，数学公式满足：行内公式使用 $...$, 独立公式使用 $$...$$

禁止：不要在JSON中出现"Let's think"、"Actually"、"Wait"等思考词汇。直接输出结果。"""
            },
            {
                "role": "user",
                "content": f"""原题目：{original_problem}

原答案：{original_answer}

修改要求：{modification_requirement}

请直接返回JSON格式的新题目和新答案。"""
            }
        ]

        # 使用自动续写功能
        result_text = await self.client.chat_with_auto_continue(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            max_rounds=max_rounds
        )

        # 提取JSON块
        filtered_text = self._extract_last_brace_block(result_text)
        return filtered_text

    async def generate_problem_variant_with_explanation(
        self,
        original_content: str,
        original_explanation: str,
        original_answer: str,
        modification_requirement: str = "",
        max_tokens: int = None,
        temperature: float = 1.5,
        max_rounds: int = 20,
        use_stream: bool = True  # 接受但不使用（为了兼容API调用）
    ) -> Dict[str, Any]:
        """
        生成题目变体（包含题目、解析、答案）
        
        这是深度变形的主要接口 - 无时间和token限制版本
        
        Args:
            original_content: 原题目
            original_explanation: 原解析
            original_answer: 原答案
            modification_requirement: 修改要求（用户指定如何修改，可为空）
            max_tokens: 每轮最大 token 数（会自动续写）
            temperature: 温度参数
            max_rounds: 最大续写轮数
            
        Returns:
            dict: {
                "variant_content": "变体题目",
                "variant_explanation": "变体解析", 
                "variant_answer": "变体答案"
            }
        """
        # 参数校验
        if not original_content.strip():
            raise ValueError("original_content 不能为空")
        if not original_explanation.strip():
            raise ValueError("original_explanation 不能为空")
        if not original_answer.strip():
            raise ValueError("original_answer 不能为空")
        
        # 构造 prompt
        system_prompt = """你是数学出题专家。根据原题的题目、解析和答案以及修改要求，生成一道新的变体题目。

请严格按以下格式返回（使用分隔符区分各部分）：

【变体题目】
（在这里写变体题目的完整内容）

【变体解析】
（在这里写详细的解题步骤和分析）

【变体答案】
（在这里写最终答案）

注意事项：
1. 必须包含以上三个部分，每个部分用【】标记
2. 数学公式使用 LaTeX 格式：行内公式用 $...$，独立公式用 $$...$$
3. 直接输出结果，不要包含思考过程"""

        # 根据修改要求是否为空，构造不同的 user_message
        if modification_requirement and modification_requirement.strip():
            user_message = f"""原题目：{original_content}

原解析：{original_explanation}

原答案：{original_answer}

修改要求：{modification_requirement}

请根据修改要求生成一道变体题目，包含完整的题目、解析和答案。"""
        else:
            user_message = f"""原题目：{original_content}

原解析：{original_explanation}

原答案：{original_answer}

请生成一道变体题目，要求：
1. 保持题目类型和难度相近
2. 改变具体的数值、场景或条件
3. 确保新题目有明确的解答

请包含完整的题目、解析和答案。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # 使用自动续写功能
        result_text = await self.client.chat_with_auto_continue(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            max_rounds=max_rounds
        )
        
        # 解析文本格式的返回内容
        variant_content = self._extract_section(result_text, "变体题目")
        variant_explanation = self._extract_section(result_text, "变体解析")
        variant_answer = self._extract_section(result_text, "变体答案")
        
        # 验证必需字段
        if not variant_content:
            raise ValueError(f"AI 返回内容缺少【变体题目】部分\n原始内容: {result_text[:500]}...")
        if not variant_explanation:
            raise ValueError(f"AI 返回内容缺少【变体解析】部分\n原始内容: {result_text[:500]}...")
        if not variant_answer:
            raise ValueError(f"AI 返回内容缺少【变体答案】部分\n原始内容: {result_text[:500]}...")
        
        return {
            "variant_content": variant_content,
            "variant_explanation": variant_explanation,
            "variant_answer": variant_answer,
            "ai_model": self.model_name
        }

    async def generate_multiple_variants(
        self,
        original_content: str,
        original_explanation: str,
        original_answer: str,
        modification_requirement: str = "",
        count: int = 1,
        max_tokens: int = None,
        temperature: float = 0.7,
        max_rounds: int = 20,
        use_stream: bool = True  # 接受但不使用（为了兼容API调用）
    ) -> Dict[str, Any]:
        """
        批量生成多个变体题目
        
        Args:
            original_content: 原题目
            original_explanation: 原解析
            original_answer: 原答案
            modification_requirement: 修改要求
            count: 生成数量
            max_tokens: 每轮最大token数
            temperature: 温度参数
            max_rounds: 最大续写轮数
            
        Returns:
            dict: {
                "success": bool,
                "count": int,
                "variants": List[Dict],
                "error": str (if failed)
            }
        """
        try:
            if count > 50:
                return {
                    "success": False,
                    "error": "单次最多生成50个变体"
                }
            
            variants = []
            for i in range(count):
                print(f"\n=== 生成第 {i + 1}/{count} 个变体 ===\n")
                
                try:
                    result = await self.generate_problem_variant_with_explanation(
                        original_content=original_content,
                        original_explanation=original_explanation,
                        original_answer=original_answer,
                        modification_requirement=modification_requirement,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        max_rounds=max_rounds
                    )
                    
                    variants.append({
                        "index": i + 1,
                        "success": True,
                        **result
                    })
                    
                except Exception as e:
                    variants.append({
                        "index": i + 1,
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "count": len([v for v in variants if v.get("success", False)]),
                "total": count,
                "variants": variants,
                "ai_model": self.model_name
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"批量生成失败: {str(e)}"
            }
    
    @staticmethod
    def _extract_last_brace_block(text: str) -> str:
        """
        从字符串末尾开始，提取最近一对完整的大括号内容（包含大括号）
        """
        if not text:
            return ""

        stack = 0
        end = -1

        for i in range(len(text) - 1, -1, -1):
            ch = text[i]

            if ch == '}':
                if stack == 0:
                    end = i
                stack += 1

            elif ch == '{':
                stack -= 1
                if stack == 0 and end != -1:
                    return text[i:end + 1]

        return ""
    
    @staticmethod
    def _extract_section(text: str, section_name: str) -> str:
        """从文本中提取指定分隔符之间的内容"""
        pattern = rf'【{section_name}】\s*([\s\S]*?)(?=【|$)'
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return ""


# 全局服务实例
deep_transformer_service = DeepTransformerService()
