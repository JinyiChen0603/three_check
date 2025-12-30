"""add_validated_export_id_to_tasks

Revision ID: ddd6233cec24
Revises: 0c464a350005
Create Date: 2025-12-29 15:26:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ddd6233cec24'
down_revision = '0c464a350005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 validated_export_id 字段，关联 validated_problem_exports 表
    op.add_column('tasks', 
        sa.Column('validated_export_id', sa.Integer(), nullable=True)
    )
    
    # 添加外键约束
    op.create_foreign_key(
        'fk_tasks_validated_export_id',
        'tasks', 'validated_problem_exports',
        ['validated_export_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 添加索引
    op.create_index(
        'idx_tasks_validated_export_id',
        'tasks',
        ['validated_export_id']
    )


def downgrade() -> None:
    # 反向操作
    op.drop_index('idx_tasks_validated_export_id', 'tasks')
    op.drop_constraint('fk_tasks_validated_export_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'validated_export_id')
