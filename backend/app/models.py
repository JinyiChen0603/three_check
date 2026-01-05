"""
数据库模型定义
使用 SQLAlchemy 异步 ORM
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Index,
    select,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ==================== 字符串常量定义（替代枚举） ====================

class UserRole:
    """用户角色"""
    ADMIN = "admin"
    USER = "user"


class ValidatedProblemSourceType:
    """已验证题目来源类型"""
    DIRECT = "direct"      # 直接输入（题目验证导出页面）
    VARIANT = "variant"    # 变体生成（变体生成页面）
    OCR = "ocr"           # OCR识别（预留）


class MaterialCategory:
    """资料库类别"""
    # 大类
    HIGH_SCHOOL_COMPREHENSIVE = "high_school_comprehensive"  # 高中数学联赛综合
    COLLEGE_COMPREHENSIVE = "college_comprehensive"  # 大学数学竞赛综合
    
    # 高中数学联赛小类
    HIGH_SCHOOL_ALGEBRA = "high_school_algebra"  # 代数
    HIGH_SCHOOL_GEOMETRY = "high_school_geometry"  # 几何
    HIGH_SCHOOL_NUMBER_THEORY = "high_school_number_theory"  # 数论
    HIGH_SCHOOL_COMBINATORICS = "high_school_combinatorics"  # 组合
    
    # 大学数学竞赛小类
    COLLEGE_ALGEBRA = "college_algebra"  # 代数
    COLLEGE_NUMBER_THEORY = "college_number_theory"  # 数论
    COLLEGE_ANALYSIS = "college_analysis"  # 分析和方程
    COLLEGE_COMBINATORICS = "college_combinatorics"  # 组合和概率
    COLLEGE_GEOMETRY = "college_geometry"  # 几何和拓扑
    COLLEGE_OPTIMIZATION = "college_optimization"  # 最优化方法


class TaskType:
    """任务类型"""
    REVIEW_PROBLEM = "review_problem"  # 评分任务
    CREATE_PROBLEM = "create_problem"  # 出题任务


class TaskStatus:
    """任务状态"""
    PENDING = "pending"          # 待领取
    IN_PROGRESS = "in_progress"  # 进行中
    SUBMITTED = "submitted"      # 已提交
    APPROVED = "approved"        # 已批准
    REJECTED = "rejected"        # 已驳回
    TIMEOUT = "timeout"          # 已超时


class ReviewStatus:
    """评分状态"""
    PENDING = "pending"      # 待审核
    APPROVED = "approved"    # 已通过
    REJECTED = "rejected"    # 已驳回


class AdminReviewStatus:
    """管理员审核状态"""
    PENDING = "pending"      # 待审核
    APPROVED = "approved"    # 已通过
    REJECTED = "rejected"    # 未通过


class TransactionType:
    """交易类型"""
    PROBLEM_REWARD = "problem_reward"  # 出题奖励
    REVIEW_REWARD = "review_reward"    # 评分奖励
    WITHDRAWAL = "withdrawal"          # 提现
    ADJUSTMENT = "adjustment"          # 调整


class TransactionStatus:
    """交易状态"""
    PENDING = "pending"      # 待确认
    CONFIRMED = "confirmed"  # 已到账
    CANCELLED = "cancelled"  # 已取消


# ==================== 数据模型 ====================

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.USER, nullable=False, index=True)
    
    # 财务字段
    balance = Column(Float, default=0.0, nullable=False)
    
    # 统计字段（用于排行榜）
    problems_created_count = Column(Integer, default=0, nullable=False)
    reviews_completed_count = Column(Integer, default=0, nullable=False)
    
    # 状态字段
    is_active = Column(Boolean, default=True, nullable=False)
    is_impersonating = Column(Boolean, default=False, nullable=False)  # 访客模式标记
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    
    # 关系
    claimed_tasks = relationship("Task", back_populates="user")
    reviews = relationship("Review", back_populates="reviewer")
    transactions = relationship("Transaction", back_populates="user")
    
    async def calculate_balance(self, session) -> float:
        """
        计算用户真实余额（从Transaction表）
        
        余额 = SUM(已确认交易的金额)
        """
        from sqlalchemy.ext.asyncio import AsyncSession
        result = await session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(
                Transaction.user_id == self.id,
                Transaction.status == TransactionStatus.CONFIRMED
            )
        )
        return float(result.scalar() or 0.0)
    
    async def refresh_balance(self, session):
        """
        刷新缓存的余额字段
        
        从Transaction表重新计算余额并更新balance字段
        """
        self.balance = await self.calculate_balance(session)
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class Task(Base):
    """任务领取记录表"""
    __tablename__ = "tasks"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    validated_problem_id = Column(Integer, ForeignKey("validated_problem_exports.id", ondelete="CASCADE"), nullable=True, index=True)  # 关联题目
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 任务类型
    task_type = Column(String(50), default=TaskType.REVIEW_PROBLEM, nullable=False, index=True)
    
    # 批量任务信息
    batch_id = Column(String(50), nullable=True, index=True)  # 批次ID，同一批领取的任务有相同的batch_id
    total_count = Column(Integer, default=1, nullable=False)  # 本批次总任务数
    completed_count = Column(Integer, default=0, nullable=False)  # 已完成数
    abandoned_count = Column(Integer, default=0, nullable=False)  # 已放弃数
    
    # 状态
    status = Column(String(20), default=TaskStatus.PENDING, nullable=False, index=True)
    
    # 时间控制
    claimed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)  # 过期时间（领取后12小时）
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # 结果数据
    result_data = Column(JSON, nullable=True)  # 任务结果（JSON格式）
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    validated_problem = relationship("ValidatedProblemExport", foreign_keys=[validated_problem_id], back_populates="review_tasks")
    user = relationship("User", back_populates="claimed_tasks")
    reviews = relationship("Review", back_populates="task")  # 一个评分任务批次可以有多个评分记录
    
    # 索引
    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_validated_problem_status", "validated_problem_id", "status"),
        Index("idx_expires_at", "expires_at"),
    )
    
    def __repr__(self):
        return f"<Task(id={self.id}, type={self.task_type}, status={self.status})>"
    
    @property
    def is_expired(self) -> bool:
        """判断任务是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class Review(Base):
    """评分记录表"""
    __tablename__ = "reviews"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    validated_problem_id = Column(Integer, ForeignKey("validated_problem_exports.id", ondelete="CASCADE"), nullable=False, index=True)  # 关联题目
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)  # 关联评分任务批次
    
    # 答题验证（正确性验证流程）
    correctness_verification = Column(JSON, nullable=True)  # 正确性验证过程（4选1的记录）
    is_answer_correct = Column(Boolean, nullable=True)  # 答案是否正确（领取任务时为NULL，验证后填入）
    
    # 评分维度（0-10分）
    innovation_score = Column(Integer, nullable=True)  # 创新性评分 0-10
    rigor_score = Column(Integer, nullable=True)  # 数学严谨性评分 0-10
    comment = Column(Text, nullable=True)  # 评论
    
    # 一票否决
    is_vetoed = Column(Boolean, default=False, nullable=False)  # 是否一票否决
    veto_reason = Column(Text, nullable=True)  # 否决理由
    
    # 状态
    status = Column(String(20), default=ReviewStatus.PENDING, nullable=False, index=True)
    
    # 审核信息
    admin_note = Column(Text, nullable=True)  # 管理员备注
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    
    # 关系
    validated_problem = relationship("ValidatedProblemExport", foreign_keys=[validated_problem_id], back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews")
    task = relationship("Task", back_populates="reviews")
    
    # 索引
    __table_args__ = (
        Index("idx_validated_problem_reviewer", "validated_problem_id", "reviewer_id"),
        Index("idx_reviewer_status", "reviewer_id", "status"),
    )
    
    def __repr__(self):
        return f"<Review(id={self.id}, validated_problem_id={self.validated_problem_id}, reviewer_id={self.reviewer_id})>"


class Transaction(Base):
    """资金流水表"""
    __tablename__ = "transactions"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 金额
    amount = Column(Float, nullable=False)  # 金额（可正可负）
    
    # 交易类型
    transaction_type = Column(String(50), nullable=False, index=True)
    
    # 关联信息
    related_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # 状态
    status = Column(
        String(20),
        default=TransactionStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # 描述
    description = Column(String(500), nullable=True)
    
    # 余额快照（记录交易后的余额）
    balance_after = Column(Float, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    
    # 关系
    user = relationship("User", back_populates="transactions")
    
    # 索引
    __table_args__ = (
        Index("idx_user_type_status", "user_id", "transaction_type", "status"),
        Index("idx_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type={self.transaction_type})>"


class MaterialLibrary(Base):
    """资料库表"""
    __tablename__ = "material_library"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    
    # 分类
    category = Column(String(100), nullable=False, index=True)
    
    # 资料信息
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    baidu_link = Column(String(500), nullable=False)  # 百度网盘链接
    extract_code = Column(String(20), nullable=True)  # 提取码
    
    # 统计
    download_count = Column(Integer, default=0, nullable=False)  # 下载次数
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<MaterialLibrary(id={self.id}, title={self.title}, category={self.category})>"


class ValidationRecord(Base):
    """AI验证记录表"""
    __tablename__ = "validation_records"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    validated_problem_id = Column(Integer, ForeignKey("validated_problem_exports.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # 验证类型
    validation_type = Column(String(50), nullable=False)  # difficulty/originality/rigor
    
    # AI模型信息
    ai_model = Column(String(100), nullable=False)  # doubao-seed-thinking/gpt-4o/gpt-research
    
    # 验证参数
    attempts = Column(Integer, nullable=True)  # 尝试次数（对于难度验证是8次）
    correct_count = Column(Integer, nullable=True)  # 正确次数
    
    # 验证结果
    is_passed = Column(Boolean, nullable=False)  # 是否通过
    result_data = Column(JSON, nullable=False)  # 详细结果（JSON格式）
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关系
    validated_problem = relationship("ValidatedProblemExport", back_populates="validation_records")
    
    # 索引
    __table_args__ = (
        Index("idx_validated_problem_type", "validated_problem_id", "validation_type"),
    )
    
    def __repr__(self):
        return f"<ValidationRecord(id={self.id}, validated_problem_id={self.validated_problem_id}, type={self.validation_type}, passed={self.is_passed})>"


class ValidatedProblemExport(Base):
    """已验证题目导出记录表"""
    __tablename__ = "validated_problem_exports"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)  # 关联出题任务ID
    
    # 题目来源
    source_type = Column(
        String(20),
        default=ValidatedProblemSourceType.DIRECT,
        nullable=False,
        index=True
    )  # 来源类型：direct=直接输入, variant=变体生成, ocr=OCR识别
    
    # 题目信息
    content = Column(Text, nullable=False)  # 题目内容
    answer = Column(Text, nullable=False)  # 标准答案
    explanation = Column(Text, nullable=False)  # 解析（必填）
    
    # 难度验证结果
    difficulty_validation = Column(JSON, nullable=True)  # 难度验证结果
    
    # 二维质检结果（对于草稿可以为空对象）
    originality_check = Column(JSON, nullable=True)  # 原创性检测结果
    rigor_check = Column(JSON, nullable=True)  # 严谨性检测结果
    
    # 评分相关字段
    review_count = Column(Integer, default=0, nullable=False)  # 已完成的评分数
    avg_innovation_score = Column(Float, nullable=True)  # 平均创新性评分
    avg_rigor_score = Column(Float, nullable=True)  # 平均严谨性评分
    
    # 管理员审核相关
    admin_review_status = Column(
        String(20),
        default=AdminReviewStatus.PENDING,
        nullable=False,
        index=True
    )  # 管理员审核状态
    admin_reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 审核管理员ID
    admin_review_note = Column(Text, nullable=True)  # 管理员审核备注
    admin_reviewed_at = Column(DateTime, nullable=True)  # 审核时间
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关系
    user = relationship("User", backref="validated_exports", foreign_keys=[user_id])
    admin_reviewer = relationship("User", foreign_keys=[admin_reviewer_id])
    creation_task = relationship("Task", foreign_keys="[ValidatedProblemExport.task_id]", backref="created_problems")
    review_tasks = relationship("Task", foreign_keys="[Task.validated_problem_id]", back_populates="validated_problem")
    reviews = relationship("Review", back_populates="validated_problem", cascade="all, delete-orphan")
    validation_records = relationship("ValidationRecord", back_populates="validated_problem", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index("idx_user_source", "user_id", "source_type"),
        Index("idx_source_task", "source_type", "task_id"),
    )
    
    def __repr__(self):
        return f"<ValidatedProblemExport(id={self.id}, user_id={self.user_id}, source_type={self.source_type})>"
