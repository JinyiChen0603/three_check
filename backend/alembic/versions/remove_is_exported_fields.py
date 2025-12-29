"""remove is_exported and exported_at fields from validated_problem_exports

Revision ID: remove_is_exported_001
Revises: make_category_nullable
Create Date: 2025-12-26 14:39:03.936856

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'remove_is_exported_001'
down_revision = 'make_category_nullable'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查字段是否存在
    connection = op.get_bind()
    
    # 检查 is_exported 字段
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='validated_problem_exports' AND column_name='is_exported'
    """))
    
    if result.fetchone():
        # 删除 is_exported 字段
        op.drop_column('validated_problem_exports', 'is_exported')
    
    # 检查 exported_at 字段
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='validated_problem_exports' AND column_name='exported_at'
    """))
    
    if result.fetchone():
        # 删除 exported_at 字段
        op.drop_column('validated_problem_exports', 'exported_at')


def downgrade() -> None:
    # 恢复 exported_at 字段
    op.add_column('validated_problem_exports',
                  sa.Column('exported_at', sa.DateTime(), nullable=True))
    
    # 恢复 is_exported 字段
    op.add_column('validated_problem_exports',
                  sa.Column('is_exported', sa.Boolean(), nullable=True))

