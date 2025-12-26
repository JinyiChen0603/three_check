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
        
        导出所有列的所有内容（JSON内容全部导出）
        
        Args:
            problems: 题目列表，每个题目包含所有字段的完整内容
            
        Returns:
            BytesIO: Excel文件的字节流
        """
        # 准备数据，导出所有列的所有内容
        data = []
        for idx, p in enumerate(problems, 1):
            # 将所有JSON字段序列化为字符串，保留完整内容
            difficulty_validation_str = json.dumps(p.get("difficulty_validation"), ensure_ascii=False, indent=2) if p.get("difficulty_validation") else ""
            originality_check_str = json.dumps(p.get("originality_check"), ensure_ascii=False, indent=2) if p.get("originality_check") else ""
            rigor_check_str = json.dumps(p.get("rigor_check"), ensure_ascii=False, indent=2) if p.get("rigor_check") else ""
            
            data.append({
                "序号": idx,
                "ID": p.get("id", ""),
                "用户ID": p.get("user_id", ""),
                "用户名称": p.get("username", ""),  # 添加用户名列
                "题目内容": p.get("content", ""),
                "标准答案": p.get("answer", ""),
                "题目解析": p.get("explanation", ""),
                "难度验证结果（完整JSON）": difficulty_validation_str,
                "原创性检测结果（完整JSON）": originality_check_str,
                "严谨性检测结果（完整JSON）": rigor_check_str,
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
                # JSON列需要更宽的宽度
                adjusted_width = min(max_length + 2, 100) if "JSON" in str(col) else min(max_length + 2, 50)
                col_letter = chr(64 + idx) if idx <= 26 else f"A{chr(64 + idx - 26)}"
                worksheet.column_dimensions[col_letter].width = adjusted_width
        
        output.seek(0)
        return output


# 全局服务实例
export_service = ExportService()

