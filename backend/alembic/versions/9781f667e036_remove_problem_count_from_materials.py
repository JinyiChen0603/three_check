"""remove_problem_count_from_materials

Revision ID: 9781f667e036
Revises: 4deaebe64c95
Create Date: 2025-12-17 17:18:45.655954

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9781f667e036'
down_revision = '4deaebe64c95'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 删除 problem_count 列（如果存在）
    # 使用原生 SQL 检查列是否存在
    connection = op.get_bind()
    
    # 检查列是否存在
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='material_library' AND column_name='problem_count'
    """))
    
    if result.fetchone():
        op.drop_column('material_library', 'problem_count')


def downgrade() -> None:
    # 恢复 problem_count 列
    op.add_column('material_library', sa.Column('problem_count', sa.Integer(), nullable=False, server_default='0'))

