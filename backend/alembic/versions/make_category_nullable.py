"""make category nullable in validated_problem_exports

Revision ID: make_category_nullable
Revises: validated_export_001
Create Date: 2025-12-25 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'make_category_nullable'
down_revision = 'validated_export_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查表和字段是否存在
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='validated_problem_exports' AND column_name='category'
    """))
    
    if not result.fetchone():
        # 字段不存在，跳过
        return
    
    # 将 category 字段改为可空
    op.alter_column('validated_problem_exports', 'category',
                    existing_type=postgresql.ENUM(
                        'high_school_comprehensive', 'college_comprehensive', 'high_school_algebra', 
                        'high_school_geometry', 'high_school_number_theory', 'high_school_combinatorics', 
                        'college_algebra', 'college_number_theory', 'college_analysis', 'college_combinatorics', 
                        'college_geometry', 'college_optimization', 
                        name='materialcategory'
                    ),
                    nullable=True)


def downgrade() -> None:
    # 将 category 字段改回非空（注意：如果有NULL值，回滚会失败）
    op.alter_column('validated_problem_exports', 'category',
                    existing_type=postgresql.ENUM(
                        'high_school_comprehensive', 'college_comprehensive', 'high_school_algebra', 
                        'high_school_geometry', 'high_school_number_theory', 'high_school_combinatorics', 
                        'college_algebra', 'college_number_theory', 'college_analysis', 'college_combinatorics', 
                        'college_geometry', 'college_optimization', 
                        name='materialcategory'
                    ),
                    nullable=False)




