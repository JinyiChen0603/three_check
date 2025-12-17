"""
验证服务模块
使用 Doubao 进行对抗验证（难度检测）
"""

import asyncio
from typing import Dict, Any, List, Optional
import httpx
import json

from app.config import settings


class ValidationService:
    """题目验证服务（对抗验证）"""
    
    def __init__(self):
        self.api_key = settings.DOUBAO_API_KEY
        self.model = settings.DOUBAO_MODEL
        # Doubao API endpoint（需要根据实际情况调整）
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    
    async def validate_difficulty(
        self,
        problem: str,
        answer: str,
        explanation: Optional[str] = None,
        attempts: int = 8
    ) -> Dict[str, Any]:
        """
        验证题目难度（对抗验证）
        
        通过让AI模型多次回答题目，统计正确率来判断难度：
        - 正确次数 <= 4：难度合格（题目有一定难度）
        - 正确次数 > 4：难度不合格（题目太简单）
        
        Args:
            problem: 题目内容
            answer: 标准答案
            explanation: 解析（可选）
            attempts: 尝试次数（默认8次）
            
        Returns:
            Dict: {
                "success": bool,
                "is_passed": bool,  # 是否通过验证
                "attempts": int,    # 尝试次数
                "correct_count": int,  # 正确次数
                "correct_rate": float,  # 正确率
                "attempts_details": List[Dict],  # 每次尝试的详细结果
                "error": str  # 错误信息（如果失败）
            }
        """
        try:
            # 构建prompt
            prompt = f"""请解答以下数学题目，直接给出最终答案即可，不需要解题过程。

题目：
{problem}

请给出你的答案："""
            
            # 并发进行多次验证
            tasks = [
                self._single_attempt(prompt, answer)
                for _ in range(attempts)
            ]
            
            attempt_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            correct_count = 0
            valid_attempts = []
            
            for i, result in enumerate(attempt_results):
                if isinstance(result, Exception):
                    # 如果某次尝试失败，记录错误
                    valid_attempts.append({
                        "attempt": i + 1,
                        "success": False,
                        "error": str(result)
                    })
                else:
                    valid_attempts.append(result)
                    if result.get("is_correct", False):
                        correct_count += 1
            
            # 判断是否通过验证
            # 正确次数 <= 4 才算通过（题目有难度）
            is_passed = correct_count <= settings.VALIDATION_MAX_CORRECT
            correct_rate = correct_count / attempts if attempts > 0 else 0
            
            return {
                "success": True,
                "is_passed": is_passed,
                "attempts": attempts,
                "correct_count": correct_count,
                "correct_rate": correct_rate,
                "attempts_details": valid_attempts,
                "verdict": "难度合格" if is_passed else "题目太简单"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"验证失败: {str(e)}"
            }
    
    async def _single_attempt(
        self,
        prompt: str,
        standard_answer: str
    ) -> Dict[str, Any]:
        """
        单次验证尝试
        
        Args:
            prompt: 提示词
            standard_answer: 标准答案
            
        Returns:
            Dict: 单次尝试的结果
        """
        try:
            # 调用Doubao API
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
                        "max_tokens": 1000,
                        "temperature": 0.7,  # 使用一定随机性
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 提取AI的答案
                ai_answer = result["choices"][0]["message"]["content"].strip()
                
                # 判断答案是否正确
                is_correct = self._check_answer(ai_answer, standard_answer)
                
                return {
                    "success": True,
                    "ai_answer": ai_answer,
                    "is_correct": is_correct
                }
        
        except Exception as e:
            raise Exception(f"单次验证失败: {str(e)}")
    
    def _check_answer(self, ai_answer: str, standard_answer: str) -> bool:
        """
        检查答案是否正确
        
        这是一个简化的比较逻辑，实际应用中可能需要更复杂的数学表达式比较
        
        Args:
            ai_answer: AI给出的答案
            standard_answer: 标准答案
            
        Returns:
            bool: 是否正确
        """
        # 简单的字符串匹配（实际应用中需要更智能的比较）
        # 去除空格、标点符号后比较
        ai_clean = self._clean_answer(ai_answer)
        standard_clean = self._clean_answer(standard_answer)
        
        # 检查标准答案是否在AI答案中
        return standard_clean in ai_clean or ai_clean in standard_clean
    
    def _clean_answer(self, answer: str) -> str:
        """
        清理答案（去除空格、标点等）
        
        Args:
            answer: 原始答案
            
        Returns:
            str: 清理后的答案
        """
        import re
        # 去除空格
        cleaned = answer.replace(" ", "").replace("\n", "")
        # 转为小写
        cleaned = cleaned.lower()
        # 去除常见标点
        cleaned = re.sub(r'[，。；：！？、,.;:!?]', '', cleaned)
        return cleaned


class QualityCheckService:
    """质量检查服务（三维度）"""
    
    def __init__(self):
        self.validation_service = ValidationService()
        self.openai_api_key = settings.OPENAI_API_KEY
        self.gpt4_model = settings.OPENAI_GPT4_MODEL
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    async def full_quality_check(
        self,
        problem: str,
        answer: str,
        explanation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        完整的质量检查（三个维度）
        
        1. 难度检测：Doubao对抗验证（8次，≤4次正确）
        2. 原创性检测：GPT-4o Research联网搜索
        3. 数学严谨性检测：GPT-4o判断
        
        Args:
            problem: 题目内容
            answer: 标准答案
            explanation: 解析
            
        Returns:
            Dict: {
                "success": bool,
                "all_passed": bool,  # 三个维度是否都通过
                "difficulty": Dict,  # 难度检测结果
                "originality": Dict,  # 原创性检测结果
                "rigor": Dict,  # 严谨性检测结果
            }
        """
        try:
            # 并发执行三个维度的检测
            difficulty_task = self.validation_service.validate_difficulty(
                problem, answer, explanation
            )
            originality_task = self._check_originality(problem)
            rigor_task = self._check_rigor(problem, answer, explanation)
            
            results = await asyncio.gather(
                difficulty_task,
                originality_task,
                rigor_task,
                return_exceptions=True
            )
            
            difficulty_result = results[0] if not isinstance(results[0], Exception) else {"success": False, "error": str(results[0])}
            originality_result = results[1] if not isinstance(results[1], Exception) else {"success": False, "error": str(results[1])}
            rigor_result = results[2] if not isinstance(results[2], Exception) else {"success": False, "error": str(results[2])}
            
            # 判断是否全部通过
            all_passed = (
                difficulty_result.get("success", False) and difficulty_result.get("is_passed", False) and
                originality_result.get("success", False) and originality_result.get("is_original", False) and
                rigor_result.get("success", False) and rigor_result.get("is_rigorous", False)
            )
            
            return {
                "success": True,
                "all_passed": all_passed,
                "difficulty": difficulty_result,
                "originality": originality_result,
                "rigor": rigor_result,
                "summary": {
                    "difficulty_passed": difficulty_result.get("is_passed", False),
                    "originality_passed": originality_result.get("is_original", False),
                    "rigor_passed": rigor_result.get("is_rigorous", False),
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"质量检查失败: {str(e)}"
            }
    
    async def _check_originality(self, problem: str) -> Dict[str, Any]:
        """
        检查原创性（使用GPT-4o Research联网搜索）
        
        Args:
            problem: 题目内容
            
        Returns:
            Dict: 原创性检测结果
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
                        "model": self.gpt4_model,
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
                    "verdict": "原创性合格" if is_original else "可能存在相似题目"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"原创性检测失败: {str(e)}"
            }
    
    async def _check_rigor(
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
            Dict: 严谨性检测结果
        """
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
                    "verdict": "数学严谨性合格" if is_rigorous else "存在严谨性问题"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"严谨性检测失败: {str(e)}"
            }


# 全局服务实例
validation_service = ValidationService()
quality_check_service = QualityCheckService()

