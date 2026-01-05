"""add_source_type_and_remove_problem

Revision ID: 68f87fd688c1
Revises: 589f93d393cd
Create Date: 2026-01-04 15:08:44.318086

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '68f87fd688c1'
down_revision = '589f93d393cd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级步骤：
    1. 在 validated_problem_exports 表添加 source_type 字段
    2. 删除 tasks.problem_id 外键
    3. 删除 reviews.problem_id 外键
    4. 删除 transactions.related_problem_id 外键
    5. 删除 problems 表
    """
    
    # 1. 添加新字段到 validated_problem_exports
    op.add_column('validated_problem_exports', 
        sa.Column('source_type', sa.String(20), nullable=False, server_default='direct')
    )
    
    # 添加索引
    op.create_index('idx_source_type', 'validated_problem_exports', ['source_type'])
    op.create_index('idx_user_source', 'validated_problem_exports', ['user_id', 'source_type'])
    op.create_index('idx_source_task', 'validated_problem_exports', ['source_type', 'task_id'])
    
    # 修改 originality_check 和 rigor_check 允许为 NULL（草稿状态下可以为空）
    op.alter_column('validated_problem_exports', 'originality_check',
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=True
    )
    op.alter_column('validated_problem_exports', 'rigor_check',
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=True
    )
    
    # 2. 删除 tasks.problem_id（如果存在）
    try:
        op.drop_constraint('tasks_problem_id_fkey', 'tasks', type_='foreignkey')
    except:
        pass  # 如果外键不存在，忽略
    
    try:
        op.drop_index('idx_problem_status', table_name='tasks')
    except:
        pass
    
    try:
        op.drop_column('tasks', 'problem_id')
    except:
        pass
    
    # 更新索引名称
    try:
        op.create_index('idx_validated_problem_status', 'tasks', ['validated_problem_id', 'status'])
    except:
        pass
    
    # 3. 删除 reviews.problem_id（如果存在）
    try:
        op.drop_constraint('reviews_problem_id_fkey', 'reviews', type_='foreignkey')
    except:
        pass
    
    try:
        op.drop_index('idx_problem_reviewer', table_name='reviews')
    except:
        pass
    
    try:
        op.drop_column('reviews', 'problem_id')
    except:
        pass
    
    # 更新索引
    try:
        op.create_index('idx_validated_problem_reviewer', 'reviews', ['validated_problem_id', 'reviewer_id'])
    except:
        pass
    
    # 修改 validated_problem_id 为 NOT NULL
    op.alter_column('reviews', 'validated_problem_id',
        existing_type=sa.Integer(),
        nullable=False
    )
    
    # 4. 删除 transactions.related_problem_id（如果存在）
    try:
        op.drop_constraint('transactions_related_problem_id_fkey', 'transactions', type_='foreignkey')
    except:
        pass
    
    try:
        op.drop_column('transactions', 'related_problem_id')
    except:
        pass
    
    # 5. 删除 problems 表（如果存在）
    try:
        # 先删除依赖的外键
        op.drop_constraint('problems_creator_id_fkey', 'problems', type_='foreignkey')
    except:
        pass
    
    try:
        op.drop_constraint('problems_parent_problem_id_fkey', 'problems', type_='foreignkey')
    except:
        pass
    
    try:
        op.drop_table('problems')
    except:
        pass


def downgrade() -> None:
    """
    降级步骤（回滚）：
    警告：这个操作会导致数据丢失！
    """
    
    # 1. 重新创建 problems 表（简化版，仅用于回滚）
    op.create_table('problems',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column('parent_problem_id', sa.Integer(), nullable=True),
        sa.Column('mongo_id', sa.String(24), nullable=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_foreign_key('problems_creator_id_fkey', 'problems', 'users', ['creator_id'], ['id'])
    op.create_foreign_key('problems_parent_problem_id_fkey', 'problems', 'problems', ['parent_problem_id'], ['id'])
    
    # 2. 恢复 tasks.problem_id
    op.add_column('tasks', sa.Column('problem_id', sa.Integer(), nullable=True))
    op.create_foreign_key('tasks_problem_id_fkey', 'tasks', 'problems', ['problem_id'], ['id'])
    op.create_index('idx_problem_status', 'tasks', ['problem_id', 'status'])
    
    # 3. 恢复 reviews.problem_id
    op.add_column('reviews', sa.Column('problem_id', sa.Integer(), nullable=True))
    op.create_foreign_key('reviews_problem_id_fkey', 'reviews', 'problems', ['problem_id'], ['id'])
    op.create_index('idx_problem_reviewer', 'reviews', ['problem_id', 'reviewer_id'])
    
    # 修改 validated_problem_id 为可NULL
    op.alter_column('reviews', 'validated_problem_id',
        existing_type=sa.Integer(),
        nullable=True
    )
    
    # 4. 恢复 transactions.related_problem_id
    op.add_column('transactions', sa.Column('related_problem_id', sa.Integer(), nullable=True))
    op.create_foreign_key('transactions_related_problem_id_fkey', 'transactions', 'problems', ['related_problem_id'], ['id'])
    
    # 5. 删除 validated_problem_exports 的新字段
    op.drop_index('idx_source_task', table_name='validated_problem_exports')
    op.drop_index('idx_user_source', table_name='validated_problem_exports')
    op.drop_index('idx_source_type', table_name='validated_problem_exports')
    
    op.drop_column('validated_problem_exports', 'source_type')
    
    # 恢复 originality_check 和 rigor_check 为 NOT NULL
    op.alter_column('validated_problem_exports', 'originality_check',
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=False
    )
    op.alter_column('validated_problem_exports', 'rigor_check',
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=False
    )

