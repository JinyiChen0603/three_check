"""add_mongo_id_to_problems

Revision ID: add_mongo_id_001
Revises: 9781f667e036
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_mongo_id_001'
down_revision = '9781f667e036'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查 mongo_id 字段是否已存在
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='problems' AND column_name='mongo_id'
    """))
    
    if not result.fetchone():
        # 添加 mongo_id 字段（如果不存在）
        op.add_column('problems', sa.Column('mongo_id', sa.String(length=24), nullable=True))
        # 创建索引
        op.create_index('ix_problems_mongo_id', 'problems', ['mongo_id'], unique=True)
    
    # 将 content, answer 字段改为可空（因为新数据会存在MongoDB）
    # 注意：这里不删除字段，保持兼容性
    op.alter_column('problems', 'content', nullable=True, existing_type=sa.JSON())
    op.alter_column('problems', 'answer', nullable=True, existing_type=sa.Text())


def downgrade() -> None:
    # 删除索引
    op.drop_index('ix_problems_mongo_id', table_name='problems')
    # 删除字段
    op.drop_column('problems', 'mongo_id')
    
    # 恢复字段约束（如果需要）
    op.alter_column('problems', 'content', nullable=False, existing_type=sa.JSON())
    op.alter_column('problems', 'answer', nullable=False, existing_type=sa.Text())

