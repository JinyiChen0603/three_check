"""add_validated_export_id_to_reviews

Revision ID: 0c464a350005
Revises: add_task_id_to_exports_001
Create Date: 2025-12-29 15:24:07.363951

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c464a350005'
down_revision = 'add_task_id_to_exports_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 将 problem_id 改为可空（兼容新旧数据）
    op.alter_column('reviews', 'problem_id',
                    existing_type=sa.Integer(),
                    nullable=True)
    
    # 2. 添加 validated_export_id 字段，关联 validated_problem_exports 表
    op.add_column('reviews', 
        sa.Column('validated_export_id', sa.Integer(), nullable=True)
    )
    
    # 3. 添加外键约束
    op.create_foreign_key(
        'fk_reviews_validated_export_id',
        'reviews', 'validated_problem_exports',
        ['validated_export_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 4. 添加索引
    op.create_index(
        'idx_reviews_validated_export_id',
        'reviews',
        ['validated_export_id']
    )


def downgrade() -> None:
    # 反向操作
    op.drop_index('idx_reviews_validated_export_id', 'reviews')
    op.drop_constraint('fk_reviews_validated_export_id', 'reviews', type_='foreignkey')
    op.drop_column('reviews', 'validated_export_id')
    
    # 恢复 problem_id 为非空
    op.alter_column('reviews', 'problem_id',
                    existing_type=sa.Integer(),
                    nullable=False)

