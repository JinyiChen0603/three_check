"""Initial schema with all tables

Revision ID: 4deaebe64c95
Revises: 
Create Date: 2025-12-17 10:12:02.048946

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4deaebe64c95'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建用户表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'user', name='userrole'), nullable=False),
        sa.Column('balance', sa.Float(), nullable=False),
        sa.Column('problems_created_count', sa.Integer(), nullable=False),
        sa.Column('reviews_completed_count', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_impersonating', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # 创建题目表
    op.create_table(
        'problems',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column('parent_problem_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.JSON(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('difficulty', sa.Integer(), nullable=True),
        sa.Column('category', sa.Enum('high_school_comprehensive', 'college_comprehensive', 
                                      'high_school_algebra', 'high_school_geometry', 
                                      'high_school_number_theory', 'high_school_combinatorics',
                                      'college_algebra', 'college_number_theory', 'college_analysis',
                                      'college_combinatorics', 'college_geometry', 'college_optimization',
                                      name='materialcategory'), nullable=True),
        sa.Column('source_type', sa.Enum('ocr', 'manual', 'ai_variant', name='problemsourcetype'), nullable=False),
        sa.Column('ocr_image_url', sa.String(length=500), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('variant_count', sa.Integer(), nullable=False),
        sa.Column('validation_status', sa.Enum('not_validated', 'validating', 'passed', 'failed', 
                                               name='problemvalidationstatus'), nullable=False),
        sa.Column('validation_result', sa.JSON(), nullable=True),
        sa.Column('validation_correct_count', sa.Integer(), nullable=True),
        sa.Column('validation_completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'pending_review', 'published', 'archived', 
                                    name='problemstatus'), nullable=False),
        sa.Column('quality_check', sa.JSON(), nullable=True),
        sa.Column('quality_check_details', sa.JSON(), nullable=True),
        sa.Column('human_review_status', sa.Enum('pending', 'approved', 'rejected', 'need_modification',
                                                 name='humanreviewstatus'), nullable=False),
        sa.Column('human_review_note', sa.Text(), nullable=True),
        sa.Column('review_count', sa.Integer(), nullable=False),
        sa.Column('avg_innovation_score', sa.Float(), nullable=True),
        sa.Column('avg_rigor_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_problem_id'], ['problems.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_problems_id'), 'problems', ['id'], unique=False)
    op.create_index(op.f('ix_problems_creator_id'), 'problems', ['creator_id'], unique=False)
    op.create_index(op.f('ix_problems_parent_problem_id'), 'problems', ['parent_problem_id'], unique=False)
    op.create_index(op.f('ix_problems_category'), 'problems', ['category'], unique=False)
    op.create_index(op.f('ix_problems_validation_status'), 'problems', ['validation_status'], unique=False)
    op.create_index(op.f('ix_problems_status'), 'problems', ['status'], unique=False)
    op.create_index(op.f('ix_problems_human_review_status'), 'problems', ['human_review_status'], unique=False)
    op.create_index(op.f('ix_problems_created_at'), 'problems', ['created_at'], unique=False)
    op.create_index('idx_creator_status', 'problems', ['creator_id', 'status'], unique=False)
    op.create_index('idx_validation_status', 'problems', ['validation_status', 'status'], unique=False)
    
    # 创建任务表
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('problem_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.Enum('review_problem', 'create_problem', name='tasktype'), nullable=False),
        sa.Column('batch_id', sa.String(length=50), nullable=True),
        sa.Column('total_count', sa.Integer(), nullable=False),
        sa.Column('completed_count', sa.Integer(), nullable=False),
        sa.Column('abandoned_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'submitted', 'approved', 'rejected', 'timeout',
                                    name='taskstatus'), nullable=False),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)
    op.create_index(op.f('ix_tasks_problem_id'), 'tasks', ['problem_id'], unique=False)
    op.create_index(op.f('ix_tasks_user_id'), 'tasks', ['user_id'], unique=False)
    op.create_index(op.f('ix_tasks_batch_id'), 'tasks', ['batch_id'], unique=False)
    op.create_index(op.f('ix_tasks_status'), 'tasks', ['status'], unique=False)
    op.create_index(op.f('ix_tasks_expires_at'), 'tasks', ['expires_at'], unique=False)
    op.create_index('idx_user_status', 'tasks', ['user_id', 'status'], unique=False)
    op.create_index('idx_problem_status', 'tasks', ['problem_id', 'status'], unique=False)
    op.create_index('idx_expires_at', 'tasks', ['expires_at'], unique=False)
    
    # 创建评分表
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('problem_id', sa.Integer(), nullable=False),
        sa.Column('reviewer_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('correctness_verification', sa.JSON(), nullable=True),
        sa.Column('is_answer_correct', sa.Boolean(), nullable=False),
        sa.Column('innovation_score', sa.Integer(), nullable=True),
        sa.Column('rigor_score', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('is_vetoed', sa.Boolean(), nullable=False),
        sa.Column('veto_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='reviewstatus'), nullable=False),
        sa.Column('admin_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], ),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reviews_id'), 'reviews', ['id'], unique=False)
    op.create_index(op.f('ix_reviews_problem_id'), 'reviews', ['problem_id'], unique=False)
    op.create_index(op.f('ix_reviews_reviewer_id'), 'reviews', ['reviewer_id'], unique=False)
    op.create_index(op.f('ix_reviews_task_id'), 'reviews', ['task_id'], unique=True)
    op.create_index(op.f('ix_reviews_status'), 'reviews', ['status'], unique=False)
    op.create_index('idx_problem_reviewer', 'reviews', ['problem_id', 'reviewer_id'], unique=False)
    op.create_index('idx_reviewer_status', 'reviews', ['reviewer_id', 'status'], unique=False)
    
    # 创建交易表
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('transaction_type', sa.Enum('problem_reward', 'review_reward', 'withdrawal', 'adjustment',
                                              name='transactiontype'), nullable=False),
        sa.Column('related_problem_id', sa.Integer(), nullable=True),
        sa.Column('related_task_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'confirmed', 'cancelled', name='transactionstatus'), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('balance_after', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['related_problem_id'], ['problems.id'], ),
        sa.ForeignKeyConstraint(['related_task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    op.create_index(op.f('ix_transactions_user_id'), 'transactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_transactions_transaction_type'), 'transactions', ['transaction_type'], unique=False)
    op.create_index(op.f('ix_transactions_status'), 'transactions', ['status'], unique=False)
    op.create_index(op.f('ix_transactions_created_at'), 'transactions', ['created_at'], unique=False)
    op.create_index('idx_user_type_status', 'transactions', ['user_id', 'transaction_type', 'status'], unique=False)
    op.create_index('idx_created_at', 'transactions', ['created_at'], unique=False)
    
    # 创建资料库表
    op.create_table(
        'material_library',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category', sa.Enum('high_school_comprehensive', 'college_comprehensive', 
                                      'high_school_algebra', 'high_school_geometry', 
                                      'high_school_number_theory', 'high_school_combinatorics',
                                      'college_algebra', 'college_number_theory', 'college_analysis',
                                      'college_combinatorics', 'college_geometry', 'college_optimization',
                                      name='materialcategory'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('baidu_link', sa.String(length=500), nullable=False),
        sa.Column('extract_code', sa.String(length=20), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_material_library_id'), 'material_library', ['id'], unique=False)
    op.create_index(op.f('ix_material_library_category'), 'material_library', ['category'], unique=False)
    
    # 创建验证记录表
    op.create_table(
        'validation_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('problem_id', sa.Integer(), nullable=False),
        sa.Column('validation_type', sa.String(length=50), nullable=False),
        sa.Column('ai_model', sa.String(length=100), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=True),
        sa.Column('correct_count', sa.Integer(), nullable=True),
        sa.Column('is_passed', sa.Boolean(), nullable=False),
        sa.Column('result_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_validation_records_id'), 'validation_records', ['id'], unique=False)
    op.create_index(op.f('ix_validation_records_problem_id'), 'validation_records', ['problem_id'], unique=False)
    op.create_index(op.f('ix_validation_records_created_at'), 'validation_records', ['created_at'], unique=False)
    op.create_index('idx_problem_type', 'validation_records', ['problem_id', 'validation_type'], unique=False)
    
    # 创建已验证题目导出表
    op.create_table(
        'validated_problem_exports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('difficulty_validation', sa.JSON(), nullable=True),
        sa.Column('originality_check', sa.JSON(), nullable=False),
        sa.Column('rigor_check', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_validated_problem_exports_id'), 'validated_problem_exports', ['id'], unique=False)
    op.create_index(op.f('ix_validated_problem_exports_user_id'), 'validated_problem_exports', ['user_id'], unique=False)
    op.create_index(op.f('ix_validated_problem_exports_task_id'), 'validated_problem_exports', ['task_id'], unique=False)
    op.create_index(op.f('ix_validated_problem_exports_created_at'), 'validated_problem_exports', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_validated_problem_exports_created_at'), table_name='validated_problem_exports')
    op.drop_index(op.f('ix_validated_problem_exports_task_id'), table_name='validated_problem_exports')
    op.drop_index(op.f('ix_validated_problem_exports_user_id'), table_name='validated_problem_exports')
    op.drop_index(op.f('ix_validated_problem_exports_id'), table_name='validated_problem_exports')
    op.drop_table('validated_problem_exports')
    
    op.drop_index('idx_problem_type', table_name='validation_records')
    op.drop_index(op.f('ix_validation_records_created_at'), table_name='validation_records')
    op.drop_index(op.f('ix_validation_records_problem_id'), table_name='validation_records')
    op.drop_index(op.f('ix_validation_records_id'), table_name='validation_records')
    op.drop_table('validation_records')
    
    op.drop_index(op.f('ix_material_library_category'), table_name='material_library')
    op.drop_index(op.f('ix_material_library_id'), table_name='material_library')
    op.drop_table('material_library')
    
    op.drop_index('idx_created_at', table_name='transactions')
    op.drop_index('idx_user_type_status', table_name='transactions')
    op.drop_index(op.f('ix_transactions_created_at'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_status'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_transaction_type'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_user_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_table('transactions')
    
    op.drop_index('idx_reviewer_status', table_name='reviews')
    op.drop_index('idx_problem_reviewer', table_name='reviews')
    op.drop_index(op.f('ix_reviews_status'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_task_id'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_reviewer_id'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_problem_id'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_id'), table_name='reviews')
    op.drop_table('reviews')
    
    op.drop_index('idx_expires_at', table_name='tasks')
    op.drop_index('idx_problem_status', table_name='tasks')
    op.drop_index('idx_user_status', table_name='tasks')
    op.drop_index(op.f('ix_tasks_expires_at'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_status'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_batch_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_user_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_problem_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')
    
    op.drop_index('idx_validation_status', table_name='problems')
    op.drop_index('idx_creator_status', table_name='problems')
    op.drop_index(op.f('ix_problems_created_at'), table_name='problems')
    op.drop_index(op.f('ix_problems_human_review_status'), table_name='problems')
    op.drop_index(op.f('ix_problems_status'), table_name='problems')
    op.drop_index(op.f('ix_problems_validation_status'), table_name='problems')
    op.drop_index(op.f('ix_problems_category'), table_name='problems')
    op.drop_index(op.f('ix_problems_parent_problem_id'), table_name='problems')
    op.drop_index(op.f('ix_problems_creator_id'), table_name='problems')
    op.drop_index(op.f('ix_problems_id'), table_name='problems')
    op.drop_table('problems')
    
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')

