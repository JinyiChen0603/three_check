"""
OCR 服务模块
使用 GPT-4o Vision 识别图片中的数学题目和答案
"""

import base64
from typing import Optional, Dict, Any
from pathlib import Path
import httpx

from app.config import settings


class OCRService:
    """OCR 识别服务"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_OCR_MODEL
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    async def recognize_image(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        extract_answer: bool = True
    ) -> Dict[str, Any]:
        """
        识别图片中的数学题目
        
        Args:
            image_path: 本地图片路径
            image_url: 图片URL
            image_base64: Base64编码的图片
            extract_answer: 是否同时提取答案
            
        Returns:
            Dict: {
                "success": bool,
                "problem": str,  # 题目内容
                "answer": str,   # 答案（如果extract_answer=True）
                "explanation": str,  # 解析（如果有）
                "raw_text": str,  # 原始识别文本
                "error": str  # 错误信息（如果失败）
            }
        """
        try:
            # 准备图片数据
            image_data = None
            if image_path:
                # 从本地文件读取
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                    image_data = base64.b64encode(image_bytes).decode('utf-8')
            elif image_base64:
                image_data = image_base64
            elif image_url:
                # 直接使用URL
                pass
            else:
                return {
                    "success": False,
                    "error": "必须提供image_path、image_url或image_base64之一"
                }
            
            # 构建prompt
            if extract_answer:
                prompt = """请识别这张图片中的数学题目，并按照以下格式返回：

【题目】
（题目的完整内容，包括题设、条件、问题等）

【答案】
（标准答案）

【解析】
（如果图片中包含解析，请提取；否则留空）

注意：
1. 保持数学公式的准确性
2. 如果有多个小题，请分别列出
3. 答案要明确、具体
4. 使用LaTeX格式表示数学公式（用$...$包裹）"""
            else:
                prompt = """请识别这张图片中的数学题目内容。

注意：
1. 保持数学公式的准确性
2. 如果有多个小题，请分别列出
3. 使用LaTeX格式表示数学公式（用$...$包裹）"""
            
            # 构建请求
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # 添加图片
            if image_url:
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
                })
            else:
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                })
            
            # 调用OpenAI API
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": 2000,
                        "temperature": 0.2,  # 低温度以提高准确性
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 解析返回结果
                raw_text = result["choices"][0]["message"]["content"]
                
                # 简单解析（实际应用中可能需要更复杂的解析逻辑）
                parsed_result = self._parse_ocr_result(raw_text, extract_answer)
                
                return {
                    "success": True,
                    "raw_text": raw_text,
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
                "error": f"OCR识别失败: {str(e)}"
            }
    
    def _parse_ocr_result(self, raw_text: str, has_answer: bool) -> Dict[str, str]:
        """
        解析OCR识别结果
        
        Args:
            raw_text: 原始识别文本
            has_answer: 是否包含答案
            
        Returns:
            Dict: 包含problem, answer, explanation的字典
        """
        result = {
            "problem": "",
            "answer": "",
            "explanation": ""
        }
        
        # 简单的解析逻辑（使用标记分割）
        sections = raw_text.split("【")
        
        for section in sections:
            if section.startswith("题目】"):
                content = section.replace("题目】", "").strip()
                # 提取到下一个【之前的内容
                if "【" in content:
                    content = content.split("【")[0].strip()
                result["problem"] = content
            
            elif section.startswith("答案】"):
                content = section.replace("答案】", "").strip()
                if "【" in content:
                    content = content.split("【")[0].strip()
                result["answer"] = content
            
            elif section.startswith("解析】"):
                content = section.replace("解析】", "").strip()
                if "【" in content:
                    content = content.split("【")[0].strip()
                result["explanation"] = content
        
        # 如果没有成功解析，将整个文本作为题目
        if not result["problem"]:
            result["problem"] = raw_text.strip()
        
        return result


# 全局OCR服务实例
ocr_service = OCRService()

