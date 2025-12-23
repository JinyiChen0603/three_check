"""
深度变形服务模块
基于 DeepSeek Math-V2 实现题目深度变形功能
支持自动续写和无限制运行
"""

import json
import requests
import time
import urllib3
from typing import Dict, Any, Optional

from app.config import settings

# 临时禁用 SSL 验证警告（代理服务器证书问题）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DeepTransformerService:
    """深度变形服务 - 无时间和token限制"""
    
    def __init__(self):
        # 从配置文件获取API配置
        # self.api_key = settings.GEMINI_API_KEY
        # self.model = "gemini-2.0-flash-exp"
        # 使用香港代理服务器中转（www.stem-align.com/v2/）
        #self.api_url = f"https://www.stem-align.com/v2/gemini/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        # 使用 Google 官方 Gemini API
        #self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        # 使用 OpenRouter API
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = "google/gemini-3-pro-preview"
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def chat_stream_with_auto_continue(
        self,
        messages,
        max_rounds=20,  # 增加到20轮以支持更长内容
        sleep_between_rounds=0.5,
        max_tokens=8000,  # 增加初始token数
        temperature=0.3
    ):
        """
        流式输出 + token 截断自动续写（OpenRouter API - OpenAI兼容格式）
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

            # OpenRouter 使用 OpenAI 兼容格式，直接传递 messages
            payload = {
                "model": self.model,
                "messages": current_messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://mathtasks.app",
                    "X-Title": "MathTasks"
                },
                json=payload,
                timeout=None  # 无超时限制 - 允许长时间运行
            )

            response.raise_for_status()
            data = response.json()

            round_text = ""
            finish_reason = None

            # OpenAI 兼容格式的响应解析
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    round_text = choice["message"]["content"] or ""
                    full_text += round_text
                
                if "finish_reason" in choice:
                    finish_reason = choice["finish_reason"]

            # ✅ 正常结束，不需要续写
            if finish_reason != "length":
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
        非流式输出 + token 截断自动续写（OpenRouter API - OpenAI兼容格式）
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

            # OpenRouter 使用 OpenAI 兼容格式
            payload = {
                "model": self.model,
                "messages": current_messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://mathtasks.app",
                    "X-Title": "MathTasks"
                },
                json=payload,
                timeout=None  # 无超时限制
            )

            response.raise_for_status()
            data = response.json()

            content = ""
            finish_reason = None

            # OpenAI 兼容格式的响应解析
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"] or ""
                
                if "finish_reason" in choice:
                    finish_reason = choice["finish_reason"]

            if content:
                full_text += content

            # ✅ 正常结束
            if finish_reason != "length":
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
        
        # 4. 解析文本格式的返回内容
        import re
        
        def extract_section(text: str, section_name: str) -> str:
            """从文本中提取指定分隔符之间的内容"""
            # 匹配 【section_name】 后面的内容，直到下一个 【 或文本结束
            pattern = rf'【{section_name}】\s*([\s\S]*?)(?=【|$)'
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
            return ""
        
        variant_content = extract_section(result_text, "变体题目")
        variant_explanation = extract_section(result_text, "变体解析")
        variant_answer = extract_section(result_text, "变体答案")
        
        # 5. 验证必需字段
        if not variant_content:
            raise ValueError(f"AI 返回内容缺少【变体题目】部分\n原始内容: {result_text[:500]}...")
        if not variant_explanation:
            raise ValueError(f"AI 返回内容缺少【变体解析】部分\n原始内容: {result_text[:500]}...")
        if not variant_answer:
            raise ValueError(f"AI 返回内容缺少【变体答案】部分\n原始内容: {result_text[:500]}...")
        
        return {
            "variant_content": variant_content,
            "variant_explanation": variant_explanation,
            "variant_answer": variant_answer
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
