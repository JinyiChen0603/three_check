"""remove_problem_id_from_validation_records

Revision ID: 4235fd04f6f1
Revises: 7eaeb3407b67
Create Date: 2025-12-31 12:09:42.983057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4235fd04f6f1'
down_revision = '7eaeb3407b67'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 先删除外键约束（如果存在）
    op.drop_constraint('validation_records_problem_id_fkey', 'validation_records', type_='foreignkey')
    
    # 删除索引（如果存在）
    try:
        op.drop_index('ix_validation_records_problem_id', table_name='validation_records')
    except:
        pass  # 索引可能不存在
    
    # 删除 problem_id 列
    op.drop_column('validation_records', 'problem_id')


def downgrade() -> None:
    # 回滚：重新添加 problem_id 列
    op.add_column('validation_records', 
                  sa.Column('problem_id', sa.Integer(), nullable=True))
    
    # 重新添加外键约束
    op.create_foreign_key(
        'validation_records_problem_id_fkey',
        'validation_records', 'problems',
        ['problem_id'], ['id']
    )
    
    # 重新添加索引
    op.create_index('ix_validation_records_problem_id', 
                   'validation_records', ['problem_id'])

