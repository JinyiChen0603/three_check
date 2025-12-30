"""rename_validated_export_id_to_validated_problem_id

Revision ID: df57bf1cb678
Revises: ddd6233cec24
Create Date: 2025-12-29 16:11:47.201562

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df57bf1cb678'
down_revision = 'ddd6233cec24'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 重命名 tasks 表的列
    op.alter_column('tasks', 'validated_export_id', 
                    new_column_name='validated_problem_id',
                    existing_type=sa.Integer(),
                    existing_nullable=True)
    
    # 重命名 reviews 表的列
    op.alter_column('reviews', 'validated_export_id', 
                    new_column_name='validated_problem_id',
                    existing_type=sa.Integer(),
                    existing_nullable=True)


def downgrade() -> None:
    # 回滚：重命名回去
    op.alter_column('reviews', 'validated_problem_id', 
                    new_column_name='validated_export_id',
                    existing_type=sa.Integer(),
                    existing_nullable=True)
    
    op.alter_column('tasks', 'validated_problem_id', 
                    new_column_name='validated_export_id',
                    existing_type=sa.Integer(),
                    existing_nullable=True)

