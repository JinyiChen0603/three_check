"""
难度检测服务模块
使用豆包进行 8 次对抗验证
使用 GPT-4o 进行答案校验
"""

import asyncio
import re
from typing import Dict, Any, Optional, List, Callable

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
        progress_callback: Optional[Callable[[dict], None]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        验证题目难度
        
        Args:
            problem: 题目内容
            answer: 标准答案
            explanation: 解析
            attempts: 尝试次数（默认8）
            progress_callback: 可选的进度回调函数，接收 {"progress": int} 格式的字典
            
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
            
            # 进度追踪（并发安全）
            completed_attempts = 0
            lock = asyncio.Lock()
            
            async def limited_attempt():
                nonlocal completed_attempts
                try:
                    async with semaphore:
                        return await self._single_attempt(messages, answer)
                finally:
                    # 无论成功或异常，都更新进度
                    async with lock:
                        completed_attempts += 1
                        # 只发送 0-99% 的进度，100% 由调用方在存储最终结果时发送
                        # 避免异步回调与最终结果写入产生竞态条件
                        if progress_callback and completed_attempts < attempts:
                            progress = int(completed_attempts / attempts * 100)
                            progress_callback({"progress": progress})
            
            # 并发执行多次验证（受并发数限制）
            tasks = [limited_attempt() for _ in range(attempts)]
            
            attempt_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 注意：不在这里发送 100% 进度，由调用方在存储最终结果时发送
            # 避免异步回调与最终结果写入产生竞态条件
            
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
                "ai_answer": ai_answer[-200:] if ai_answer else "",
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
    
    def _extract_boxed_content(self, text: str) -> str:
        """
        健壮地提取 \boxed{} 中的内容，支持嵌套大括号
        
        示例:
            \boxed{10} -> 10
            \boxed{\frac{1}{2}} -> \frac{1}{2}
            \boxed{(1,2),(3,4)} -> (1,2),(3,4)
        """
        if not text or '\\boxed' not in text:
            return text
        
        # 找到所有 \boxed 匹配，取最后一个
        matches = list(re.finditer(r'\\boxed\s*\{', text))
        if not matches:
            return text
        
        # 从最后一个 \boxed 开始
        last_match = matches[-1]
        start_pos = last_match.end() - 1  # { 的位置
        
        # 括号计数法：找到匹配的 }
        brace_count = 0
        for i in range(start_pos, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    # 找到匹配的 }
                    return text[start_pos + 1:i]
        
        # 如果没找到匹配的 }，返回从 { 到末尾的内容
        return text[start_pos + 1:]
    
    def _normalize_math_expression(self, text: str) -> str:
        """
        标准化数学表达式，使等价的表达式具有相同的标准形式
        
        处理内容：
        1. 提取 \boxed{} 内容
        2. 移除 LaTeX 标记
        3. 统一空格、大小写
        4. 转换常见 LaTeX 命令
        5. 标准化符号
        """
        if not text:
            return ""
        
        text = str(text).strip()
        
        # 1. 提取 boxed 内容
        text = self._extract_boxed_content(text)
        
        # 2. 移除 LaTeX 数学模式标记
        text = text.replace('\\[', '').replace('\\]', '')
        text = text.replace('\\(', '').replace('\\)', '')
        text = text.replace('$', '')
        
        # 3. 处理 \frac{a}{b} -> (a)/(b)
        # 使用递归处理嵌套分数
        while '\\frac' in text:
            # 匹配 \frac{分子}{分母}，支持嵌套括号
            match = re.search(r'\\frac\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', text)
            if match:
                numerator = match.group(1)
                denominator = match.group(2)
                # 替换为 (分子)/(分母)
                text = text[:match.start()] + f'({numerator})/({denominator})' + text[match.end():]
            else:
                break
        
        # 4. 处理 \sqrt{n} (保留形式)
        text = re.sub(r'\\sqrt\s*\{([^}]+)\}', r'sqrt(\1)', text)
        
        # 5. 移除常见 LaTeX 命令的反斜杠（保留内容）
        latex_commands = [
            'sin', 'cos', 'tan', 'cot', 'sec', 'csc',
            'arcsin', 'arccos', 'arctan',
            'log', 'ln', 'exp',
            'angle', 'circ', 'degree', 'cdot', 'times',
            'alpha', 'beta', 'gamma', 'theta', 'pi',
            'infty', 'pm', 'mp'
        ]
        for cmd in latex_commands:
            text = text.replace(f'\\{cmd}', cmd)
        
        # 6. 统一角度符号
        text = text.replace('°', 'degree')
        text = text.replace('度', 'degree')
        
        # 7. 统一负号和减号
        text = text.replace('−', '-')  # 全角转半角
        text = text.replace('—', '-')  # 破折号
        
        # 8. 统一乘号
        text = text.replace('×', '*')
        text = text.replace('·', '*')
        
        # 9. 移除所有空格
        text = text.replace(' ', '')
        
        # 10. 转小写（对于字母表达式）
        text = text.lower()
        
        # 11. 移除外层括号（如果有）
        text = text.strip()
        if text.startswith('(') and text.endswith(')'):
            # 检查是否整体括号
            count = 0
            is_whole = True
            for i, char in enumerate(text):
                if char == '(':
                    count += 1
                elif char == ')':
                    count -= 1
                    if count == 0 and i < len(text) - 1:
                        is_whole = False
                        break
            if is_whole:
                text = text[1:-1]
        
        return text.strip()
    
    def _try_evaluate_as_number(self, expr: str) -> Optional[float]:
        """
        尝试将表达式计算为数值
        
        支持：
        - 整数：123
        - 小数：3.14
        - 分数：(1)/(2) 或 1/2
        - 带千分位：1,234.56
        - 科学计数法：1.23e-4
        """
        if not expr:
            return None
        
        try:
            # 1. 移除千分位逗号，尝试直接转换
            expr_clean = expr.replace(',', '')
            return float(expr_clean)
        except ValueError:
            pass
        
        try:
            # 2. 尝试计算简单分数 (a)/(b) 或 a/b
            if '/' in expr:
                # 移除可能的括号
                expr_clean = expr.replace('(', '').replace(')', '')
                parts = expr_clean.split('/')
                if len(parts) == 2:
                    numerator = float(parts[0].strip())
                    denominator = float(parts[1].strip())
                    if denominator != 0:
                        return numerator / denominator
        except (ValueError, ZeroDivisionError):
            pass
        
        return None
    
    def _compare_as_set(self, expr1: str, expr2: str) -> Optional[bool]:
        """
        尝试作为集合/列表比较（顺序无关）
        
        支持格式：
        - 1,2,3
        - (1,2),(3,4)
        - {1,2,3}
        - x=1,y=2
        """
        if ',' not in expr1 or ',' not in expr2:
            return None
        
        # 简单情况：直接按逗号分割
        elements1 = set(e.strip() for e in expr1.split(','))
        elements2 = set(e.strip() for e in expr2.split(','))
        
        if elements1 == elements2:
            return True
        
        # 复杂情况：提取括号内容
        # 例如：(1,2),(3,4)
        pattern = r'\([^)]+\)'
        tuples1 = re.findall(pattern, expr1)
        tuples2 = re.findall(pattern, expr2)
        
        if tuples1 and tuples2:
            set1 = set(t.replace(' ', '') for t in tuples1)
            set2 = set(t.replace(' ', '') for t in tuples2)
            return set1 == set2
        
        return None
    
    def _quick_check_answer(self, ai_answer: str, standard_answer: str) -> Optional[bool]:
        """
        快速答案检查（简单情况，无需调用AI）
        
        返回：
            True: 确定相等
            False: 确定不相等
            None: 无法确定，需要 AI 判断
        """
        # 标准化
        normalized_ai = self._normalize_math_expression(ai_answer)
        normalized_std = self._normalize_math_expression(standard_answer)
        
        # 调试日志
        print(f"[QuickCheck] AI标准化: '{normalized_ai}' | 标准答案: '{normalized_std}'")
        
        # 1. 完全相同
        if normalized_ai == normalized_std:
            print(f"[QuickCheck] ✓ 字符串完全匹配")
            return True
        
        # 2. 都为空
        if not normalized_ai or not normalized_std:
            print(f"[QuickCheck] ✗ 其中一个为空")
            return False
        
        # 3. 数值比较
        num_ai = self._try_evaluate_as_number(normalized_ai)
        num_std = self._try_evaluate_as_number(normalized_std)
        
        if num_ai is not None and num_std is not None:
            is_equal = abs(num_ai - num_std) < 1e-9
            print(f"[QuickCheck] 数值比较: {num_ai} vs {num_std} -> {is_equal}")
            return is_equal
        
        # 4. 集合比较
        set_result = self._compare_as_set(normalized_ai, normalized_std)
        if set_result is not None:
            print(f"[QuickCheck] 集合比较: {set_result}")
            return set_result
        
        # 5. 长答案需要 AI
        if len(normalized_ai) > 100 or len(normalized_std) > 100:
            print(f"[QuickCheck] ? 答案过长，需要 AI")
            return None
        
        # 6. 其他情况，需要 AI
        print(f"[QuickCheck] ? 无法快速判断，需要 AI")
        return None
    
    def _strict_check_answer(self, ai_answer: str, standard_answer: str) -> bool:
        """
        严格的答案检查（作为AI检查的回退方案）
        
        当 GPT-4o 不可用时使用此方法
        """
        print(f"[StrictCheck] 开始回退检查...")
        
        # 复用 quick_check 的逻辑
        result = self._quick_check_answer(ai_answer, standard_answer)
        
        if result is True:
            print(f"[StrictCheck] ✓ 判定为正确")
            return True
        elif result is False:
            print(f"[StrictCheck] ✗ 判定为错误")
            return False
        else:
            # 无法确定时，保守判定为错误（避免误判）
            print(f"[StrictCheck] ✗ 无法确定，保守判定为错误")
            return False


# 全局服务实例
difficulty_check_service = DifficultyCheckService()
