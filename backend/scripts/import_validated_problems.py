"""
导入题目到可评分表（ValidatedProblemExport）
将JSON格式的题目导入到数据库，确保可以立即被评分

使用方法：
    python scripts/import_validated_problems.py [json文件路径] [选项]
    
选项：
    --admin-review-status [pending|approved]  管理员审核状态（默认：approved）
    --user [username]  指定导入者用户名（默认：第一个管理员）
    --simulate-checks  模拟生成质检结果（如果JSON中没有）
"""

import asyncio
import json
import sys
import argparse
import os
from pathlib import Path
from datetime import datetime, timedelta

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


async def import_validated_problems(
    json_file_path: str,
    admin_review_status: str = "approved",
    target_username: str = None,
    simulate_checks: bool = True
):
    """
    从JSON导入题目到ValidatedProblemExport表

    Args:
        json_file_path: JSON文件路径
        admin_review_status: 管理员审核状态（pending/approved/rejected）
        target_username: 指定导入者用户名
        simulate_checks: 是否模拟生成质检结果
    """

    print(f"\n{'='*70}")
    print(f"📥 导入题目到可评分表（ValidatedProblemExport）")
    print(f"{'='*70}\n")
    print(f"[Info] JSON文件: {json_file_path}")
    print(f"[Info] 审核状态: {admin_review_status}")

    # 读取JSON文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[Error] 无法读取JSON文件: {e}")
        return

    metadata = data.get('metadata', {})
    questions = data.get('questions', [])

    print(f"[Info] 批次名称: {metadata.get('batch_name', 'Unknown')}")
    print(f"[Info] 题目总数: {len(questions)}")
    print(f"[Info] 导出时间: {metadata.get('export_time', 'Unknown')}\n")

    if not questions:
        print("[Error] JSON中没有题目数据")
        return

    # 转换审核状态
    status_map = {
        "pending": AdminReviewStatus.PENDING,
        "approved": AdminReviewStatus.APPROVED,
        "rejected": AdminReviewStatus.REJECTED
    }
    
    admin_review_status_lower = admin_review_status.lower()
    if admin_review_status_lower not in status_map:
        print(f"[Error] 无效的审核状态: {admin_review_status}")
        print(f"[Info] 有效值: pending, approved, rejected")
        return

    review_status = status_map[admin_review_status_lower]
    
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
            batch_name = metadata.get('batch_name', Path(json_file_path).stem)
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

                    # 检查是否已存在（通过内容哈希或简单匹配）
                    # 为了性能，这里简化为检查内容前100字符
                    content_prefix = content[:100] if len(content) >= 100 else content
                    existing = await session.execute(
                        select(ValidatedProblemExport).where(
                            ValidatedProblemExport.content.like(f"{content_prefix}%")
                        ).limit(1)
                    )
                    if existing.scalar_one_or_none():
                        print(f"[Skip] [{idx}/{len(questions)}] {title[:40]}... (已存在)")
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
            print(f"[Info] 审核状态: {review_status.value}")
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
        description='导入题目到可评分表（ValidatedProblemExport）'
    )
    parser.add_argument(
        'json_file',
        nargs='?',
        default='scripts/01_100.json',
        help='JSON文件路径（默认：01_100.json）'
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
    
    # 解析JSON文件路径
    json_file = Path(args.json_file)
    if not json_file.is_absolute():
        # 相对路径：尝试从backend目录查找
        json_file = Path(__file__).parent.parent / args.json_file
    
    if not json_file.exists():
        print(f"[Error] JSON文件不存在: {json_file}")
        print(f"\n使用方法:")
        print(f"  python scripts/import_validated_problems.py [json文件路径] [选项]")
        print(f"\n选项:")
        print(f"  --admin-review-status [pending|approved]  审核状态（默认：approved）")
        print(f"  --user [username]  指定导入者（默认：第一个管理员）")
        print(f"  --simulate-checks  模拟质检结果（默认：开启）")
        sys.exit(1)
    
    await import_validated_problems(
        json_file_path=str(json_file),
        admin_review_status=args.admin_review_status,
        target_username=args.user,
        simulate_checks=args.simulate_checks
    )


if __name__ == "__main__":
    asyncio.run(main())

