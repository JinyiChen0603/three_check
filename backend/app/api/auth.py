"""
认证API路由
处理登录、登出、修改密码、访客模式切换等功能
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import User, UserRole
from app.config import settings
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token
)
from app.api.deps import get_current_user, get_current_admin_user


router = APIRouter()


# ==================== Pydantic 模型 ====================

class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str = "bearer"
    user_info: dict


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str = Field(..., min_length=6, description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class ImpersonateRequest(BaseModel):
    """访客模式请求模型"""
    target_user_id: Optional[int] = Field(None, description="目标用户ID（None表示退出访客模式）")


# ==================== API 路由 ====================

@router.post("/login", response_model=Token, summary="用户登录")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    """
    # 查询用户
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    # 验证用户和密码
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    
    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    
    # 刷新用户余额（从Transaction表计算）
    await user.refresh_balance(db)
    
    await db.commit()
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "balance": user.balance,  # 已刷新的余额
            "is_impersonating": user.is_impersonating
        }
    }


@router.post("/logout", summary="用户登出")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    用户登出
    
    注意：JWT是无状态的，实际上客户端只需删除token即可
    这里提供一个标准的登出端点供客户端调用
    """
    return {
        "success": True,
        "message": "登出成功"
    }


@router.post("/change-password", summary="修改密码")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改当前用户密码
    
    - **old_password**: 旧密码
    - **new_password**: 新密码（至少6个字符）
    """
    # 验证旧密码
    if not verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    # 检查新密码是否与旧密码相同
    if request.old_password == request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与旧密码相同"
        )
    
    # 更新密码
    current_user.password_hash = get_password_hash(request.new_password)
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    
    return {
        "success": True,
        "message": "密码修改成功"
    }


@router.post("/impersonate", summary="管理员访客模式切换")
async def impersonate_user(
    request: ImpersonateRequest,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员切换到访客模式（以普通用户视角查看）
    
    - **target_user_id**: 目标用户ID（None表示退出访客模式）
    
    **只有管理员可以使用此功能**
    """
    # 如果target_user_id为None，表示退出访客模式
    if request.target_user_id is None:
        admin_user.is_impersonating = False
        await db.commit()
        
        return {
            "success": True,
            "message": "已退出访客模式",
            "is_impersonating": False,
            "target_user": None
        }
    
    # 查询目标用户
    result = await db.execute(
        select(User).where(User.id == request.target_user_id)
    )
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标用户不存在"
        )
    
    # 不能访客模式切换到另一个管理员
    if target_user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能切换到管理员账户"
        )
    
    # 设置访客模式
    admin_user.is_impersonating = True
    await db.commit()
    
    # 创建一个新的令牌，包含目标用户的信息，但标记为访客模式
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(admin_user.id),  # 实际用户ID仍然是管理员
            "username": admin_user.username,
            "role": admin_user.role,
            "impersonating": True,
            "target_user_id": target_user.id,
            "target_username": target_user.username
        },
        expires_delta=access_token_expires
    )
    
    return {
        "success": True,
        "message": f"已切换到用户 {target_user.username} 的视角",
        "is_impersonating": True,
        "access_token": access_token,
        "token_type": "bearer",
        "target_user": {
            "id": target_user.id,
            "username": target_user.username,
            "role": target_user.role,
            "balance": target_user.balance
        }
    }


@router.get("/me", summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户的信息
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "balance": current_user.balance,
        "problems_created_count": current_user.problems_created_count,
        "reviews_completed_count": current_user.reviews_completed_count,
        "is_active": current_user.is_active,
        "is_impersonating": current_user.is_impersonating,
        "created_at": current_user.created_at,
        "last_login_at": current_user.last_login_at
    }

