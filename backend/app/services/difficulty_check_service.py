"""
难度检测服务模块
使用豆包进行 8 次对抗验证
使用 GPT-4o 进行答案校验
"""

import asyncio
import re
from typing import Dict, Any, Optional, List

from app.services.llm import doubao, gpt4o, LLMClient
from app.config import settings


class DifficultyCheckService:
    """
    题目难度检测服务
    
    使用豆包进行对抗验证：
    - 8 次验证，正确次数 ≤4 才算合格
    - 使用 GPT-4o 进行答案对比
    """
    
    def __init__(
        self,
        validation_client: LLMClient = None,
        answer_check_client: LLMClient = None,
        max_concurrent: int = 4
    ):
        """
        初始化难度检测服务
        
        Args:
            validation_client: 用于对抗验证的客户端，默认使用豆包
            answer_check_client: 用于答案校验的客户端，默认使用 gpt4o
            max_concurrent: 最大并发数（8次验证中同时执行的最大数量），默认4
        """
        self.validation_client = validation_client or doubao
        self.answer_check_client = answer_check_client or gpt4o
        
        # 验证参数
        self.attempts = settings.VALIDATION_ATTEMPTS  # 16次
        self.max_correct = settings.VALIDATION_MAX_CORRECT  # ≤8次正确
        
        # 并发控制
        self.max_concurrent = max_concurrent  # 最大并发数
    
    async def validate_difficulty(
        self,
        problem: str,
        answer: str,
        explanation: Optional[str] = None,
        attempts: int = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        验证题目难度
        
        Args:
            problem: 题目内容
            answer: 标准答案
            explanation: 解析（可选）
            attempts: 尝试次数（默认8）
            
        Returns:
            Dict: 验证结果
        """
        if attempts is None:
            attempts = self.attempts
        
        try:
            # 构建提示词
            messages = self._build_messages(problem)
            
            # 使用 Semaphore 限制并发数
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def limited_attempt():
                async with semaphore:
                    return await self._single_attempt(messages, answer)
            
            # 并发执行多次验证（受并发数限制）
            tasks = [limited_attempt() for _ in range(attempts)]
            
            attempt_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            correct_count = 0
            valid_attempts = []
            
            for i, result in enumerate(attempt_results):
                if isinstance(result, Exception):
                    valid_attempts.append({
                        "attempt": i + 1,
                        "success": False,
                        "error": str(result)
                    })
                else:
                    valid_attempts.append({
                        "attempt": i + 1,
                        **result
                    })
                    if result.get("is_correct", False):
                        correct_count += 1
            
            # 判断是否通过验证
            is_passed = correct_count <= self.max_correct
            correct_rate = correct_count / attempts if attempts > 0 else 0
            
            return {
                "success": True,
                "is_passed": is_passed,
                "mode": "doubao",
                "attempts": attempts,
                "correct_count": correct_count,
                "correct_rate": correct_rate,
                "max_correct_threshold": self.max_correct,
                "attempts_details": valid_attempts,
                "verdict": "难度合格" if is_passed else "难度不合格",
                "summary": f"豆包{'通过' if is_passed else '未通过'}({correct_count}/{attempts})",
                "ai_model": f"豆包 ({self.validation_client.model})"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"难度验证失败: {str(e)}"
            }
    
    def _build_messages(self, problem: str) -> List[Dict[str, str]]:
        """构建验证提示词"""
        return [
            {
                "role": "system",
                "content": "You are a math expert. Give direct answer only. Put your final answer within \\boxed{}."
            },
            {
                "role": "user",
                "content": f"""请直接给出以下数学题目的最终答案，无需解题过程，将答案放在\\boxed{{}}中。

题目：
{problem}

答案："""
            }
        ]
    
    async def _single_attempt(
        self,
        messages: List[Dict[str, str]],
        standard_answer: str
    ) -> Dict[str, Any]:
        """单次验证尝试"""
        try:
            # 调用豆包
            response = await self.validation_client.chat(
                messages=messages,
                temperature=0.7
            )
            
            # 提取内容（智谱 thinking 模式返回 reasoning_content 和 content）
            reasoning, content = LLMClient.extract_thinking_content(response)
            ai_answer = content if content else reasoning
            
            if not ai_answer:
                ai_answer = LLMClient.extract_content(response)
            
            # 使用 GPT-4o 进行答案对比
            is_correct = await self._check_answer_with_ai(ai_answer, standard_answer)
            
            return {
                "success": True,
                "ai_answer": ai_answer[:500] if ai_answer else "",
                "is_correct": is_correct
            }
        
        except Exception as e:
            raise Exception(f"验证失败: {str(e)}")
    
    async def _check_answer_with_ai(self, ai_answer: str, standard_answer: str) -> bool:
        """
        使用 GPT-4o 判断答案是否正确
        """
        # 先用简单规则快速判断
        quick_result = self._quick_check_answer(ai_answer, standard_answer)
        if quick_result is not None:
            return quick_result
        
        # 复杂情况使用 GPT-4o 判断
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a math answer comparison expert. Only answer YES or NO."
                },
                {
                    "role": "user",
                    "content": f"""请判断以下两个数学答案是否等价。

AI模型给出的答案：
{ai_answer}

标准答案：
{standard_answer}

判断规则：
1. 数学表达式等价即可（如 2x+1 和 1+2x 是等价的）
2. 数值答案允许不同的表示形式（如 0.5 和 1/2 是等价的）
3. 集合答案元素相同即可，顺序无关
4. LaTeX 格式差异忽略
5. 只关注最终答案，忽略解题过程

请只回答 "YES" 或 "NO"，不要解释。"""
                }
            ]
            
            response = await self.answer_check_client.chat(
                messages=messages,
                temperature=0,
                max_tokens=10
            )
            
            content = LLMClient.extract_content(response)
            content_upper = content.strip().upper()
            
            if "YES" in content_upper:
                return True
            elif "NO" in content_upper:
                return False
            else:
                # 无法确定，回退到严格检查
                print(f"GPT答案对比返回不明确结果: {content}")
                return self._strict_check_answer(ai_answer, standard_answer)
        
        except Exception as e:
            print(f"GPT答案对比失败，回退到正则检查: {str(e)}")
            return self._strict_check_answer(ai_answer, standard_answer)
    
    def _quick_check_answer(self, ai_answer: str, standard_answer: str) -> Optional[bool]:
        """快速答案检查（简单情况，无需调用AI）"""
        def normalize_answer(text):
            if not text:
                return ""
            text = str(text)
            
            # 提取 \boxed{} 中的内容（取最后一个）
            boxed_matches = re.findall(r'\\boxed\s*\{(.*?)\}', text)
            if boxed_matches:
                text = boxed_matches[-1]
            
            # 移除各种 LaTeX 数学模式标记
            text = text.replace('\\[', '').replace('\\]', '')
            text = text.replace('\\(', '').replace('\\)', '')
            text = text.replace('$', '').replace(' ', '').strip()
            
            return text
        
        extracted_model = normalize_answer(ai_answer)
        clean_truth = normalize_answer(standard_answer)
        
        # 直接字符串匹配
        if extracted_model and extracted_model == clean_truth:
            return True
        
        # 数字比较
        try:
            num_model = float(extracted_model.replace(',', ''))
            num_truth = float(clean_truth.replace(',', ''))
            return abs(num_model - num_truth) < 1e-9
        except (ValueError, AttributeError):
            pass
        
        # 短答案且不同，可能需要AI判断
        if len(extracted_model) < 50 and len(clean_truth) < 50:
            if not extracted_model or not clean_truth:
                return False
            return None
        
        return None
    
    def _strict_check_answer(self, ai_answer: str, standard_answer: str) -> bool:
        """严格的答案检查（作为AI检查的回退方案）"""
        def normalize_answer(text):
            if not text:
                return ""
            text = str(text)
            
            boxed_matches = re.findall(r'\\boxed\s*\{(.*?)\}', text)
            if boxed_matches:
                text = boxed_matches[-1]
            
            text = text.replace('\\[', '').replace('\\]', '')
            text = text.replace('\\(', '').replace('\\)', '')
            text = text.replace('$', '').replace(' ', '').strip()
            
            return text
        
        extracted_model = normalize_answer(ai_answer)
        clean_truth = normalize_answer(standard_answer)
        
        # 直接匹配
        if extracted_model and extracted_model == clean_truth:
            return True
        
        # 检查标准答案是否在AI答案末尾
        if clean_truth and clean_truth in ai_answer.replace(' ', '')[-50:]:
            return True
        
        # 集合匹配
        if ',' in extracted_model and ',' in clean_truth:
            model_elements = re.findall(r'\([^)]+\)', extracted_model)
            truth_elements = re.findall(r'\([^)]+\)', clean_truth)
            
            if len(model_elements) > 1 and len(truth_elements) > 1:
                model_set = set(e.replace(' ', '') for e in model_elements)
                truth_set = set(e.replace(' ', '') for e in truth_elements)
                if model_set == truth_set:
                    return True
        
        return False


# 全局服务实例
difficulty_check_service = DifficultyCheckService()
