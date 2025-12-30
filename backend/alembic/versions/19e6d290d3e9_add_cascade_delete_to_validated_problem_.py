"""add_cascade_delete_to_validated_problem_fks

Revision ID: 19e6d290d3e9
Revises: df57bf1cb678
Create Date: 2025-12-29 16:26:21.828304

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '19e6d290d3e9'
down_revision = 'df57bf1cb678'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### 为 tasks 和 reviews 表的 validated_problem_id 外键添加 CASCADE 删除 ###
    # 同时将约束名从 validated_export_id 改为 validated_problem_id，保持命名一致性
    
    # 1. 删除 tasks 表的旧外键约束
    op.drop_constraint('fk_tasks_validated_export_id', 'tasks', type_='foreignkey')
    
    # 2. 添加新的带 CASCADE 的外键约束（使用新的约束名）
    op.create_foreign_key(
        'fk_tasks_validated_problem_id',
        'tasks',
        'validated_problem_exports',
        ['validated_problem_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # 3. 删除 reviews 表的旧外键约束
    op.drop_constraint('fk_reviews_validated_export_id', 'reviews', type_='foreignkey')
    
    # 4. 添加新的带 CASCADE 的外键约束（使用新的约束名）
    op.create_foreign_key(
        'fk_reviews_validated_problem_id',
        'reviews',
        'validated_problem_exports',
        ['validated_problem_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # ### 移除 CASCADE，恢复原来的外键约束 ###
    
    # 1. 删除 tasks 表的新外键（带 CASCADE）
    op.drop_constraint('fk_tasks_validated_problem_id', 'tasks', type_='foreignkey')
    
    # 2. 恢复原来的外键（不带 CASCADE，使用旧的约束名）
    op.create_foreign_key(
        'fk_tasks_validated_export_id',
        'tasks',
        'validated_problem_exports',
        ['validated_problem_id'],
        ['id']
    )
    
    # 3. 删除 reviews 表的新外键（带 CASCADE）
    op.drop_constraint('fk_reviews_validated_problem_id', 'reviews', type_='foreignkey')
    
    # 4. 恢复原来的外键（不带 CASCADE，使用旧的约束名）
    op.create_foreign_key(
        'fk_reviews_validated_export_id',
        'reviews',
        'validated_problem_exports',
        ['validated_problem_id'],
        ['id']
    )

