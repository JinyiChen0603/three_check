"""add_validated_problem_id_to_validation_records

Revision ID: 7eaeb3407b67
Revises: cc6e11dc09bf
Create Date: 2025-12-31 12:00:19.038396

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7eaeb3407b67'
down_revision = 'cc6e11dc09bf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 validated_problem_id 列到 validation_records 表
    op.add_column('validation_records', 
                  sa.Column('validated_problem_id', sa.Integer(), nullable=True))
    
    # 添加外键约束
    op.create_foreign_key(
        'validation_records_validated_problem_id_fkey',
        'validation_records', 'validated_problem_exports',
        ['validated_problem_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 添加索引
    op.create_index(
        'idx_validated_problem_type',
        'validation_records',
        ['validated_problem_id', 'validation_type']
    )


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_validated_problem_type', table_name='validation_records')
    
    # 删除外键约束
    op.drop_constraint('validation_records_validated_problem_id_fkey', 
                      'validation_records', type_='foreignkey')
    
    # 删除列
    op.drop_column('validation_records', 'validated_problem_id')

