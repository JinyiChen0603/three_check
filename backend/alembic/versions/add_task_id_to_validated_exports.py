"""add task_id field to validated_problem_exports table

Revision ID: add_task_id_to_exports_001
Revises: remove_is_exported_001
Create Date: 2025-12-29 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_task_id_to_exports_001'
down_revision = 'remove_is_exported_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 task_id 字段
    op.add_column('validated_problem_exports',
                  sa.Column('task_id', sa.Integer(), nullable=True))

    # 添加外键约束
    op.create_foreign_key(
        'fk_validated_problem_exports_task_id',
        'validated_problem_exports',
        'tasks',
        ['task_id'],
        ['id']
    )

    # 添加索引
    op.create_index(
        op.f('ix_validated_problem_exports_task_id'),
        'validated_problem_exports',
        ['task_id'],
        unique=False
    )


def downgrade() -> None:
    # 删除索引
    op.drop_index(
        op.f('ix_validated_problem_exports_task_id'),
        table_name='validated_problem_exports'
    )

    # 删除外键约束
    op.drop_constraint(
        'fk_validated_problem_exports_task_id',
        'validated_problem_exports',
        type_='foreignkey'
    )

    # 删除字段
    op.drop_column('validated_problem_exports', 'task_id')

