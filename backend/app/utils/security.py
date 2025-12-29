"""
安全工具模块
处理密码加密、JWT 令牌等
"""

from datetime import datetime, timedelta
from typing import Optional, Union

from jose import jwt
import bcrypt

from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    ⚠️ 警告：当前使用明文比对（仅开发/测试环境）
    
    Args:
        plain_password: 明文密码
        hashed_password: 数据库中的密码（明文或哈希）
        
    Returns:
        bool: 密码是否匹配
    """
    # ⚠️ 明文比对模式（仅开发/测试）
    if plain_password == hashed_password:
        return True
    
    # 兼容模式：如果是 bcrypt 哈希，尝试验证
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    加密密码
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希密码
    """
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建 JWT 访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
        
    Returns:
        str: JWT 令牌
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码 JWT 令牌
    
    Args:
        token: JWT 令牌
        
    Returns:
        Optional[dict]: 解码后的数据，失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.JWTError:
        return None

