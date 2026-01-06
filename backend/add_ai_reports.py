"""
批量生成题目的原创性和严谨性AI检测报告
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# 导入服务
from app.services.originality_check_service import originality_check_service
from app.services.rigor_check_service import rigor_check_service


async def process_single_question(question: Dict[str, Any], index: int, total: int) -> Dict[str, Any]:
    """
    处理单个题目，添加原创性和严谨性报告
    
    Args:
        question: 题目数据
        index: 当前索引（从1开始）
        total: 总数
        
    Returns:
        更新后的题目数据
    """
    question_id = question.get('id', 'unknown')
    title = question.get('title', 'untitled')
    
    print(f"\n{'='*60}")
    print(f"[{index}/{total}] 处理题目 ID: {question_id} - {title}")
    print(f"{'='*60}")
    
    # 提取必要字段
    question_text = question.get('question_text', '')
    answer = question.get('answer', '')
    solution = question.get('solution', '')
    
    # 1. 原创性检测
    print(f"[{index}/{total}] 开始原创性检测...")
    try:
        originality_result = await originality_check_service.check_originality(
            problem=question_text
        )
        
        if originality_result.get('success'):
            question['originality_report'] = {
                'is_original': originality_result.get('is_original'),
                'verdict': originality_result.get('verdict'),
                'details': originality_result.get('details'),
                'ai_model': originality_result.get('ai_model'),
                'citations': originality_result.get('citations', [])
            }
            print(f"[{index}/{total}] ✓ 原创性检测完成: {originality_result.get('verdict')}")
        else:
            question['originality_report'] = {
                'error': originality_result.get('error')
            }
            print(f"[{index}/{total}] ✗ 原创性检测失败: {originality_result.get('error')}")
    except Exception as e:
        question['originality_report'] = {
            'error': f"异常: {str(e)}"
        }
        print(f"[{index}/{total}] ✗ 原创性检测异常: {str(e)}")
    
    # 等待一下，避免API调用过快
    await asyncio.sleep(2)
    
    # 2. 严谨性检测
    print(f"[{index}/{total}] 开始严谨性检测...")
    try:
        rigor_result = await rigor_check_service.check_rigor(
            problem=question_text,
            answer=answer,
            explanation=solution if solution else None
        )
        
        if rigor_result.get('success'):
            question['rigor_report'] = {
                'is_rigorous': rigor_result.get('is_rigorous'),
                'verdict': rigor_result.get('verdict'),
                'details': rigor_result.get('details'),
                'ai_model': rigor_result.get('ai_model'),
                'issues': rigor_result.get('issues', [])
            }
            print(f"[{index}/{total}] ✓ 严谨性检测完成: {rigor_result.get('verdict')}")
        else:
            question['rigor_report'] = {
                'error': rigor_result.get('error')
            }
            print(f"[{index}/{total}] ✗ 严谨性检测失败: {rigor_result.get('error')}")
    except Exception as e:
        question['rigor_report'] = {
            'error': f"异常: {str(e)}"
        }
        print(f"[{index}/{total}] ✗ 严谨性检测异常: {str(e)}")
    
    # 等待一下，避免API调用过快
    await asyncio.sleep(2)
    
    return question


async def process_batch(questions: List[Dict[str, Any]], batch_size: int = 5) -> List[Dict[str, Any]]:
    """
    批量处理题目（分批并发处理以提高效率）
    
    Args:
        questions: 题目列表
        batch_size: 每批处理的数量
        
    Returns:
        更新后的题目列表
    """
    total = len(questions)
    updated_questions = []
    
    for i in range(0, total, batch_size):
        batch = questions[i:i+batch_size]
        batch_start = i + 1
        
        print(f"\n{'#'*80}")
        print(f"处理批次 {batch_start}-{min(i+batch_size, total)} / {total}")
        print(f"{'#'*80}")
        
        # 并发处理当前批次
        tasks = [
            process_single_question(q, idx, total)
            for idx, q in enumerate(batch, start=batch_start)
        ]
        
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 检查结果
        for result in batch_results:
            if isinstance(result, Exception):
                print(f"✗ 批次处理出现异常: {result}")
            else:
                updated_questions.append(result)
        
        # 批次之间稍作等待
        if i + batch_size < total:
            print(f"\n等待3秒后处理下一批次...")
            await asyncio.sleep(3)
    
    return updated_questions


async def main():
    """
    主函数：读取JSON文件，处理所有题目，保存结果
    """
    # 文件路径
    input_file = Path("01_100.json")
    output_file = Path("01_100_with_reports.json")
    backup_file = Path("01_100_backup.json")
    
    print("="*80)
    print("批量生成原创性和严谨性AI报告")
    print("="*80)
    
    # 1. 读取JSON文件
    print(f"\n读取文件: {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"✗ 错误: 文件 {input_file} 不存在！")
        return
    except json.JSONDecodeError as e:
        print(f"✗ 错误: JSON解析失败: {e}")
        return
    
    # 2. 备份原文件
    print(f"创建备份: {backup_file}")
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 3. 提取题目列表
    questions = data.get('questions', [])
    total_count = len(questions)
    print(f"✓ 找到 {total_count} 道题目")
    
    if total_count == 0:
        print("✗ 错误: 没有找到题目！")
        return
    
    # 4. 处理所有题目（并发处理，提高效率）
    print(f"\n开始处理题目（批次大小: 3，并发处理）...")
    updated_questions = await process_batch(questions, batch_size=3)
    
    # 5. 更新数据
    data['questions'] = updated_questions
    
    # 6. 保存结果
    print(f"\n{'='*80}")
    print(f"保存结果到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 7. 统计结果
    originality_success = sum(
        1 for q in updated_questions 
        if 'originality_report' in q and 'error' not in q['originality_report']
    )
    rigor_success = sum(
        1 for q in updated_questions 
        if 'rigor_report' in q and 'error' not in q['rigor_report']
    )
    
    print(f"\n{'='*80}")
    print("处理完成！统计结果：")
    print(f"{'='*80}")
    print(f"总题目数: {total_count}")
    print(f"原创性检测成功: {originality_success}/{total_count}")
    print(f"严谨性检测成功: {rigor_success}/{total_count}")
    print(f"\n输出文件: {output_file}")
    print(f"备份文件: {backup_file}")
    print(f"{'='*80}")


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())

