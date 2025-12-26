"""
题目导出服务
用于导出验证通过的题目到Excel
"""

import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
from io import BytesIO
import json


def _safe_bool(value) -> bool:
    """
    安全地将值转换为布尔值
    处理可能的字符串 "true"/"false" 或 "True"/"False"
    
    Args:
        value: 要转换的值
        
    Returns:
        bool: 转换后的布尔值
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    if isinstance(value, (int, float)):
        return bool(value)
    return False


class ExportService:
    """题目导出服务"""
    
    @staticmethod
    def format_check_result(check_result: Dict[str, Any]) -> str:
        """
        格式化检测结果为可读文本
        
        Args:
            check_result: 检测结果字典
            
        Returns:
            格式化后的文本
        """
        if not check_result or not check_result.get("success"):
            return "检测失败"
        
        # 提取关键信息
        is_passed = check_result.get("is_original") or check_result.get("is_rigorous")
        reason = check_result.get("reason", "")
        score = check_result.get("score", "N/A")
        
        return f"通过: {is_passed}\n分数: {score}\n原因: {reason}"
    
    @staticmethod
    def export_to_excel(problems: List[Dict[str, Any]]) -> BytesIO:
        """
        导出题目列表到Excel
        
        Args:
            problems: 题目列表，每个题目包含：
                - content: 题目内容
                - answer: 答案
                - explanation: 解析
                - difficulty_validation: 难度验证结果
                - originality_check: 原创性检测结果
                - rigor_check: 严谨性检测结果
                - created_at: 创建时间
                
        Returns:
            BytesIO: Excel文件的字节流
        """
        # 准备数据
        data = []
        for idx, p in enumerate(problems, 1):
            # 提取原创性结果 - 使用 _safe_bool 处理可能的字符串 "true"/"false"
            originality = p.get("originality_check", {})
            originality_passed = _safe_bool(originality.get("is_original", False))
            originality_reason = originality.get("reason", "")
            originality_score = originality.get("originality_score", "N/A")
            
            # 提取严谨性结果 - 使用 _safe_bool 处理可能的字符串 "true"/"false"
            rigor = p.get("rigor_check", {})
            rigor_passed = _safe_bool(rigor.get("is_rigorous", False))
            rigor_reason = rigor.get("reason", "")
            rigor_score = rigor.get("rigor_score", "N/A")
            
            # 提取难度验证结果（如果有）- 使用 _safe_bool 处理可能的字符串 "true"/"false"
            difficulty = p.get("difficulty_validation", {})
            difficulty_passed_raw = difficulty.get("is_passed", "N/A")
            difficulty_passed = _safe_bool(difficulty_passed_raw) if difficulty_passed_raw != "N/A" else "N/A"
            difficulty_correct = difficulty.get("correct_count", "N/A")
            difficulty_total = difficulty.get("total_attempts", "N/A")
            
            data.append({
                "序号": idx,
                "题目内容": p.get("content", ""),
                "标准答案": p.get("answer", ""),
                "题目解析": p.get("explanation", ""),
                
                # 难度验证
                "难度验证通过": ("是" if difficulty_passed else "否") if difficulty_passed != "N/A" else "未检测",
                "难度-正确次数": f"{difficulty_correct}/{difficulty_total}" if difficulty_correct != "N/A" else "N/A",
                
                # 原创性检测
                "原创性通过": "是" if originality_passed else "否",
                "原创性分数": originality_score,
                "原创性评价": originality_reason,
                
                # 严谨性检测
                "严谨性通过": "是" if rigor_passed else "否",
                "严谨性分数": rigor_score,
                "严谨性评价": rigor_reason,
                
                "创建时间": p.get("created_at", ""),
            })
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 导出到Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='验证题目', index=False)
            
            # 调整列宽
            worksheet = writer.sheets['验证题目']
            for idx, col in enumerate(df.columns, 1):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                # 限制最大宽度
                adjusted_width = min(max_length + 2, 50)
                col_letter = chr(64 + idx) if idx <= 26 else f"A{chr(64 + idx - 26)}"
                worksheet.column_dimensions[col_letter].width = adjusted_width
        
        output.seek(0)
        return output


# 全局服务实例
export_service = ExportService()

