"""
验证服务模块（协调器）
整合三个独立的检测服务：难度、原创性、严谨性
"""

import asyncio
from typing import Dict, Any, Optional

# 导入三个独立的检测服务
from app.services.difficulty_check_service import difficulty_check_service
from app.services.originality_check_service import originality_check_service
from app.services.rigor_check_service import rigor_check_service


class ValidationService:
    """
    题目验证服务（对抗验证）- 使用 Doubao Seed Thinking
    
    这是一个兼容层，实际调用 difficulty_check_service
    """
    
    def __init__(self):
        self.difficulty_service = difficulty_check_service
    
    async def validate_difficulty(
        self,
        problem: str,
        answer: str,
        explanation: Optional[str] = None,
        attempts: int = 8
    ) -> Dict[str, Any]:
        """
        验证题目难度（对抗验证）
        
        委托给 difficulty_check_service 处理
        """
        return await self.difficulty_service.validate_difficulty(
            problem=problem,
            answer=answer,
            explanation=explanation,
            attempts=attempts
        )


class QualityCheckService:
    """
    质量检查协调服务（三维度）
    
    整合三个独立的检测服务：
    1. 难度检测 - DifficultyCheckService (Doubao)
    2. 原创性检测 - OriginalityCheckService (GPT-4o)
    3. 严谨性检测 - RigorCheckService (GPT-4o)
    """
    
    def __init__(self):
        # 使用三个独立的服务
        self.difficulty_service = difficulty_check_service
        self.originality_service = originality_check_service
        self.rigor_service = rigor_check_service
    
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
            difficulty_task = self.difficulty_service.validate_difficulty(
                problem, answer, explanation
            )
            originality_task = self.originality_service.check_originality(problem)
            rigor_task = self.rigor_service.check_rigor(problem, answer, explanation)
            
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
    
    async def sequential_quality_check(
        self,
        problem: str,
        answer: str,
        explanation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        顺序执行质量检查（三个维度）
        
        1. 先检查创新性和严谨性（并发）
        2. 只有两项都通过后，才检查难度（豆包对抗验证）
        
        这样可以节省成本，如果基础检测不通过就不调用昂贵的难度检测
        
        Returns:
            Dict: {
                "success": bool,
                "all_passed": bool,
                "originality": Dict,
                "rigor": Dict,
                "difficulty": Dict,  # 可能为 None
                "early_stop": bool,
                "early_stop_reason": str
            }
        """
        try:
            # 第一步：先检查创新性和严谨性（并发执行这两项）
            originality_result, rigor_result = await asyncio.gather(
                self.originality_service.check_originality(problem),
                self.rigor_service.check_rigor(problem, answer, explanation),
                return_exceptions=True
            )
            
            # 处理异常
            if isinstance(originality_result, Exception):
                originality_result = {"success": False, "error": str(originality_result)}
            if isinstance(rigor_result, Exception):
                rigor_result = {"success": False, "error": str(rigor_result)}
            
            # 检查创新性和严谨性是否都通过
            originality_passed = (
                originality_result.get("success", False) and 
                originality_result.get("is_original", False)
            )
            rigor_passed = (
                rigor_result.get("success", False) and 
                rigor_result.get("is_rigorous", False)
            )
            
            # 如果创新性或严谨性未通过，提前终止
            if not (originality_passed and rigor_passed):
                early_stop_reasons = []
                if not originality_passed:
                    early_stop_reasons.append("创新性检测未通过")
                if not rigor_passed:
                    early_stop_reasons.append("严谨性检测未通过")
                
                return {
                    "success": True,
                    "all_passed": False,
                    "originality": originality_result,
                    "rigor": rigor_result,
                    "difficulty": None,  # 未执行难度检测
                    "early_stop": True,
                    "early_stop_reason": "；".join(early_stop_reasons),
                    "summary": {
                        "difficulty_passed": None,  # 未检测
                        "originality_passed": originality_passed,
                        "rigor_passed": rigor_passed,
                    }
                }
            
            # 第二步：创新性和严谨性都通过，执行难度检测
            difficulty_result = await self.difficulty_service.validate_difficulty(
                problem, answer, explanation
            )
            
            if isinstance(difficulty_result, Exception):
                difficulty_result = {"success": False, "error": str(difficulty_result)}
            
            # 判断是否全部通过
            all_passed = (
                difficulty_result.get("success", False) and 
                difficulty_result.get("is_passed", False)
            )
            
            return {
                "success": True,
                "all_passed": all_passed,
                "originality": originality_result,
                "rigor": rigor_result,
                "difficulty": difficulty_result,
                "early_stop": False,
                "early_stop_reason": None,
                "summary": {
                    "difficulty_passed": difficulty_result.get("is_passed", False),
                    "originality_passed": originality_passed,
                    "rigor_passed": rigor_passed,
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"质量检查失败: {str(e)}"
            }


# 全局服务实例
validation_service = ValidationService()
quality_check_service = QualityCheckService()
