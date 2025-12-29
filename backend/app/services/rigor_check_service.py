"""
严谨性检测服务模块
使用 GPT-5.2 判断数学竞赛题目的严谨性（无需联网搜索）
"""

import traceback
from typing import Dict, Any, Optional

from app.services.llm import gpt52_with_reasoning, LLMClient


class RigorCheckService:
    """
    数学严谨性检测服务 - 使用 GPT-5.2
    
    专门针对高中/大学数学竞赛题目，检查：
    - 题目表述是否清晰、无歧义
    - 数学符号和术语使用是否规范
    - 题目条件是否充分且无冗余
    - 答案是否正确且完整
    - 解题逻辑是否严密
    """
    
    def __init__(self, client: LLMClient = None):
        """
        初始化严谨性检测服务
        
        Args:
            client: LLMClient 实例，默认使用 gpt52_with_reasoning
        """
        self.client = client or gpt52_with_reasoning
        self.model_name = "gpt-5.2"
    
    async def check_rigor(
        self,
        problem: str,
        answer: str,
        explanation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        检查数学竞赛题目的严谨性
        
        Args:
            problem: 题目内容
            answer: 标准答案
            explanation: 解析（可选）
            
        Returns:
            Dict: {
                "success": bool,
                "is_rigorous": bool,
                "details": str,
                "verdict": str,
                "ai_model": str,
                "issues": List[str],  # 发现的问题列表
                "error": str  # 错误信息（如果失败）
            }
        """
        try:
            # 构建系统提示词（英文）
            system_prompt = """You are a senior math competition problem reviewer and editor, experienced with high school competitions (AMC, AIME, IMO) and university competitions (Putnam, Yau Mathematical Sciences Competition).

Your task is to review problems for mathematical rigor, ensuring they are suitable for official competitions or model training datasets.

Review Criteria:
1. [Condition Completeness] Are the given conditions sufficient? Do they uniquely determine the answer? Are there missing implicit conditions?
2. [Condition Necessity] Are there redundant conditions? Does each condition contribute to the solution?
3. [Clarity of Statement] Is the problem statement clear and unambiguous? Are mathematical terms used correctly?
4. [Notation Standards] Are mathematical symbols properly used? Is LaTeX formatting correct?
5. [Answer Correctness] Is the provided answer correct? Are there missing solutions?
6. [Solution Rigor] (If solution provided) Is the reasoning rigorous? Are there logical gaps or skipped steps?

Apply strict competition-level standards in your review.

IMPORTANT: Always respond in Chinese (中文), as the reviewers are Chinese teachers."""

            # 构建用户提示词（英文）
            user_prompt = f"""Please review the following math competition problem for rigor:

[Problem]
{problem}

[Answer]
{answer}"""
            
            if explanation:
                user_prompt += f"""

[Solution/Explanation]
{explanation}

**⚠️ CRITICAL WARNING ⚠️**: 
The provided explanation may contain SERIOUS ERRORS (wrong reasoning, calculation mistakes, or logical gaps). 
Your job is to find these errors, not to assume the explanation is correct.

**MANDATORY VERIFICATION PROCESS** (Strictly follow this order):

1. **Independent Verification FIRST** (Most Important):
   - Solve the problem YOURSELF using your own mathematical reasoning
   - Do NOT rely on or reference the explanation yet
   - Calculate/prove the answer independently
   - Record your own answer before comparing

2. **Critical Comparison**:
   - Compare YOUR answer with the PROVIDED answer
   - If they DIFFER → This is a MAJOR ISSUE - clearly state: "My independent verification gives [X], but the provided answer is [Y]"
   - If your reasoning contradicts the explanation → TRUST YOUR REASONING, not the explanation
   - Finding contradictions is GOOD - it means you found an error

3. **Explanation Critique** (Only after your independent verification):
   - Review the explanation with a CRITICAL eye
   - Actively look for: logical gaps, calculation errors, invalid steps, missing cases
   - Check if it correctly derives the given answer
   - If you find errors, explicitly state them

4. **Final Consistency Check**:
   - Are the problem, answer, and explanation all mutually consistent?
   - If not, identify which component has the error

**REMEMBER**: 
- Do NOT try to "make it work" if you find contradictions
- Do NOT assume the explanation is correct just because it's provided
- Your independent judgment is MORE important than agreeing with the explanation
- Be HARSH in your evaluation - competition-level standards require perfection"""
            else:
                user_prompt += """

**Note**: No solution/explanation provided. You must independently verify the answer's correctness through your own mathematical reasoning."""
            
            user_prompt += """

Please provide your review in Chinese using the following format:

【判断结果】严谨 / 不严谨

【严谨性评分】X/10（10分为完全严谨）

【条件分析】
- 完整性：（分析题目条件是否充分）
- 必要性：（分析是否有冗余条件）

【表述分析】
- 清晰性：（分析表述是否清晰无歧义）
- 符号规范：（分析数学符号是否规范）

【答案验证】
- 我的独立验证：（在不依赖解析的情况下，你通过独立推理得到的答案是什么？简述推理过程）
- 与给定答案对比：你的答案与给定答案是否一致？
  * 如果一致 → 说明答案可能正确
  * ⚠️ 如果不一致 → 这是严重问题！明确说明："我的验证得出[X]，但给定答案是[Y]，差异原因是..."
- 完整性检查：是否有遗漏的解或特殊情况？

【解析检查】（如提供了解析）
- 解析正确性：解析的推理是否正确？有无计算错误、逻辑错误？
- 逻辑严密性：推理是否严密？有无跳步、逻辑漏洞、未证明的断言？
- 与答案一致性：解析最终是否正确推导出给定答案？
- ⚠️ 矛盾检测：你的独立验证与解析是否有矛盾？如有，是解析错了还是你的推理有误？

【发现的问题】（如果有问题，逐条列出；如果没有问题，写"无"）

【修改建议】（如果有问题，给出具体修改建议；如果没有问题，写"无需修改"）"""

            # 调用 GPT-5.2
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.client.chat(
                messages=messages
                # GPT-5.2 不支持自定义 temperature，使用默认值
            )
            
            # 提取内容
            content = LLMClient.extract_content(response)
            
            if not content:
                return {
                    "success": False,
                    "error": "AI 返回内容为空"
                }
            
            # 解析判断结果
            is_rigorous = self._parse_rigor_result(content)
            
            # 提取发现的问题
            issues = self._extract_issues(content)
            
            return {
                "success": True,
                "is_rigorous": is_rigorous,
                "details": content,
                "verdict": "数学严谨性合格" if is_rigorous else "存在严谨性问题",
                "ai_model": self.model_name,
                "issues": issues
            }
        
        except Exception as e:
            # 打印详细错误信息到控制台
            error_msg = str(e) if str(e) else repr(e)
            print(f"[RigorCheck] 严谨性检测失败!")
            print(f"[RigorCheck] 异常类型: {type(e).__name__}")
            print(f"[RigorCheck] 异常信息: {error_msg}")
            print(f"[RigorCheck] 完整堆栈:")
            traceback.print_exc()
            
            # 如果是 HTTP 错误，尝试提取更多信息
            if hasattr(e, 'response'):
                try:
                    resp = e.response
                    print(f"[RigorCheck] HTTP 状态码: {resp.status_code}")
                    print(f"[RigorCheck] HTTP 响应内容: {resp.text[:1000]}")
                except:
                    pass
            
            return {
                "success": False,
                "error": f"严谨性检测失败: {type(e).__name__}: {error_msg}"
            }
    
    def _parse_rigor_result(self, content: str) -> bool:
        """
        解析严谨性判断结果
        
        Args:
            content: AI 返回的内容
            
        Returns:
            bool: 是否严谨
        """
        import re
        content_lower = content.lower()
        
        # 检查 [Verdict] 部分（英文）
        if "[verdict]" in content_lower:
            verdict_match = re.search(r'\[verdict\]\s*[:\-]?\s*(\w+)', content_lower)
            if verdict_match:
                verdict = verdict_match.group(1)
                if "not" in verdict or "no" in verdict:
                    return False
                if "rigorous" in verdict:
                    return True
        
        # 检查中文格式（兼容）
        if "【判断结果】" in content:
            start = content.find("【判断结果】")
            end = content.find("【", start + 1) if "【" in content[start + 1:] else len(content)
            result_section = content[start:end].lower()
            
            if "不严谨" in result_section:
                return False
            if "严谨" in result_section:
                return True
        
        # 检查评分（如果 ≥8 分认为严谨）
        score_match = re.search(r'\[rigor\s*score\]\s*[:\-]?\s*(\d+)', content_lower)
        if score_match:
            score = int(score_match.group(1))
            return score >= 8
        
        # 中文评分格式
        score_match = re.search(r'【严谨性评分】\s*(\d+)', content)
        if score_match:
            score = int(score_match.group(1))
            return score >= 8
        
        # 回退：简单判断
        if "not rigorous" in content_lower:
            return False
        if "rigorous" in content_lower and "not rigorous" not in content_lower:
            return True
        if "不严谨" in content:
            return False
        if "严谨" in content and "不严谨" not in content:
            return True
        
        # 默认认为严谨（保守策略）
        return True
    
    def _extract_issues(self, content: str) -> list:
        """
        从内容中提取发现的问题列表
        
        Args:
            content: AI 返回的内容
            
        Returns:
            list: 问题列表
        """
        import re
        issues = []
        
        # 查找 [Issues Found] 部分（英文）
        issues_match = re.search(r'\[issues\s*found\]\s*(.*?)(?=\[|$)', content, re.IGNORECASE | re.DOTALL)
        if issues_match:
            issues_section = issues_match.group(1).strip()
            
            # 如果是 "None" 或类似，返回空列表
            if issues_section.lower() in ["none", "none.", "no issues", "n/a", ""]:
                return []
            
            # 按行分割
            lines = issues_section.split('\n')
            for line in lines:
                line = line.strip()
                if line and line.lower() not in ["none", "none.", "no issues"]:
                    # 移除序号前缀
                    line = re.sub(r'^[\d\.\-\*]+\s*', '', line)
                    if line:
                        issues.append(line)
            
            if issues:
                return issues
        
        # 查找【发现的问题】部分（中文兼容）
        if "【发现的问题】" in content:
            start = content.find("【发现的问题】") + len("【发现的问题】")
            end = content.find("【", start) if "【" in content[start:] else len(content)
            issues_section = content[start:end].strip()
            
            # 如果是"无"，返回空列表
            if issues_section.strip() in ["无", "无。", "无问题", "暂无"]:
                return []
            
            # 按行分割
            lines = issues_section.split('\n')
            for line in lines:
                line = line.strip()
                if line and line not in ["无", "无。"]:
                    line = re.sub(r'^[\d\.\-\*]+\s*', '', line)
                    if line:
                        issues.append(line)
        
        return issues


# 全局服务实例
rigor_check_service = RigorCheckService()
