"""
用户管理API
包含用户信息、余额、排名等功能
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel

from app.database import get_db
from app.models import User, UserRole, Transaction, TransactionStatus
from app.api.deps import get_current_user, get_current_admin_user


router = APIRouter()


# ==================== Pydantic 模型 ====================

class UserStatsResponse(BaseModel):
    """用户统计响应"""
    id: int
    username: str
    role: str
    balance: float
    problems_created_count: int
    reviews_completed_count: int
    rank: Optional[int] = None
    
    class Config:
        from_attributes = True


class LeaderboardResponse(BaseModel):
    """排行榜响应"""
    rank: int
    username: str
    balance: float
    problems_created: int
    reviews_completed: int
    total_earnings: float


class TransactionResponse(BaseModel):
    """交易记录响应"""
    id: int
    amount: float
    transaction_type: str
    status: str
    description: Optional[str]
    balance_after: Optional[float]
    created_at: str
    
    class Config:
        from_attributes = True


# ==================== API 路由 ====================

@router.get("/me/stats", response_model=UserStatsResponse, summary="获取我的统计信息")
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的统计信息
    
    包括：余额、出题数、评分数、排名等
    """
    # 计算排名
    result = await db.execute(
        select(func.count(User.id))
        .where(
            User.balance > current_user.balance,
            User.role == UserRole.USER,
            User.is_active == True
        )
    )
    better_users = result.scalar()
    rank = better_users + 1 if current_user.role == UserRole.USER else None
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role.value,
        "balance": current_user.balance,
        "problems_created_count": current_user.problems_created_count,
        "reviews_completed_count": current_user.reviews_completed_count,
        "rank": rank
    }


@router.get("/leaderboard", response_model=List[LeaderboardResponse], summary="获取排行榜")
async def get_leaderboard(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户排行榜（按余额排序）
    
    只显示普通用户的排名
    """
    query = (
        select(User)
        .where(
            User.role == UserRole.USER,
            User.is_active == True
        )
        .order_by(desc(User.balance))
        .limit(limit)
    )
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    leaderboard = []
    for idx, user in enumerate(users, start=1):
        leaderboard.append({
            "rank": idx,
            "username": user.username,
            "balance": user.balance,
            "problems_created": user.problems_created_count,
            "reviews_completed": user.reviews_completed_count,
            "total_earnings": user.balance
        })
    
    return leaderboard


@router.get("/me/transactions", summary="获取我的交易记录")
async def get_my_transactions(
    skip: int = 0,
    limit: int = 50,
    transaction_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的交易记录（流水）
    
    可按交易类型筛选
    """
    query = select(Transaction).where(Transaction.user_id == current_user.id)
    
    if transaction_type:
        query = query.where(Transaction.transaction_type == transaction_type)
    
    query = query.order_by(desc(Transaction.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return {
        "total": len(transactions),
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "transaction_type": t.transaction_type.value,
                "status": t.status.value,
                "description": t.description,
                "balance_after": t.balance_after,
                "created_at": t.created_at.isoformat(),
                "confirmed_at": t.confirmed_at.isoformat() if t.confirmed_at else None
            }
            for t in transactions
        ]
    }


@router.get("/me/balance", summary="获取我的余额详情")
async def get_my_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的余额详情
    
    包括：当前余额、待确认金额、总收入等
    """
    # 统计待确认金额
    result = await db.execute(
        select(func.sum(Transaction.amount))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.status == TransactionStatus.PENDING
        )
    )
    pending_amount = result.scalar() or 0
    
    # 统计总收入（已确认）
    result = await db.execute(
        select(func.sum(Transaction.amount))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.status == TransactionStatus.CONFIRMED,
            Transaction.amount > 0
        )
    )
    total_earnings = result.scalar() or 0
    
    # 分别统计出题和评分收入
    result = await db.execute(
        select(func.sum(Transaction.amount))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.status == TransactionStatus.CONFIRMED,
            Transaction.transaction_type == "problem_reward"
        )
    )
    problem_earnings = result.scalar() or 0
    
    result = await db.execute(
        select(func.sum(Transaction.amount))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.status == TransactionStatus.CONFIRMED,
            Transaction.transaction_type == "review_reward"
        )
    )
    review_earnings = result.scalar() or 0
    
    return {
        "current_balance": current_user.balance,
        "pending_amount": float(pending_amount),
        "total_earnings": float(total_earnings),
        "breakdown": {
            "problem_earnings": float(problem_earnings),
            "review_earnings": float(review_earnings)
        },
        "problems_created": current_user.problems_created_count,
        "reviews_completed": current_user.reviews_completed_count
    }


@router.get("/list", summary="获取用户列表（管理员）")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户列表（仅管理员可访问）
    """
    query = select(User).order_by(desc(User.balance)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return {
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role.value,
                "balance": u.balance,
                "problems_created_count": u.problems_created_count,
                "reviews_completed_count": u.reviews_completed_count,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ]
    }


@router.get("/{user_id}", summary="获取指定用户信息")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定用户的信息
    
    普通用户只能查看公开信息，管理员可以查看所有信息
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 公开信息
    user_info = {
        "id": user.id,
        "username": user.username,
        "role": user.role.value,
        "problems_created_count": user.problems_created_count,
        "reviews_completed_count": user.reviews_completed_count
    }
    
    # 管理员或本人可以查看更多信息
    if current_user.role == UserRole.ADMIN or current_user.id == user_id:
        user_info.update({
            "email": user.email,
            "balance": user.balance,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
        })
    
    return user_info

