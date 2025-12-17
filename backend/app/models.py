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
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


# ==================== 枚举类型定义 ====================

class UserRole(str, enum.Enum):
    """用户角色"""
    ADMIN = "admin"
    USER = "user"


class ProblemSourceType(str, enum.Enum):
    """题目来源类型"""
    OCR = "ocr"              # OCR识别
    MANUAL = "manual"        # 手动输入
    AI_VARIANT = "ai_variant"  # AI变体


class ProblemValidationStatus(str, enum.Enum):
    """题目验证状态"""
    NOT_VALIDATED = "not_validated"  # 未验证
    VALIDATING = "validating"        # 验证中
    PASSED = "passed"                # 验证通过（≤4次正确）
    FAILED = "failed"                # 验证失败（>4次正确）


class ProblemStatus(str, enum.Enum):
    """题目生命周期状态"""
    DRAFT = "draft"              # 草稿
    PENDING_REVIEW = "pending_review"  # 待审核
    PUBLISHED = "published"      # 已发布
    ARCHIVED = "archived"        # 已下架


class HumanReviewStatus(str, enum.Enum):
    """人工质检状态"""
    PENDING = "pending"          # 待质检
    APPROVED = "approved"        # 质检通过
    REJECTED = "rejected"        # 质检不通过
    NEED_MODIFICATION = "need_modification"  # 需要修改


class MaterialCategory(str, enum.Enum):
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


class TaskType(str, enum.Enum):
    """任务类型"""
    REVIEW_PROBLEM = "review_problem"  # 评分任务
    CREATE_PROBLEM = "create_problem"  # 出题任务（可扩展）


class TaskStatus(str, enum.Enum):
    """任务状态"""
    PENDING = "pending"          # 待领取
    IN_PROGRESS = "in_progress"  # 进行中
    SUBMITTED = "submitted"      # 已提交
    APPROVED = "approved"        # 已批准
    REJECTED = "rejected"        # 已驳回
    TIMEOUT = "timeout"          # 已超时


class ReviewStatus(str, enum.Enum):
    """评分状态"""
    PENDING = "pending"      # 待审核
    APPROVED = "approved"    # 已通过
    REJECTED = "rejected"    # 已驳回


class TransactionType(str, enum.Enum):
    """交易类型"""
    PROBLEM_REWARD = "problem_reward"  # 出题奖励
    REVIEW_REWARD = "review_reward"    # 评分奖励
    WITHDRAWAL = "withdrawal"          # 提现
    ADJUSTMENT = "adjustment"          # 调整


class TransactionStatus(str, enum.Enum):
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
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    
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
    created_problems = relationship("Problem", back_populates="creator", foreign_keys="Problem.creator_id")
    claimed_tasks = relationship("Task", back_populates="user")
    reviews = relationship("Review", back_populates="reviewer")
    transactions = relationship("Transaction", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class Problem(Base):
    """题目表"""
    __tablename__ = "problems"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 母题关系（自关联）
    parent_problem_id = Column(Integer, ForeignKey("problems.id"), nullable=True, index=True)
    
    # 题目内容
    title = Column(String(200), nullable=False)
    content = Column(JSON, nullable=False)  # 题目详细内容（JSON格式）
    explanation = Column(Text, nullable=True)  # 题目解析
    answer = Column(Text, nullable=False)   # 标准答案
    difficulty = Column(Integer, nullable=True)  # 难度等级 1-5
    category = Column(Enum(MaterialCategory), nullable=True, index=True)  # 题目分类
    
    # 溯源字段
    source_type = Column(Enum(ProblemSourceType), default=ProblemSourceType.MANUAL, nullable=False)
    ocr_image_url = Column(String(500), nullable=True)  # OCR图片URL
    version = Column(Integer, default=1, nullable=False)  # 版本号
    variant_count = Column(Integer, default=0, nullable=False)  # 变形次数（限制≤10）
    
    # 验证字段
    validation_status = Column(
        Enum(ProblemValidationStatus),
        default=ProblemValidationStatus.NOT_VALIDATED,
        nullable=False,
        index=True
    )
    validation_result = Column(JSON, nullable=True)  # 验证结果详情（8次AI验证的记录）
    validation_correct_count = Column(Integer, nullable=True)  # 验证正确次数
    validation_completed_at = Column(DateTime, nullable=True)
    
    # 生命周期状态
    status = Column(
        Enum(ProblemStatus),
        default=ProblemStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    # 质检字段（三个维度）
    quality_check = Column(JSON, nullable=True)  # 质检结果 {"difficulty": bool, "originality": bool, "rigor": bool}
    quality_check_details = Column(JSON, nullable=True)  # 质检详细信息
    
    # 人工质检
    human_review_status = Column(
        Enum(HumanReviewStatus),
        default=HumanReviewStatus.PENDING,
        nullable=False,
        index=True
    )
    human_review_note = Column(Text, nullable=True)  # 人工质检理由/反馈
    
    # 审核相关
    review_count = Column(Integer, default=0, nullable=False)  # 已完成的评分数
    avg_innovation_score = Column(Float, nullable=True)  # 平均创新性评分
    avg_rigor_score = Column(Float, nullable=True)  # 平均数学严谨性评分
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)
    
    # 关系
    creator = relationship("User", back_populates="created_problems", foreign_keys=[creator_id])
    parent_problem = relationship("Problem", remote_side=[id], backref="variants")
    tasks = relationship("Task", back_populates="problem")
    reviews = relationship("Review", back_populates="problem")
    transactions = relationship("Transaction", back_populates="related_problem")
    validation_records = relationship("ValidationRecord", back_populates="problem")
    
    # 索引
    __table_args__ = (
        Index("idx_creator_status", "creator_id", "status"),
        Index("idx_validation_status", "validation_status", "status"),
    )
    
    def __repr__(self):
        return f"<Problem(id={self.id}, title={self.title}, creator_id={self.creator_id})>"


class Task(Base):
    """任务领取记录表"""
    __tablename__ = "tasks"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=True, index=True)  # 对于批量领取，单个任务可能没有problem_id
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 任务类型
    task_type = Column(Enum(TaskType), default=TaskType.REVIEW_PROBLEM, nullable=False)
    
    # 批量任务信息
    batch_id = Column(String(50), nullable=True, index=True)  # 批次ID，同一批领取的任务有相同的batch_id
    total_count = Column(Integer, default=1, nullable=False)  # 本批次总任务数
    completed_count = Column(Integer, default=0, nullable=False)  # 已完成数
    abandoned_count = Column(Integer, default=0, nullable=False)  # 已放弃数
    
    # 状态
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    
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
    problem = relationship("Problem", back_populates="tasks")
    user = relationship("User", back_populates="claimed_tasks")
    review = relationship("Review", back_populates="task", uselist=False)
    
    # 索引
    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_problem_status", "problem_id", "status"),
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
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, unique=True)  # 关联任务
    
    # 答题验证（正确性验证流程）
    correctness_verification = Column(JSON, nullable=True)  # 正确性验证过程（4选1的记录）
    is_answer_correct = Column(Boolean, nullable=False)  # 答案是否正确
    
    # 评分维度（0-10分）
    innovation_score = Column(Integer, nullable=True)  # 创新性评分 0-10
    rigor_score = Column(Integer, nullable=True)  # 数学严谨性评分 0-10
    comment = Column(Text, nullable=True)  # 评论
    
    # 一票否决
    is_vetoed = Column(Boolean, default=False, nullable=False)  # 是否一票否决
    veto_reason = Column(Text, nullable=True)  # 否决理由
    
    # 状态
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False, index=True)
    
    # 审核信息
    admin_note = Column(Text, nullable=True)  # 管理员备注
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    
    # 关系
    problem = relationship("Problem", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews")
    task = relationship("Task", back_populates="review")
    
    # 索引
    __table_args__ = (
        Index("idx_problem_reviewer", "problem_id", "reviewer_id"),
        Index("idx_reviewer_status", "reviewer_id", "status"),
    )
    
    def __repr__(self):
        return f"<Review(id={self.id}, problem_id={self.problem_id}, reviewer_id={self.reviewer_id})>"


class Transaction(Base):
    """资金流水表"""
    __tablename__ = "transactions"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 金额
    amount = Column(Float, nullable=False)  # 金额（可正可负）
    
    # 交易类型
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    
    # 关联信息
    related_problem_id = Column(Integer, ForeignKey("problems.id"), nullable=True)
    related_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # 状态
    status = Column(
        Enum(TransactionStatus),
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
    related_problem = relationship("Problem", back_populates="transactions")
    
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
    category = Column(Enum(MaterialCategory), nullable=False, index=True)
    
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
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False, index=True)
    
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
    problem = relationship("Problem", back_populates="validation_records")
    
    # 索引
    __table_args__ = (
        Index("idx_problem_type", "problem_id", "validation_type"),
    )
    
    def __repr__(self):
        return f"<ValidationRecord(id={self.id}, problem_id={self.problem_id}, type={self.validation_type}, passed={self.is_passed})>"

