"""
难度检测服务模块
支持两种验证模式：
1. 豆包模式:Doubao Seed Thinking 8次对抗验证(保留原逻辑)
2. 双模型模式:ChatGPT + 智谱GLM 各16次验证(新增)
"""

import asyncio
from typing import Dict, Any, Optional, List, Literal
import httpx
import json
import re

from app.config import settings


class DifficultyCheckService:
    """题目难度检测服务 - 支持多种验证模式"""
    
    def __init__(self):
        # ==================== 豆包配置（保留原有） ====================
        self.doubao_api_key = settings.DOUBAO_API_KEY
        self.doubao_model = "doubao-seed-1-6-thinking-250715"
        self.doubao_base_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        
        # ==================== ChatGPT 配置（新增） ====================
        # 通过香港代理访问 OpenRouter（绕过地区限制）
        self.chatgpt_api_key = settings.OPENROUTER_API_KEY
        # self.chatgpt_model = "openai/gpt-5.2-pro"  # gpt-5.2-pro 暂时注释，待代理配置完善后启用
        self.chatgpt_model = "openai/gpt-4o"  # 暂时使用 gpt-4o
        self.chatgpt_base_url = "https://www.stem-align.com/v2/openrouter/api/v1/chat/completions"
        
        # ==================== 智谱 GLM 配置（新增） ====================
        self.zhipu_api_key = settings.ZHIPU_API_KEY
        self.zhipu_model = settings.ZHIPU_MODEL
        self.zhipu_base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        
        # 验证参数
        self.dual_model_attempts = settings.VALIDATION_ATTEMPTS  # 双模型各16次
        self.dual_model_max_correct = settings.VALIDATION_MAX_CORRECT  # 每个模型<=8
        self.doubao_attempts = 8  # 豆包8次
        self.doubao_max_correct = 4  # 豆包<=4
    
    # ==================== 主验证方法（默认使用双模型） ====================
    
    async def validate_difficulty(
        self,
        problem: str,
        answer: str,
        explanation: Optional[str] = None,
        attempts: int = None,
        mode: Literal["dual", "doubao"] = "dual"
    ) -> Dict[str, Any]:
        """
        验证题目难度
        
        Args:
            problem: 题目内容
            answer: 标准答案
            explanation: 解析（可选）
            attempts: 尝试次数（可选，默认根据模式自动选择）
            mode: 验证模式
                - "dual": 双模型验证（ChatGPT + 智谱GLM 各16次，默认）
                - "doubao": 豆包验证（8次）
            
        Returns:
            Dict: 验证结果
        """
        if mode == "doubao":
            return await self.validate_with_doubao(problem, answer, explanation, attempts)
        else:
            return await self.validate_with_dual_models(problem, answer, explanation, attempts)
    
    # ==================== 双模型验证（新增：ChatGPT + 智谱GLM） ====================
    
    async def validate_with_dual_models(
        self,
        problem: str,
        answer: str,
        explanation: Optional[str] = None,
        attempts: int = None
    ) -> Dict[str, Any]:
        """
        双模型验证（ChatGPT + 智谱GLM）
        
        每个模型各做16次验证，正确次数<=8才算通过，两个都要通过
        
        Args:
            problem: 题目内容
            answer: 标准答案
            explanation: 解析（可选）
            attempts: 每个模型的尝试次数（默认16）
            
        Returns:
            Dict: 验证结果
        """
        if attempts is None:
            attempts = self.dual_model_attempts
        
        try:
            prompt = self._build_prompt(problem)
            
            # 并发执行两个模型的验证
            chatgpt_task = self._validate_with_model("chatgpt", prompt, answer, attempts)
            zhipu_task = self._validate_with_model("zhipu", prompt, answer, attempts)
            
            results = await asyncio.gather(chatgpt_task, zhipu_task, return_exceptions=True)
            
            # 处理结果
            chatgpt_result = results[0] if not isinstance(results[0], Exception) else {
                "success": False, "error": str(results[0]), "correct_count": 0, "is_passed": False
            }
            zhipu_result = results[1] if not isinstance(results[1], Exception) else {
                "success": False, "error": str(results[1]), "correct_count": 0, "is_passed": False
            }
            
            # 两个模型都要通过
            chatgpt_passed = chatgpt_result.get("is_passed", False)
            zhipu_passed = zhipu_result.get("is_passed", False)
            is_passed = chatgpt_passed and zhipu_passed
            
            # 生成总结
            chatgpt_correct = chatgpt_result.get("correct_count", 0)
            zhipu_correct = zhipu_result.get("correct_count", 0)
            
            verdict_parts = []
            if chatgpt_passed:
                verdict_parts.append(f"ChatGPT通过({chatgpt_correct}/{attempts})")
            else:
                verdict_parts.append(f"ChatGPT未通过({chatgpt_correct}/{attempts})")
            
            if zhipu_passed:
                verdict_parts.append(f"智谱GLM通过({zhipu_correct}/{attempts})")
            else:
                verdict_parts.append(f"智谱GLM未通过({zhipu_correct}/{attempts})")
            
            # 生成详细评价（异步，不阻塞主流程）
            chatgpt_evaluation = None
            zhipu_evaluation = None
            try:
                # 并发生成两个模型的评价
                eval_tasks = []
                if chatgpt_result.get("success"):
                    eval_tasks.append(self._generate_evaluation("chatgpt", problem, answer, chatgpt_correct, attempts, chatgpt_passed))
                else:
                    eval_tasks.append(None)
                
                if zhipu_result.get("success"):
                    eval_tasks.append(self._generate_evaluation("zhipu", problem, answer, zhipu_correct, attempts, zhipu_passed))
                else:
                    eval_tasks.append(None)
                
                eval_results = await asyncio.gather(*[t for t in eval_tasks if t is not None], return_exceptions=True)
                
                eval_idx = 0
                if chatgpt_result.get("success"):
                    if eval_idx < len(eval_results) and not isinstance(eval_results[eval_idx], Exception):
                        chatgpt_evaluation = eval_results[eval_idx]
                    eval_idx += 1
                
                if zhipu_result.get("success"):
                    if eval_idx < len(eval_results) and not isinstance(eval_results[eval_idx], Exception):
                        zhipu_evaluation = eval_results[eval_idx]
            except Exception as e:
                # 评价生成失败不影响主流程
                print(f"生成评价失败: {str(e)}")
            
            # 更新结果中的评价
            if chatgpt_evaluation:
                chatgpt_result["evaluation"] = chatgpt_evaluation
            if zhipu_evaluation:
                zhipu_result["evaluation"] = zhipu_evaluation
            
            return {
                "success": True,
                "is_passed": is_passed,
                "mode": "dual",
                "attempts": attempts,
                "max_correct_threshold": self.dual_model_max_correct,
                "chatgpt_result": chatgpt_result,
                "zhipu_result": zhipu_result,
                "correct_count": max(chatgpt_correct, zhipu_correct),  # 兼容旧接口
                "verdict": "难度合格" if is_passed else "难度不合格",
                "summary": " | ".join(verdict_parts),
                "ai_model": "ChatGPT + 智谱GLM"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"双模型验证失败: {str(e)}"
            }
    
    # ==================== 豆包验证（保留原有逻辑） ====================
    
    async def validate_with_doubao(
        self,
        problem: str,
        answer: str,
        explanation: Optional[str] = None,
        attempts: int = None
    ) -> Dict[str, Any]:
        """
        豆包验证（Doubao Seed Thinking）
        
        8次对抗验证，正确次数<=4才算通过
        
        Args:
            problem: 题目内容
            answer: 标准答案
            explanation: 解析（可选）
            attempts: 尝试次数（默认8次）
            
        Returns:
            Dict: {
                "success": bool,
                "is_passed": bool,
                "attempts": int,
                "correct_count": int,
                "correct_rate": float,
                "attempts_details": List[Dict],
                "verdict": str,
                "ai_model": str,
            }
        """
        if attempts is None:
            attempts = self.doubao_attempts
        
        try:
            prompt = self._build_prompt(problem)
            
            # 并发进行多次验证
            tasks = [
                self._doubao_attempt(prompt, answer)
                for _ in range(attempts)
            ]
            
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
                    valid_attempts.append(result)
                    if result.get("is_correct", False):
                        correct_count += 1
            
            # 判断是否通过验证（正确次数 <= 4）
            is_passed = correct_count <= self.doubao_max_correct
            correct_rate = correct_count / attempts if attempts > 0 else 0
            
            # 生成详细评价（异步，不阻塞主流程）
            doubao_evaluation = None
            try:
                doubao_evaluation = await self._generate_evaluation("doubao", problem, answer, correct_count, attempts, is_passed)
            except Exception as e:
                print(f"生成豆包评价失败: {str(e)}")
            
            result = {
                "success": True,
                "is_passed": is_passed,
                "mode": "doubao",
                "attempts": attempts,
                "correct_count": correct_count,
                "correct_rate": correct_rate,
                "attempts_details": valid_attempts,
                "verdict": "难度合格" if is_passed else "题目太简单",
                "ai_model": self.doubao_model
            }
            
            if doubao_evaluation:
                result["evaluation"] = doubao_evaluation
            
            return result
        
        except Exception as e:
            return {
                "success": False,
                "error": f"豆包验证失败: {str(e)}"
            }
    
    # ==================== 内部方法 ====================
    
    def _build_prompt(self, problem: str) -> str:
        """构建验证提示词"""
        return f"""请直接给出以下数学题目的最终答案，无需解题过程，将答案放在\\boxed{{}}中。

题目：
{problem}

答案："""
    
    async def _validate_with_model(
        self,
        model_type: str,
        prompt: str,
        standard_answer: str,
        attempts: int
    ) -> Dict[str, Any]:
        """使用指定模型进行多次验证"""
        try:
            tasks = [
                self._single_attempt(model_type, prompt, standard_answer)
                for _ in range(attempts)
            ]
            
            attempt_results = await asyncio.gather(*tasks, return_exceptions=True)
            
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
                    valid_attempts.append(result)
                    if result.get("is_correct", False):
                        correct_count += 1
            
            is_passed = correct_count <= self.dual_model_max_correct
            correct_rate = correct_count / attempts if attempts > 0 else 0
            
            return {
                "success": True,
                "model": model_type,
                "is_passed": is_passed,
                "attempts": attempts,
                "correct_count": correct_count,
                "correct_rate": correct_rate,
                "threshold": self.dual_model_max_correct,
                "attempts_details": valid_attempts
            }
        
        except Exception as e:
            return {
                "success": False,
                "model": model_type,
                "error": str(e),
                "is_passed": False,
                "correct_count": 0
            }
    
    async def _single_attempt(
        self,
        model_type: str,
        prompt: str,
        standard_answer: str
    ) -> Dict[str, Any]:
        """单次验证尝试"""
        if model_type == "chatgpt":
            return await self._chatgpt_attempt(prompt, standard_answer)
        elif model_type == "zhipu":
            return await self._zhipu_attempt(prompt, standard_answer)
        else:
            return await self._doubao_attempt(prompt, standard_answer)
    
    async def _chatgpt_attempt(
        self,
        prompt: str,
        standard_answer: str
    ) -> Dict[str, Any]:
        """ChatGPT 单次验证"""
        try:
            # gpt-5.2-pro 是推理模型，不限制响应时间
            async with httpx.AsyncClient(timeout=None, verify=False) as client:
                # 根据 API 端点构建不同的请求体
                if "responses" in self.chatgpt_base_url:
                    # Responses API 格式：使用 "input" 而不是 "messages"
                    # 合并 system 和 user 消息为一个 input
                    full_prompt = f"You are a math expert. Give direct answer only. Put your final answer within \\boxed{{}}.\n\n{prompt}"
                    request_body = {
                        "model": self.chatgpt_model,  # 使用配置中的模型名：gpt-5.2-pro
                        "input": full_prompt,
                        "reasoning": {
                            "effort": "medium"  # gpt-5.2-pro 支持: "medium", "high", "xhigh" (不支持 "none")
                        }
                    }
                else:
                    # Chat Completions API 格式
                    request_body = {
                        "model": self.chatgpt_model,
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
                        "temperature": 0.7,
                        "max_tokens": 2048
                    }
                
                response = await client.post(
                    self.chatgpt_base_url,
                    headers={
                        "Authorization": f"Bearer {self.chatgpt_api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://mathtasks.app",  # OpenRouter 要求
                        "X-Title": "MathTasks Validation"  # OpenRouter 要求
                    },
                    json=request_body
                )
                
                # 如果返回错误，打印详细信息
                if response.status_code != 200:
                    error_detail = response.text
                    print(f"❌ ChatGPT API 错误 (状态码: {response.status_code}):")
                    print(f"   请求 URL: {self.chatgpt_base_url}")
                    print(f"   模型: {self.chatgpt_model}")
                    print(f"   请求体: {request_body}")
                    print(f"   错误详情: {error_detail}")
                
                response.raise_for_status()
                data = response.json()
                
                # Responses API 和 Chat Completions API 的响应格式不同
                if "responses" in self.chatgpt_base_url:
                    # Responses API 格式：output 是数组，内容在 output[0].content[0].text
                    if "output" in data and isinstance(data["output"], list) and len(data["output"]) > 0:
                        output_item = data["output"][0]
                        if "content" in output_item and isinstance(output_item["content"], list) and len(output_item["content"]) > 0:
                            content_item = output_item["content"][0]
                            if "text" in content_item:
                                content = content_item["text"]
                            else:
                                content = str(content_item)
                        else:
                            content = str(output_item)
                    elif "output" in data:
                        content = str(data["output"])
                    else:
                        content = str(data)
                else:
                    # Chat Completions API 格式
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"]["content"]
                    else:
                        content = str(data)
                
                # 使用 GPT-5.2-pro 进行答案对比
                is_correct = await self._check_answer_with_ai(content, standard_answer)
                
                return {
                    "success": True,
                    "model": "chatgpt",
                    "ai_answer": content[:500],
                    "is_correct": is_correct
                }
        
        except Exception as e:
            raise Exception(f"ChatGPT验证失败: {str(e)}")
    
    async def _zhipu_attempt(
        self,
        prompt: str,
        standard_answer: str
    ) -> Dict[str, Any]:
        """智谱GLM 单次验证"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.zhipu_base_url,
                    headers={
                        "Authorization": f"Bearer {self.zhipu_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.zhipu_model,
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
                        "temperature": 0.7,
                        "max_tokens": 2048
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                content = data["choices"][0]["message"]["content"]
                # 使用 GPT-5.2-pro 进行答案对比
                is_correct = await self._check_answer_with_ai(content, standard_answer)
                
                return {
                    "success": True,
                    "model": "zhipu",
                    "ai_answer": content[:500],
                    "is_correct": is_correct
                }
        
        except Exception as e:
            raise Exception(f"智谱GLM验证失败: {str(e)}")
    
    async def _doubao_attempt(
        self,
        prompt: str,
        standard_answer: str
    ) -> Dict[str, Any]:
        """豆包 单次验证（流式响应）"""
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                async with client.stream(
                    "POST",
                    self.doubao_base_url,
                    headers={
                        "Authorization": f"Bearer {self.doubao_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.doubao_model,
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
                        "stream": True,
                        "temperature": 0.6,
                    }
                ) as response:
                    response.raise_for_status()
                    
                    full_content = ""
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or line == "data: [DONE]":
                            continue
                        
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    
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
                    
                    # 使用 GPT-5.2-pro 进行答案对比
                    is_correct = await self._check_answer_with_ai(full_content, standard_answer)
                    
                    return {
                        "success": True,
                        "model": "doubao",
                        "ai_answer": full_content[:500],
                        "is_correct": is_correct
                    }
        
        except Exception as e:
            raise Exception(f"豆包验证失败: {str(e)}")
    
    async def _generate_evaluation(
        self,
        model_type: str,
        problem: str,
        answer: str,
        correct_count: int,
        total_attempts: int,
        is_passed: bool
    ) -> Optional[str]:
        """
        生成题目的详细评价
        
        Args:
            model_type: 模型类型 ("chatgpt"、"zhipu" 或 "doubao")
            problem: 题目内容
            answer: 标准答案
            correct_count: 正确次数
            total_attempts: 总尝试次数
            is_passed: 是否通过
            
        Returns:
            str: 详细评价文本
        """
        try:
            if model_type == "chatgpt":
                api_key = self.chatgpt_api_key
                model = self.chatgpt_model
                base_url = self.chatgpt_base_url
            elif model_type == "zhipu":
                api_key = self.zhipu_api_key
                model = self.zhipu_model
                base_url = self.zhipu_base_url
            elif model_type == "doubao":
                # 豆包暂时不生成评价（流式API较复杂）
                return None
            else:
                return None
            
            evaluation_prompt = f"""请对以下数学题目进行详细评价，包括：
1. 题目的难度分析
2. 题目的考查点
3. 题目的优缺点
4. 是否适合作为竞赛题目

题目：
{problem}

标准答案：
{answer}

验证结果：在 {total_attempts} 次尝试中，AI模型答对了 {correct_count} 次，{'通过' if is_passed else '未通过'}难度验证。

请给出详细的评价（200-300字），客观分析题目的特点。"""
            
            # 使用香港代理时跳过 SSL 验证
            async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                response = await client.post(
                    base_url,
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "你是一位数学竞赛题目评价专家，擅长分析题目的难度、考查点和质量。"
                            },
                            {
                                "role": "user",
                                "content": evaluation_prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                evaluation = data["choices"][0]["message"]["content"].strip()
                return evaluation
        
        except Exception as e:
            print(f"生成{model_type}评价失败: {str(e)}")
            return None
    
    async def _check_answer_with_ai(self, ai_answer: str, standard_answer: str) -> bool:
        """
        使用 GPT-5.2-pro 判断答案是否正确
        
        对于复杂的数学答案（如表达式、集合、多解等），正则无法准确判断，
        因此使用 GPT-5.2-pro 进行智能对比。
        
        Args:
            ai_answer: AI模型给出的答案
            standard_answer: 用户输入的标准答案
            
        Returns:
            bool: 答案是否等价
        """
        # 先用简单规则快速判断（提高效率）
        quick_result = self._quick_check_answer(ai_answer, standard_answer)
        if quick_result is not None:
            return quick_result
        
        # 复杂情况使用 GPT-5.2-pro 判断
        try:
            comparison_prompt = f"""请判断以下两个数学答案是否等价。

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

            # gpt-5.2-pro 是推理模型，不限制响应时间
            async with httpx.AsyncClient(timeout=None, verify=False) as client:
                # 使用 Responses API（gpt-5.2-pro）
                if "responses" in self.chatgpt_base_url:
                    request_body = {
                        "model": self.chatgpt_model,
                        "input": comparison_prompt,
                        "reasoning": {
                            "effort": "medium"
                        }
                    }
                else:
                    request_body = {
                        "model": self.chatgpt_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a math answer comparison expert. Only answer YES or NO."
                            },
                            {
                                "role": "user",
                                "content": comparison_prompt
                            }
                        ],
                        "temperature": 0,
                        "max_tokens": 10
                    }
                
                response = await client.post(
                    self.chatgpt_base_url,
                    headers={
                        "Authorization": f"Bearer {self.chatgpt_api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://mathtasks.app",  # OpenRouter 要求
                        "X-Title": "MathTasks Answer Comparison"  # OpenRouter 要求
                    },
                    json=request_body
                )
                
                # 如果请求失败，回退到 OpenRouter gpt-4o（通过香港代理）
                if response.status_code == 400:
                    fallback_url = "https://www.stem-align.com/v2/openrouter/api/v1/chat/completions"
                    request_body = {
                        "model": "openai/gpt-4o",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a math answer comparison expert. Only answer YES or NO."
                            },
                            {
                                "role": "user",
                                "content": comparison_prompt
                            }
                        ],
                        "temperature": 0,
                        "max_tokens": 10
                    }
                    response = await client.post(
                        fallback_url,
                        headers={
                            "Authorization": f"Bearer {self.chatgpt_api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://mathtasks.app",
                            "X-Title": "MathTasks Answer Comparison"
                        },
                        json=request_body
                    )
                
                response.raise_for_status()
                data = response.json()
                
                # 解析响应
                content = ""
                if "output" in data and isinstance(data["output"], list) and len(data["output"]) > 0:
                    # Responses API 格式
                    first_output = data["output"][0]
                    if "content" in first_output and isinstance(first_output["content"], list) and len(first_output["content"]) > 0:
                        content = first_output["content"][0].get("text", "")
                    elif "text" in first_output:
                        content = first_output["text"]
                elif "choices" in data and len(data["choices"]) > 0:
                    # Chat Completions 格式
                    content = data["choices"][0]["message"]["content"]
                elif "response" in data:
                    content = str(data["response"])
                else:
                    content = str(data)
                
                # 判断结果
                content_upper = content.strip().upper()
                if "YES" in content_upper:
                    return True
                elif "NO" in content_upper:
                    return False
                else:
                    # 无法确定，使用保守策略（回退到快速检查的严格模式）
                    print(f"GPT答案对比返回不明确结果: {content}")
                    return self._strict_check_answer(ai_answer, standard_answer)
        
        except Exception as e:
            print(f"GPT答案对比失败，回退到正则检查: {str(e)}")
            # 回退到传统方法
            return self._strict_check_answer(ai_answer, standard_answer)
    
    def _quick_check_answer(self, ai_answer: str, standard_answer: str) -> Optional[bool]:
        """
        快速答案检查（简单情况，无需调用AI）
        
        Returns:
            bool: 如果能快速判断则返回结果
            None: 如果需要AI判断则返回None
        """
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
        
        # 直接字符串匹配（完全相同）
        if extracted_model and extracted_model == clean_truth:
            return True
        
        # 如果两个答案都是简单数字，直接比较
        try:
            num_model = float(extracted_model.replace(',', ''))
            num_truth = float(clean_truth.replace(',', ''))
            return abs(num_model - num_truth) < 1e-9
        except (ValueError, AttributeError):
            pass
        
        # 如果两个答案都很短且完全不同，可能需要AI判断
        if len(extracted_model) < 50 and len(clean_truth) < 50:
            # 简单情况，如果完全不相关则返回False
            if not extracted_model or not clean_truth:
                return False
            # 需要AI进一步判断
            return None
        
        # 复杂情况，需要AI判断
        return None
    
    def _strict_check_answer(self, ai_answer: str, standard_answer: str) -> bool:
        """严格的答案检查（作为AI检查的回退方案）"""
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
        
        # 方法1: 直接字符串匹配
        if extracted_model and extracted_model == clean_truth:
            return True
        
        # 方法2: 检查标准答案是否在AI答案的末尾
        if clean_truth and clean_truth in ai_answer.replace(' ', '')[-50:]:
            return True
        
        # 方法3: 集合匹配（多解情况）
        if ',' in extracted_model and ',' in clean_truth:
            model_elements = re.findall(r'\([^)]+\)', extracted_model)
            truth_elements = re.findall(r'\([^)]+\)', clean_truth)
            
            if len(model_elements) > 1 and len(truth_elements) > 1:
                model_set = set(e.replace(' ', '') for e in model_elements)
                truth_set = set(e.replace(' ', '') for e in truth_elements)
                if model_set == truth_set:
                    return True
            
            if not model_elements or not truth_elements:
                model_items = [item.strip() for item in extracted_model.replace('(', '').replace(')', '').replace('{', '').replace('}', '').split(',')]
                truth_items = [item.strip() for item in clean_truth.replace('(', '').replace(')', '').replace('{', '').replace('}', '').split(',')]
                
                if len(model_items) > 1 and len(truth_items) > 1 and len(model_items) == len(truth_items):
                    if set(model_items) == set(truth_items):
                        return True
        
        return False


# 全局服务实例
difficulty_check_service = DifficultyCheckService()
