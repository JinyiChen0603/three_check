"""convert_enums_to_strings

Revision ID: c666a8985e52
Revises: 68f87fd688c1
Create Date: 2026-01-04 15:18:14.125734

将所有 PostgreSQL ENUM 类型转换为 VARCHAR 字符串类型
解决大小写敏感问题
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c666a8985e52'
down_revision = '68f87fd688c1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    将所有 ENUM 类型转换为 VARCHAR 类型
    """
    
    # 1. users.role: userrole -> VARCHAR(20)
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(20) USING role::text")
    
    # 2. tasks.task_type: tasktype -> VARCHAR(50)
    op.execute("ALTER TABLE tasks ALTER COLUMN task_type TYPE VARCHAR(50) USING task_type::text")
    
    # 3. tasks.status: taskstatus -> VARCHAR(20)
    op.execute("ALTER TABLE tasks ALTER COLUMN status TYPE VARCHAR(20) USING status::text")
    
    # 4. reviews.status: reviewstatus -> VARCHAR(20)
    op.execute("ALTER TABLE reviews ALTER COLUMN status TYPE VARCHAR(20) USING status::text")
    
    # 5. transactions.transaction_type: transactiontype -> VARCHAR(50)
    op.execute("ALTER TABLE transactions ALTER COLUMN transaction_type TYPE VARCHAR(50) USING transaction_type::text")
    
    # 6. transactions.status: transactionstatus -> VARCHAR(20)
    op.execute("ALTER TABLE transactions ALTER COLUMN status TYPE VARCHAR(20) USING status::text")
    
    # 7. material_library.category: materialcategory -> VARCHAR(100)
    op.execute("ALTER TABLE material_library ALTER COLUMN category TYPE VARCHAR(100) USING category::text")
    
    # 8. validated_problem_exports.source_type: validatedproblemsourcetype -> VARCHAR(20)
    op.execute("ALTER TABLE validated_problem_exports ALTER COLUMN source_type TYPE VARCHAR(20) USING source_type::text")
    
    # 9. validated_problem_exports.admin_review_status: adminreviewstatus -> VARCHAR(20)
    op.execute("ALTER TABLE validated_problem_exports ALTER COLUMN admin_review_status TYPE VARCHAR(20) USING admin_review_status::text")
    
    # 删除所有 ENUM 类型（注意：先删除使用的字段，再删除类型）
    op.execute("DROP TYPE IF EXISTS userrole CASCADE")
    op.execute("DROP TYPE IF EXISTS tasktype CASCADE")
    op.execute("DROP TYPE IF EXISTS taskstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS reviewstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS transactiontype CASCADE")
    op.execute("DROP TYPE IF EXISTS transactionstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS materialcategory CASCADE")
    op.execute("DROP TYPE IF EXISTS validatedproblemsourcetype CASCADE")
    op.execute("DROP TYPE IF EXISTS adminreviewstatus CASCADE")
    
    # 删除旧的未使用的 ENUM 类型（兼容旧版本）
    op.execute("DROP TYPE IF EXISTS humanreviewstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS problemsourcetype CASCADE")
    op.execute("DROP TYPE IF EXISTS problemstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS problemvalidationstatus CASCADE")


def downgrade() -> None:
    """
    回滚：将 VARCHAR 转换回 ENUM 类型
    注意：此操作可能失败，如果数据中有不符合枚举定义的值
    """
    
    # 1. 重新创建 ENUM 类型
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'user')")
    op.execute("CREATE TYPE tasktype AS ENUM ('review_problem', 'create_problem')")
    op.execute("CREATE TYPE taskstatus AS ENUM ('pending', 'in_progress', 'submitted', 'approved', 'rejected', 'timeout')")
    op.execute("CREATE TYPE reviewstatus AS ENUM ('pending', 'approved', 'rejected')")
    op.execute("CREATE TYPE transactiontype AS ENUM ('problem_reward', 'review_reward', 'withdrawal', 'adjustment')")
    op.execute("CREATE TYPE transactionstatus AS ENUM ('pending', 'confirmed', 'cancelled')")
    op.execute("CREATE TYPE materialcategory AS ENUM ('high_school_comprehensive', 'college_comprehensive', 'high_school_algebra', 'high_school_geometry', 'high_school_number_theory', 'high_school_combinatorics', 'college_algebra', 'college_number_theory', 'college_analysis', 'college_combinatorics', 'college_geometry', 'college_optimization')")
    op.execute("CREATE TYPE validatedproblemsourcetype AS ENUM ('direct', 'variant', 'ocr')")
    op.execute("CREATE TYPE adminreviewstatus AS ENUM ('pending', 'approved', 'rejected')")
    
    # 2. 转换字段类型回 ENUM
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole")
    op.execute("ALTER TABLE tasks ALTER COLUMN task_type TYPE tasktype USING task_type::tasktype")
    op.execute("ALTER TABLE tasks ALTER COLUMN status TYPE taskstatus USING status::taskstatus")
    op.execute("ALTER TABLE reviews ALTER COLUMN status TYPE reviewstatus USING status::reviewstatus")
    op.execute("ALTER TABLE transactions ALTER COLUMN transaction_type TYPE transactiontype USING transaction_type::transactiontype")
    op.execute("ALTER TABLE transactions ALTER COLUMN status TYPE transactionstatus USING status::transactionstatus")
    op.execute("ALTER TABLE material_library ALTER COLUMN category TYPE materialcategory USING category::materialcategory")
    op.execute("ALTER TABLE validated_problem_exports ALTER COLUMN source_type TYPE validatedproblemsourcetype USING source_type::validatedproblemsourcetype")
    op.execute("ALTER TABLE validated_problem_exports ALTER COLUMN admin_review_status TYPE adminreviewstatus USING admin_review_status::adminreviewstatus")

