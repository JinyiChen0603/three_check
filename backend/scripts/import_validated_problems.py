"""
从 Markdown 文件导入题目到可评分表（ValidatedProblemExport）

使用方法：
    python scripts/import_validated_problems.py [选项]

选项：
    --markdown-dir [目录路径]  Markdown 文件目录（默认：scripts/Maths）
    --admin-review-status [pending|approved]  管理员审核状态（默认：approved）
    --user [username]  指定导入者用户名（默认：第一个管理员）
    --simulate-checks  模拟生成质检结果（默认：开启）

示例：
    # 导入 Maths 目录下的所有 MD 文件
    python scripts/import_validated_problems.py

    # 导入指定目录的 MD 文件
    python scripts/import_validated_problems.py --markdown-dir scripts/OtherMaths
"""

import asyncio
import sys
import argparse
import os
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 设置数据库连接URL（用于测试环境）
os.environ["DATABASE_URL"] = "postgresql+asyncpg://mathtasks:mathtasks123@postgres:5432/mathtasks_test"

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import _get_session_local
from app.models import (
    User, UserRole, ValidatedProblemExport, ValidationRecord,
    AdminReviewStatus, Task, TaskType, TaskStatus
)


def generate_mock_quality_check(passed: bool = True):
    """生成模拟的质检结果"""
    if passed:
        return {
            "success": True,
            "passed": True,
            "score": 8.5,
            "reasoning": "题目质量良好，符合标准",
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        return {
            "success": True,
            "passed": False,
            "score": 4.0,
            "reasoning": "需要改进",
            "timestamp": datetime.utcnow().isoformat()
        }


def parse_markdown_file(file_path: str) -> Optional[Dict]:
    """
    解析单个 Markdown 文件

    Args:
        file_path: MD 文件路径

    Returns:
        包含题目信息的字典，如果解析失败返回 None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 跳过 YAML 元数据头部（如果存在）
        # 元数据格式：--- ... ---
        yaml_pattern = r'^---\s*\n.*?\n---\s*\n'
        content = re.sub(yaml_pattern, '', content, flags=re.DOTALL)

        # 提取各个部分
        # 提取题目内容（## 题目）
        question_match = re.search(r'##\s*题目\s*\n(.*?)(?=##|$)', content, re.DOTALL)
        question_text = question_match.group(1).strip() if question_match else ""

        # 提取解答内容（## 解答）
        solution_match = re.search(r'##\s*解答\s*\n(.*?)(?=##\s*答案|$)', content, re.DOTALL)
        solution_text = solution_match.group(1).strip() if solution_match else ""

        # 提取答案内容（## 答案）
        answer_match = re.search(r'##\s*答案\s*\n(.*?)$', content, re.DOTALL)
        answer_text = answer_match.group(1).strip() if answer_match else ""

        # 验证必需字段
        if not question_text or not answer_text or not solution_text:
            return None

        return {
            'question_text': question_text,
            'answer': answer_text,
            'solution': solution_text,
            'title': Path(file_path).stem  # 使用文件名作为标题
        }

    except Exception as e:
        print(f"[Error] 解析文件失败 {file_path}: {e}")
        return None


def load_markdown_problems(markdown_dir: str) -> List[Dict]:
    """
    从目录加载所有 MD 文件

    Args:
        markdown_dir: MD 文件目录路径

    Returns:
        题目列表
    """
    dir_path = Path(markdown_dir)

    if not dir_path.exists():
        print(f"[Error] 目录不存在: {markdown_dir}")
        return []

    if not dir_path.is_dir():
        print(f"[Error] 路径不是目录: {markdown_dir}")
        return []

    # 扫描所有 .md 文件
    md_files = sorted(dir_path.glob("*.md"))

    if not md_files:
        print(f"[Warning] 目录中没有找到 .md 文件: {markdown_dir}")
        return []

    print(f"[Info] 找到 {len(md_files)} 个 MD 文件")

    problems = []
    for md_file in md_files:
        problem = parse_markdown_file(str(md_file))
        if problem:
            problems.append(problem)

    return problems


async def import_validated_problems(
    markdown_dir: str,
    admin_review_status: str = "approved",
    target_username: str = None,
    simulate_checks: bool = True
):
    """
    从 Markdown 文件导入题目到 ValidatedProblemExport 表

    Args:
        markdown_dir: Markdown 目录路径
        admin_review_status: 管理员审核状态（pending/approved/rejected）
        target_username: 指定导入者用户名
        simulate_checks: 是否模拟生成质检结果
    """

    print(f"\n{'='*70}")
    print(f"📥 导入题目到可评分表（ValidatedProblemExport）")
    print(f"{'='*70}\n")

    print(f"[Info] 数据源: Markdown 文件")
    print(f"[Info] 目录: {markdown_dir}")
    print(f"[Info] 审核状态: {admin_review_status}")

    questions = load_markdown_problems(markdown_dir)
    batch_name = Path(markdown_dir).name
    
    print(f"[Info] 批次名称: {batch_name}")
    print(f"[Info] 题目总数: {len(questions)}\n")

    if not questions:
        print(f"[Error] 没有找到题目数据")
        return

    # 验证并获取审核状态
    status_map = {
        'pending': AdminReviewStatus.PENDING,
        'approved': AdminReviewStatus.APPROVED,
        'rejected': AdminReviewStatus.REJECTED
    }
    
    review_status = status_map.get(admin_review_status.lower())
    if not review_status:
        print(f"[Error] 无效的审核状态: {admin_review_status}")
        print(f"[Info] 有效值: pending, approved, rejected")
        return

    AsyncSessionLocal = _get_session_local()

    async with AsyncSessionLocal() as session:
        try:
            # 1. 查找导入者用户
            if target_username:
                result = await session.execute(
                    select(User).where(User.username == target_username)
                )
                import_user = result.scalar_one_or_none()
                if not import_user:
                    print(f"[Error] 用户 '{target_username}' 不存在")
                    return
            else:
                # 默认使用第一个管理员
                result = await session.execute(
                    select(User).where(User.role == UserRole.ADMIN).limit(1)
                )
                import_user = result.scalar_one_or_none()
                if not import_user:
                    print("[Error] 未找到管理员用户，请先运行 init_users.py")
                    return

            print(f"[Info] 导入者: {import_user.username} (ID: {import_user.id})")
            print(f"[Info] 模拟质检: {'是' if simulate_checks else '否'}\n")

            # 🔧 优化：每次导入创建新的虚拟任务，使用唯一的batch_id
            # 生成唯一的batch_id（基于批次名称和时间戳）
            unique_batch_id = f"imported_{batch_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            # 直接创建新的虚拟任务（不检查已存在，避免重用）
            virtual_task = Task(
                user_id=import_user.id,
                task_type=TaskType.CREATE_PROBLEM,
                batch_id=unique_batch_id,  # 使用唯一的batch_id
                total_count=len(questions),
                completed_count=len(questions),  # 已全部完成
                status=TaskStatus.SUBMITTED,  # 已提交状态（这样题目才能被评分）
                claimed_at=datetime.utcnow(),
                submitted_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=365)
            )
            session.add(virtual_task)
            await session.flush()  # 获取task.id

            print(f"[Info] ✅ 创建新虚拟任务")
            print(f"       - Task ID: {virtual_task.id}")
            print(f"       - Batch ID: {unique_batch_id}")
            print(f"       - 题目数量: {len(questions)}\n")

            # 统计
            success_count = 0
            skip_count = 0
            error_count = 0
            error_details = []

            # 2. 逐个导入题目
            for idx, question in enumerate(questions, 1):
                try:
                    # 提取题目数据
                    content = question.get('question_text', '')
                    answer = question.get('answer', '')
                    explanation = question.get('solution', '')
                    title = question.get('title', f'题目_{idx}')

                    # 验证必需字段
                    if not content:
                        print(f"[Skip] [{idx}/{len(questions)}] {title[:40]}... (缺少题目内容)")
                        skip_count += 1
                        continue

                    if not answer:
                        print(f"[Skip] [{idx}/{len(questions)}] {title[:40]}... (缺少答案)")
                        skip_count += 1
                        continue

                    if not explanation:
                        print(f"[Skip] [{idx}/{len(questions)}] {title[:40]}... (缺少解析)")
                        skip_count += 1
                        continue


                    # 准备质检结果
                    if simulate_checks:
                        # 模拟生成质检结果（默认都通过）
                        difficulty_validation = {
                            "success": True,
                            "difficulty_level": question.get('difficulty', '中学'),
                            "confidence": 0.85,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        originality_check = generate_mock_quality_check(passed=True)
                        rigor_check = generate_mock_quality_check(passed=True)
                    else:
                        # 使用JSON中的质检结果（如果有）
                        difficulty_validation = question.get('difficulty_validation')
                        originality_check = question.get('originality_check')
                        rigor_check = question.get('rigor_check')

                        # 验证必需的质检字段
                        if not originality_check:
                            originality_check = generate_mock_quality_check(passed=True)
                        if not rigor_check:
                            rigor_check = generate_mock_quality_check(passed=True)

                    # 创建ValidatedProblemExport记录
                    validated_problem = ValidatedProblemExport(
                        user_id=import_user.id,
                        task_id=virtual_task.id,  # 关联到虚拟任务（这样才能被评分）
                        content=content,
                        answer=answer,
                        explanation=explanation,
                        difficulty_validation=difficulty_validation,
                        originality_check=originality_check,
                        rigor_check=rigor_check,
                        admin_review_status=review_status,
                        review_count=0,
                        avg_innovation_score=None,
                        avg_rigor_score=None,
                        created_at=datetime.utcnow()
                    )

                    session.add(validated_problem)
                    await session.flush()  # 获取ID

                    # 创建ValidationRecord记录（用于追溯）
                    validation_records = []

                    if difficulty_validation:
                        validation_records.append(ValidationRecord(
                            validated_problem_id=validated_problem.id,
                            validation_type="difficulty",
                            ai_model="imported",
                            result_data=difficulty_validation,
                            is_passed=difficulty_validation.get('success', False),
                            created_at=datetime.utcnow()
                        ))

                    if originality_check:
                        validation_records.append(ValidationRecord(
                            validated_problem_id=validated_problem.id,
                            validation_type="originality",
                            ai_model="imported",
                            result_data=originality_check,
                            is_passed=originality_check.get('passed', False),
                            created_at=datetime.utcnow()
                        ))

                    if rigor_check:
                        validation_records.append(ValidationRecord(
                            validated_problem_id=validated_problem.id,
                            validation_type="rigor",
                            ai_model="imported",
                            result_data=rigor_check,
                            is_passed=rigor_check.get('passed', False),
                            created_at=datetime.utcnow()
                        ))

                    for record in validation_records:
                        session.add(record)

                    # 提交
                    await session.commit()

                    print(f"[OK] [{idx}/{len(questions)}] ID={validated_problem.id}: {title[:50]}...")
                    success_count += 1

                except Exception as e:
                    await session.rollback()
                    error_msg = f"[Error] [{idx}/{len(questions)}] {question.get('title', 'Unknown')[:30]}... - {str(e)}"
                    print(error_msg)
                    error_details.append(error_msg)
                    error_count += 1
                    continue

            # 打印统计结果
            print("\n" + "="*70)
            print("📊 导入完成统计")
            print("="*70)
            print(f"✅ 成功导入: {success_count} 条")
            print(f"⏭️  跳过: {skip_count} 条")
            print(f"❌ 失败: {error_count} 条")
            print(f"📋 总计: {len(questions)} 条")
            print("="*70)

            if error_details:
                print("\n❌ 错误详情:")
                for detail in error_details[:10]:  # 只显示前10个
                    print(f"  {detail}")
                if len(error_details) > 10:
                    print(f"  ... 还有 {len(error_details) - 10} 个错误")

            # 查询导入后的题目状态
            result = await session.execute(
                select(ValidatedProblemExport).where(
                    ValidatedProblemExport.user_id == import_user.id
                )
            )
            total_problems = len(result.scalars().all())

            print(f"\n[Info] 用户 {import_user.username} 当前共有 {total_problems} 道题目")
            print(f"[Info] 审核状态: {review_status}")
            print(f"[Info] 关联任务: Task ID={virtual_task.id} (状态: SUBMITTED)")

            if review_status == AdminReviewStatus.APPROVED:
                print(f"[Info] ✅ 这些题目现在可以被领取评分！")
                print(f"[Info] 💡 题目已关联到已提交的虚拟任务，满足评分条件")
            elif review_status == AdminReviewStatus.PENDING:
                print(f"[Info] ⏳ 这些题目需要管理员审核后才能被评分")

            print("\n" + "="*70 + "\n")

        except Exception as e:
            await session.rollback()
            print(f"\n[Error] 导入过程发生错误: {e}")
            import traceback
            traceback.print_exc()
            raise


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='从 Markdown 文件导入题目到可评分表（ValidatedProblemExport）'
    )
    parser.add_argument(
        '--markdown-dir',
        default='scripts/Maths',
        help='Markdown 文件目录路径（默认：scripts/Maths）'
    )
    parser.add_argument(
        '--admin-review-status',
        choices=['pending', 'approved', 'rejected'],
        default='approved',
        help='管理员审核状态（默认：approved）'
    )
    parser.add_argument(
        '--user',
        help='指定导入者用户名（默认：第一个管理员）'
    )
    parser.add_argument(
        '--simulate-checks',
        action='store_true',
        default=True,
        help='模拟生成质检结果（默认：开启）'
    )

    args = parser.parse_args()

    # 处理 Markdown 目录路径
    markdown_dir = Path(args.markdown_dir)
    if not markdown_dir.is_absolute():
        # 相对路径：从 backend 目录查找
        markdown_dir = Path(__file__).parent.parent / args.markdown_dir

    if not markdown_dir.exists():
        print(f"[Error] Markdown 目录不存在: {markdown_dir}")
        print(f"\n使用方法:")
        print(f"  python scripts/import_validated_problems.py [选项]")
        print(f"\n选项:")
        print(f"  --markdown-dir [目录路径]  Markdown 文件目录（默认：scripts/Maths）")
        print(f"  --admin-review-status [pending|approved]  审核状态（默认：approved）")
        print(f"  --user [username]  指定导入者（默认：第一个管理员）")
        sys.exit(1)

    await import_validated_problems(
        markdown_dir=str(markdown_dir),
        admin_review_status=args.admin_review_status,
        target_username=args.user,
        simulate_checks=args.simulate_checks
    )


if __name__ == "__main__":
    asyncio.run(main())

