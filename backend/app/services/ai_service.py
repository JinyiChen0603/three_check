"""
AI 服务模块
集成 DeepSeek Math-V2 用于题目创新和变形
"""

from typing import Dict, Any, Optional
import httpx

from app.config import settings


class DeepSeekService:
    """DeepSeek Math-V2 服务（题目创新）- 通过 Canopy Wave"""
    
    def __init__(self):
        # 使用 Canopy Wave API Key 而不是 DeepSeek 直接 API
        self.api_key = settings.CANOPY_WAVE_API_KEY
        self.model = "deepseek-ai/DeepSeek-Math-V2"
        # Canopy Wave API endpoint (兼容 OpenAI 格式)
        self.base_url = "https://api.canopywave.io/v1/chat/completions"
    
    async def generate_variant(
        self,
        original_problem: str,
        original_answer: str,
        original_explanation: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成题目变体
        
        要求：新题目与原题目必须有明显不同，包括但不限于：
        - 表述方式不同
        - 数字不同
        - 解答方法不同
        
        Args:
            original_problem: 原题目内容
            original_answer: 原题目答案
            original_explanation: 原题目解析
            custom_prompt: 用户自定义的变形prompt
            
        Returns:
            Dict: {
                "success": bool,
                "new_problem": str,  # 新题目
                "new_answer": str,   # 新答案
                "new_explanation": str,  # 新解析
                "changes": str,  # 变化说明
                "error": str  # 错误信息（如果失败）
            }
        """
        try:
            # 构建prompt
            if custom_prompt:
                # 使用用户自定义prompt
                prompt = f"""{custom_prompt}

【原题目】
{original_problem}

【原答案】
{original_answer}"""
                
                if original_explanation:
                    prompt += f"\n\n【原解析】\n{original_explanation}"
                
                prompt += """

请基于以上信息，生成一个新的题目。

请按照以下格式返回：
【新题目】
（新题目的完整内容）

【新答案】
（新题目的标准答案）

【新解析】
（新题目的解题过程）

【变化说明】
（说明相比原题做了哪些创新和改变）"""
            
            else:
                # 使用默认prompt
                prompt = f"""请基于以下数学题目，创造一个新的变体题目。

【原题目】
{original_problem}

【原答案】
{original_answer}"""
                
                if original_explanation:
                    prompt += f"\n\n【原解析】\n{original_explanation}"
                
                prompt += """

要求：
1. 新题目必须与原题目有明显不同，包括：
   - 改变表述方式
   - 改变具体数字
   - 可以改变解答方法或考查角度
2. 新题目需要保持与原题目相近的难度
3. 新题目必须有明确的答案（不要证明题、判断题或选择题）
4. 确保数学严谨性

请按照以下格式返回：
【新题目】
（新题目的完整内容）

【新答案】
（新题目的标准答案）

【新解析】
（新题目的解题过程）

【变化说明】
（说明相比原题做了哪些创新和改变）"""
            
            # 调用DeepSeek API
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "你是一位资深的数学题目创作专家，擅长基于已有题目创造新的变体题目。"
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 3000,
                        "temperature": 0.8,  # 较高温度以增加创新性
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 解析返回结果
                content = result["choices"][0]["message"]["content"]
                parsed_result = self._parse_variant_result(content)
                
                return {
                    "success": True,
                    "raw_content": content,
                    **parsed_result
                }
        
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP请求失败: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"生成变体失败: {str(e)}"
            }
    
    def _parse_variant_result(self, content: str) -> Dict[str, str]:
        """
        解析变体生成结果
        
        Args:
            content: AI返回的内容
            
        Returns:
            Dict: 包含new_problem, new_answer, new_explanation, changes的字典
        """
        result = {
            "new_problem": "",
            "new_answer": "",
            "new_explanation": "",
            "changes": ""
        }
        
        # 解析不同部分
        sections = content.split("【")
        
        for section in sections:
            if section.startswith("新题目】"):
                content_part = section.replace("新题目】", "").strip()
                if "【" in content_part:
                    content_part = content_part.split("【")[0].strip()
                result["new_problem"] = content_part
            
            elif section.startswith("新答案】"):
                content_part = section.replace("新答案】", "").strip()
                if "【" in content_part:
                    content_part = content_part.split("【")[0].strip()
                result["new_answer"] = content_part
            
            elif section.startswith("新解析】"):
                content_part = section.replace("新解析】", "").strip()
                if "【" in content_part:
                    content_part = content_part.split("【")[0].strip()
                result["new_explanation"] = content_part
            
            elif section.startswith("变化说明】"):
                content_part = section.replace("变化说明】", "").strip()
                result["changes"] = content_part
        
        return result
    
    async def generate_multiple_variants(
        self,
        original_problem: str,
        original_answer: str,
        original_explanation: Optional[str] = None,
        count: int = 1,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批量生成多个变体
        
        Args:
            original_problem: 原题目
            original_answer: 原答案
            original_explanation: 原解析
            count: 生成数量（最多10个）
            custom_prompt: 自定义prompt
            
        Returns:
            Dict: {
                "success": bool,
                "variants": List[Dict],  # 变体列表
                "error": str
            }
        """
        try:
            if count > 10:
                return {
                    "success": False,
                    "error": "单个母题最多生成10个变体"
                }
            
            variants = []
            for i in range(count):
                result = await self.generate_variant(
                    original_problem,
                    original_answer,
                    original_explanation,
                    custom_prompt
                )
                
                if result["success"]:
                    variants.append({
                        "index": i + 1,
                        **result
                    })
                else:
                    # 如果生成失败，记录错误
                    variants.append({
                        "index": i + 1,
                        "success": False,
                        "error": result.get("error", "未知错误")
                    })
            
            return {
                "success": True,
                "count": len([v for v in variants if v.get("success", False)]),
                "variants": variants
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"批量生成失败: {str(e)}"
            }


class GPTService:
    """GPT-4o 服务（用于生成相似答案等）- 通过 OpenRouter"""
    
    def __init__(self):
        # 使用 OpenRouter API Key 而不是 OpenAI 直接 API
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = "openai/gpt-4o"  # OpenRouter 格式
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
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
                "similar_answers": List[str],  # 相似答案列表
                "error": str
            }
        """
        try:
            prompt = f"""请为以下数学题目生成{count}个相似但错误的答案。

题目：
{problem}

正确答案：
{correct_answer}

要求：
1. 生成的答案看起来合理，但实际是错误的
2. 错误答案要足够相似，能迷惑做题者
3. 每个答案单独一行

请直接列出{count}个答案，每行一个："""
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 500,
                        "temperature": 0.9,  # 较高温度以增加多样性
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                content = result["choices"][0]["message"]["content"]
                
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
                    "similar_answers": similar_answers[:count]
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"生成相似答案失败: {str(e)}"
            }


# 全局服务实例
deepseek_service = DeepSeekService()
gpt_service = GPTService()

