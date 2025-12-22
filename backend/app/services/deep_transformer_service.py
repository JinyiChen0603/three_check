"""
深度变形服务模块
基于 DeepSeek Math-V2 实现题目深度变形功能
支持自动续写和无限制运行
"""

import json
import requests
import time
from typing import Dict, Any, Optional

from app.config import settings


class DeepTransformerService:
    """深度变形服务 - 无时间和token限制"""
    
    def __init__(self):
        # 从配置文件获取API配置
        self.api_key = settings.GEMINI_API_KEY
        self.model = "gemini-2.0-flash-exp"
        # 使用香港代理服务器中转（www.stem-align.com/v2/）
        self.api_url = f"https://www.stem-align.com/v2/gemini/v1beta/models/{self.model}:generateContent?key={self.api_key}"
    
    def chat_stream_with_auto_continue(
        self,
        messages,
        max_rounds=20,  # 增加到20轮以支持更长内容
        sleep_between_rounds=0.5,
        max_tokens=8000,  # 增加初始token数
        temperature=0.3
    ):
        """
        流式输出 + token 截断自动续写（Gemini API）
        返回完整文本
        
        无超时限制版本 - 允许AI长时间运行
        """

        full_text = ""
        current_messages = list(messages)

        for round_idx in range(max_rounds):
            print(f"\n--- 深度变形 Round {round_idx + 1} ---\n")

            if round_idx == 1:
                max_tokens = int(max_tokens * 1.5)  # 续写时增加token数
                temperature = min(temperature + 0.2, 2.0)

            # 转换消息格式为 Gemini 格式
            gemini_contents = []
            system_instruction = None
            
            for msg in current_messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                else:
                    role = "user" if msg["role"] == "user" else "model"
                    gemini_contents.append({
                        "role": role,
                        "parts": [{"text": msg["content"]}]
                    })

            payload = {
                "contents": gemini_contents,
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": temperature
                }
            }
            
            if system_instruction:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_instruction}]
                }

            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=None,  # 无超时限制 - 允许长时间运行
            )

            response.raise_for_status()
            data = response.json()

            round_text = ""
            finish_reason = None

            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        if "text" in part:
                            round_text += part["text"]
                            full_text += part["text"]
                
                if "finishReason" in candidate:
                    finish_reason = candidate["finishReason"]

            # ✅ 正常结束，不需要续写
            if finish_reason not in ["MAX_TOKENS"] or finish_reason == "STOP":
                break

            # ⚠️ token 用尽，需要续写
            current_messages.append({
                "role": "assistant",
                "content": round_text
            })
            current_messages.append({
                "role": "user",
                "content": "请从上文中断处继续，不要重复已生成内容。"
            })

            time.sleep(sleep_between_rounds)

        return full_text

    def chat_with_auto_continue_non_stream(
        self,
        messages,
        max_rounds=20,  # 增加到20轮
        sleep_between_rounds=0.5,
        max_tokens=8000,  # 增加初始token数
        temperature=0.7
    ):
        """
        非流式输出 + token 截断自动续写（Gemini API）
        返回完整文本
        
        无超时限制版本 - 允许AI长时间运行
        """

        full_text = ""
        current_messages = list(messages)

        for round_idx in range(max_rounds):
            print(f"\n--- 深度变形 Round {round_idx + 1} (非流式) ---\n")

            if round_idx == 1:
                max_tokens = int(max_tokens * 1.5)
                temperature = min(temperature + 0.2, 2.0)

            # 转换消息格式为 Gemini 格式
            gemini_contents = []
            system_instruction = None
            
            for msg in current_messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                else:
                    role = "user" if msg["role"] == "user" else "model"
                    gemini_contents.append({
                        "role": role,
                        "parts": [{"text": msg["content"]}]
                    })

            payload = {
                "contents": gemini_contents,
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": temperature
                }
            }
            
            if system_instruction:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_instruction}]
                }

            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Connection": "close"
                },
                json=payload,
                timeout=None  # 无超时限制
            )

            response.raise_for_status()
            data = response.json()

            content = ""
            finish_reason = None

            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        if "text" in part:
                            content += part["text"]
                
                if "finishReason" in candidate:
                    finish_reason = candidate["finishReason"]

            if content:
                full_text += content

            # ✅ 正常结束
            if finish_reason not in ["MAX_TOKENS"] or finish_reason == "STOP":
                break

            # ⚠️ token 用尽，准备续写
            current_messages.append({
                "role": "assistant",
                "content": content
            })
            current_messages.append({
                "role": "user",
                "content": "请从上文中断处继续，不要重复已生成内容。"
            })

            time.sleep(sleep_between_rounds)

        return full_text

    @staticmethod
    def extract_last_brace_block(text: str) -> str:
        """
        从字符串末尾开始，提取最近一对完整的大括号内容（包含大括号）。
        如果不存在完整的大括号对，则返回空字符串。
        """
        if not text:
            return ""

        stack = 0
        end = -1

        # 从后往前扫描
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

    def generate_modified_problem(
        self,
        original_problem: str,
        original_answer: str,
        modification_requirement: str,
        max_tokens=8000,  # 增加默认token数
        temperature=0.7,
        use_stream=True
    ) -> str:
        """
        根据原题目、原答案和修改要求，生成新的题目或内容
        
        Args:
            original_problem: 原题目
            original_answer: 原答案
            modification_requirement: 修改要求
            max_tokens: 最大token数（无硬性限制，会自动续写）
            temperature: 温度参数
            use_stream: 是否使用流式传输
            
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

        system_prompt = """你是数学出题专家。根据用户的修改要求生成一道新题目和答案。

必须按此格式返回（不要包含思考过程，不需要处理换行操作）：
{
    "new_question": "优化后的题目",
    "new_answer": "完整解答，含步骤"
}

文字描述用文本格式，数学公式满足：行内公式使用 $...$, 独立公式使用 $$...$$

禁止：不要在JSON中出现"Let's think"、"Actually"、"Wait"等思考词汇。直接输出结果。"""

        user_message = f"""原题目：{original_problem}

原答案：{original_answer}

修改要求：{modification_requirement}

请直接返回JSON格式的新题目和新答案。"""

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ]

        print(json.dumps(messages, indent=4, ensure_ascii=False))

        if use_stream:
            result_text = self.chat_stream_with_auto_continue(
                messages, 
                max_tokens=max_tokens, 
                temperature=temperature
            )
        else:
            result_text = self.chat_with_auto_continue_non_stream(
                messages, 
                max_tokens=max_tokens, 
                temperature=temperature
            )

        # 提取JSON块
        filtered_text = self.extract_last_brace_block(result_text)

        return filtered_text

    def generate_problem_variant_with_explanation(
        self,
        original_content: str,
        original_explanation: str,
        original_answer: str,
        modification_requirement: str = "",
        max_tokens: int = 10000,  # 增加默认token数
        temperature: float = 0.7,
        use_stream: bool = True
    ) -> Dict[str, Any]:
        """
        生成题目变体（包含题目、解析、答案）
        
        这是深度变形的主要接口 - 无时间和token限制版本
        
        根据原题的完整信息和用户的修改要求，生成一道新的变体题目及其完整解答。
        
        Args:
            original_content: 原题目
            original_explanation: 原解析
            original_answer: 原答案
            modification_requirement: 修改要求（用户指定如何修改，可为空）
            max_tokens: 最大 token 数（会自动续写，无硬性限制）
            temperature: 温度参数
            use_stream: 流式传输开关（默认 True）
            
        Returns:
            dict: {
                "variant_content": "变体题目",
                "variant_explanation": "变体解析", 
                "variant_answer": "变体答案"
            }
        """
        
        # 1. 参数校验
        if not original_content.strip():
            raise ValueError("original_content 不能为空")
        if not original_explanation.strip():
            raise ValueError("original_explanation 不能为空")
        if not original_answer.strip():
            raise ValueError("original_answer 不能为空")
        
        # 2. 构造 prompt
        system_prompt = """你是数学出题专家。根据原题的题目、解析和答案以及修改要求，生成一道新的变体题目。

必须按此 JSON 格式返回（不要包含思考过程）：
{
    "variant_content": "变体题目内容",
    "variant_explanation": "详细的解题步骤和分析",
    "variant_answer": "最终答案"
}

文字描述用文本格式，数学公式满足：行内公式使用 $...$，独立公式使用 $$...$$

禁止：不要在 JSON 中出现 "Let's think"、"Actually"、"Wait" 等思考词汇。直接输出结果。"""

        # 根据修改要求是否为空，构造不同的 user_message
        if modification_requirement and modification_requirement.strip():
            # 用户提供了具体的修改要求
            user_message = f"""原题目：{original_content}

原解析：{original_explanation}

原答案：{original_answer}

修改要求：{modification_requirement}

请根据修改要求生成一道变体题目，包含完整的题目、解析和答案。"""
        else:
            # 使用默认修改要求
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
        
        # 3. 调用 AI 服务
        print(json.dumps(messages, indent=4, ensure_ascii=False))
        
        if use_stream:
            result_text = self.chat_stream_with_auto_continue(
                messages, 
                max_tokens=max_tokens, 
                temperature=temperature
            )
        else:
            result_text = self.chat_with_auto_continue_non_stream(
                messages, 
                max_tokens=max_tokens, 
                temperature=temperature
            )
        
        # 4. 提取并解析 JSON
        json_text = self.extract_last_brace_block(result_text)
        
        if not json_text:
            raise ValueError("AI 返回内容中未找到有效的 JSON 格式")
        
        try:
            result_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失败: {str(e)}\n原始内容: {json_text}")
        
        # 5. 验证和返回
        required_fields = ["variant_content", "variant_explanation", "variant_answer"]
        for field in required_fields:
            if field not in result_data:
                raise ValueError(f"AI 返回的 JSON 缺少必需字段: {field}")
        
        return {
            "variant_content": result_data["variant_content"],
            "variant_explanation": result_data["variant_explanation"],
            "variant_answer": result_data["variant_answer"]
        }

    def generate_multiple_variants(
        self,
        original_content: str,
        original_explanation: str,
        original_answer: str,
        modification_requirement: str = "",
        count: int = 1,
        max_tokens: int = 10000,
        temperature: float = 0.7,
        use_stream: bool = True
    ) -> Dict[str, Any]:
        """
        批量生成多个变体题目
        
        Args:
            original_content: 原题目
            original_explanation: 原解析
            original_answer: 原答案
            modification_requirement: 修改要求
            count: 生成数量
            max_tokens: 最大token数
            temperature: 温度参数
            use_stream: 是否使用流式传输
            
        Returns:
            dict: {
                "success": bool,
                "count": int,
                "variants": List[Dict],
                "error": str (if failed)
            }
        """
        try:
            if count > 50:  # 提高批量限制
                return {
                    "success": False,
                    "error": "单次最多生成50个变体"
                }
            
            variants = []
            for i in range(count):
                print(f"\n=== 生成第 {i + 1}/{count} 个变体 ===\n")
                
                try:
                    result = self.generate_problem_variant_with_explanation(
                        original_content=original_content,
                        original_explanation=original_explanation,
                        original_answer=original_answer,
                        modification_requirement=modification_requirement,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        use_stream=use_stream
                    )
                    
                    variants.append({
                        "index": i + 1,
                        "success": True,
                        **result
                    })
                    
                except Exception as e:
                    # 如果生成失败，记录错误但继续
                    variants.append({
                        "index": i + 1,
                        "success": False,
                        "error": str(e)
                    })
                
                # 批量生成时在每个变体之间稍作停顿
                if i < count - 1:
                    time.sleep(1)
            
            return {
                "success": True,
                "count": len([v for v in variants if v.get("success", False)]),
                "total": count,
                "variants": variants
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"批量生成失败: {str(e)}"
            }


# 全局服务实例
deep_transformer_service = DeepTransformerService()
