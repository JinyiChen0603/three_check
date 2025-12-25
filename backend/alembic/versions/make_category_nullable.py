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
    # 将 category 字段改为可空
    op.alter_column('validated_problem_exports', 'category',
                    existing_type=postgresql.ENUM(
                        'HIGH_SCHOOL_COMPREHENSIVE', 'COLLEGE_COMPREHENSIVE', 'HIGH_SCHOOL_ALGEBRA', 
                        'HIGH_SCHOOL_GEOMETRY', 'HIGH_SCHOOL_NUMBER_THEORY', 'HIGH_SCHOOL_COMBINATORICS', 
                        'COLLEGE_ALGEBRA', 'COLLEGE_NUMBER_THEORY', 'COLLEGE_ANALYSIS', 'COLLEGE_COMBINATORICS', 
                        'COLLEGE_GEOMETRY', 'COLLEGE_OPTIMIZATION', 
                        name='materialcategory'
                    ),
                    nullable=True)


def downgrade() -> None:
    # 将 category 字段改回非空（注意：如果有NULL值，回滚会失败）
    op.alter_column('validated_problem_exports', 'category',
                    existing_type=postgresql.ENUM(
                        'HIGH_SCHOOL_COMPREHENSIVE', 'COLLEGE_COMPREHENSIVE', 'HIGH_SCHOOL_ALGEBRA', 
                        'HIGH_SCHOOL_GEOMETRY', 'HIGH_SCHOOL_NUMBER_THEORY', 'HIGH_SCHOOL_COMBINATORICS', 
                        'COLLEGE_ALGEBRA', 'COLLEGE_NUMBER_THEORY', 'COLLEGE_ANALYSIS', 'COLLEGE_COMBINATORICS', 
                        'COLLEGE_GEOMETRY', 'COLLEGE_OPTIMIZATION', 
                        name='materialcategory'
                    ),
                    nullable=False)

