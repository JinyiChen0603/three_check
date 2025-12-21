"""
难度检测服务模块
使用 Doubao Seed Thinking 进行对抗验证
"""

import asyncio
from typing import Dict, Any, Optional
import httpx
import json
import re

from app.config import settings


class DifficultyCheckService:
    """题目难度检测服务 - 使用 Doubao Seed Thinking 对抗验证"""
    
    def __init__(self):
        self.api_key = settings.DOUBAO_API_KEY
        self.model = "doubao-seed-1-6-thinking-250715"  # Doubao Seed Thinking 模型
        # Doubao API endpoint (火山引擎)
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
                "verdict": str,
                "ai_model": str,
                "error": str  # 错误信息（如果失败）
            }
        """
        try:
            # 构建prompt
            prompt = f"""请直接给出以下数学题目的最终答案，无需解题过程，将答案放在\\boxed{{}}中。

题目：
{problem}

答案："""
            
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
                "verdict": "难度合格" if is_passed else "题目太简单",
                "ai_model": self.model
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
        单次验证尝试（使用流式响应）
        
        Args:
            prompt: 提示词
            standard_answer: 标准答案
            
        Returns:
            Dict: 单次尝试的结果
        """
        try:
            # 调用Doubao API（流式响应）
            async with httpx.AsyncClient(timeout=600.0) as client:
                # 流式请求
                async with client.stream(
                    "POST",
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
                                "content": "You are a math expert. Give direct answer only. Put your final answer within \\boxed{}."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "stream": True,  # 启用流式响应
                        "temperature": 0.6,
                    }
                ) as response:
                    response.raise_for_status()
                    
                    # 读取流式响应
                    full_content = ""
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or line == "data: [DONE]":
                            continue
                        
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])  # 去掉 "data: " 前缀
                                
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    
                                    # 提取 reasoning_content 和 content
                                    reason_piece = delta.get('reasoning_content', '')
                                    content_piece = delta.get('content', '')
                                    
                                    if reason_piece:
                                        full_content += reason_piece
                                    if content_piece:
                                        full_content += content_piece
                            except:
                                continue
                    
                    if not full_content:
                        raise Exception("Empty response received")
                    
                    # 判断答案是否正确
                    is_correct = self._check_answer(full_content, standard_answer)
                    
                    return {
                        "success": True,
                        "ai_answer": full_content[:500],  # 只保存前500字符用于调试
                        "is_correct": is_correct
                    }
        
        except Exception as e:
            raise Exception(f"单次验证失败: {str(e)}")
    
    def _check_answer(self, ai_answer: str, standard_answer: str) -> bool:
        """
        检查答案是否正确（支持 \boxed{} 格式）
        
        Args:
            ai_answer: AI给出的答案
            standard_answer: 标准答案
            
        Returns:
            bool: 是否正确
        """
        # 辅助函数：规范化答案
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
        
        # 规范化两个答案
        extracted_model = normalize_answer(ai_answer)
        clean_truth = normalize_answer(standard_answer)
        
        # 方法1: 直接字符串匹配
        if extracted_model and extracted_model == clean_truth:
            return True
        
        # 方法2: 检查标准答案是否在AI答案的末尾（后50个字符）
        if clean_truth and clean_truth in ai_answer.replace(' ', '')[-50:]:
            return True
        
        # 方法3: 对于包含多个元素的答案（如坐标、多解），尝试集合匹配
        if ',' in extracted_model and ',' in clean_truth:
            # 提取所有括号内的内容作为元素
            model_elements = re.findall(r'\([^)]+\)', extracted_model)
            truth_elements = re.findall(r'\([^)]+\)', clean_truth)
            
            # 如果都找到多个括号元素，按集合比较
            if len(model_elements) > 1 and len(truth_elements) > 1:
                model_set = set(e.replace(' ', '') for e in model_elements)
                truth_set = set(e.replace(' ', '') for e in truth_elements)
                if model_set == truth_set:
                    return True
            
            # 如果没有多个括号，尝试按逗号分割（处理简单列表）
            if not model_elements or not truth_elements:
                model_items = [item.strip() for item in extracted_model.replace('(', '').replace(')', '').replace('{', '').replace('}', '').split(',')]
                truth_items = [item.strip() for item in clean_truth.replace('(', '').replace(')', '').replace('{', '').replace('}', '').split(',')]
                
                # 如果元素数量相同且都不止一个，尝试集合匹配
                if len(model_items) > 1 and len(truth_items) > 1 and len(model_items) == len(truth_items):
                    if set(model_items) == set(truth_items):
                        return True
        
        return False


# 全局服务实例
difficulty_check_service = DifficultyCheckService()

