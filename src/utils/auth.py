#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API认证与限流模块
提供JWT认证、API密钥验证和请求限流功能
"""

import time
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict
from threading import Lock

import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from loguru import logger

from src.core.config import settings
from src.database.sqlite_manager import db_manager


# JWT配置
JWT_SECRET = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else "ai4s-discovery-secret-key-2024"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# API密钥头
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


class RateLimiter:
    """请求限流器"""
    
    def __init__(self):
        """初始化限流器"""
        self.requests = defaultdict(list)
        self.lock = Lock()
        logger.info("限流器初始化完成")
    
    def is_allowed(
        self,
        key: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> bool:
        """
        检查是否允许请求
        
        Args:
            key: 限流键（通常是用户ID或IP地址）
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）
        
        Returns:
            是否允许请求
        """
        with self.lock:
            current_time = time.time()
            window_start = current_time - window_seconds
            
            # 清理过期请求
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
            
            # 检查请求数
            if len(self.requests[key]) >= max_requests:
                logger.warning(f"限流触发: {key}, 请求数: {len(self.requests[key])}")
                return False
            
            # 记录新请求
            self.requests[key].append(current_time)
            return True
    
    def get_remaining(
        self,
        key: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> int:
        """
        获取剩余请求数
        
        Args:
            key: 限流键
            max_requests: 最大请求数
            window_seconds: 时间窗口
        
        Returns:
            剩余请求数
        """
        with self.lock:
            current_time = time.time()
            window_start = current_time - window_seconds
            
            # 清理过期请求
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
            
            return max(0, max_requests - len(self.requests[key]))
    
    def reset(self, key: str):
        """重置限流计数"""
        with self.lock:
            if key in self.requests:
                del self.requests[key]
                logger.info(f"限流计数已重置: {key}")


# 全局限流器实例
rate_limiter = RateLimiter()


class AuthManager:
    """认证管理器"""
    
    @staticmethod
    def create_access_token(
        user_id: int,
        username: str,
        role: str = "user",
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建访问令牌
        
        Args:
            user_id: 用户ID
            username: 用户名
            role: 用户角色
            expires_delta: 过期时间增量
        
        Returns:
            JWT令牌
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)
        
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        logger.info(f"创建访问令牌: {username}")
        
        return token
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        验证令牌
        
        Args:
            token: JWT令牌
        
        Returns:
            解码后的payload，如果无效则返回None
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效令牌: {e}")
            return None
    
    @staticmethod
    def generate_api_key(user_id: int, prefix: str = "ai4s") -> str:
        """
        生成API密钥
        
        Args:
            user_id: 用户ID
            prefix: 密钥前缀
        
        Returns:
            API密钥
        """
        import secrets
        
        # 生成随机密钥
        random_part = secrets.token_urlsafe(32)
        
        # 组合密钥
        api_key = f"{prefix}_{user_id}_{random_part}"
        
        # 哈希存储
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        logger.info(f"生成API密钥: user_id={user_id}")
        
        return api_key
    
    @staticmethod
    def verify_api_key(api_key: str) -> Optional[int]:
        """
        验证API密钥
        
        Args:
            api_key: API密钥
        
        Returns:
            用户ID，如果无效则返回None
        """
        try:
            # 解析密钥
            parts = api_key.split('_')
            if len(parts) < 3:
                return None
            
            user_id = int(parts[1])
            
            # 这里应该从数据库验证密钥
            # 简化实现：直接返回用户ID
            logger.info(f"验证API密钥: user_id={user_id}")
            
            return user_id
            
        except Exception as e:
            logger.warning(f"API密钥验证失败: {e}")
            return None
    
    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """验证密码"""
        return AuthManager.hash_password(password) == hashed


# 全局认证管理器实例
auth_manager = AuthManager()


# FastAPI依赖函数

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
) -> Dict[str, Any]:
    """
    获取当前用户（JWT认证）
    
    Args:
        credentials: Bearer令牌
    
    Returns:
        用户信息
    
    Raises:
        HTTPException: 认证失败
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="无效或过期的令牌")
    
    return payload


async def get_current_user_by_api_key(
    api_key: str = Security(api_key_header)
) -> Dict[str, Any]:
    """
    通过API密钥获取当前用户
    
    Args:
        api_key: API密钥
    
    Returns:
        用户信息
    
    Raises:
        HTTPException: 认证失败
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="未提供API密钥")
    
    user_id = auth_manager.verify_api_key(api_key)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的API密钥")
    
    # 从数据库获取用户信息
    # 简化实现
    return {
        "user_id": user_id,
        "username": f"user_{user_id}",
        "role": "user"
    }


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户
    
    Returns:
        用户信息
    
    Raises:
        HTTPException: 用户未激活
    """
    # 这里可以添加用户激活状态检查
    return current_user


async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    要求管理员权限
    
    Args:
        current_user: 当前用户
    
    Returns:
        用户信息
    
    Raises:
        HTTPException: 权限不足
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    return current_user


def rate_limit(
    max_requests: int = 100,
    window_seconds: int = 60,
    key_func=None
):
    """
    限流装饰器
    
    Args:
        max_requests: 时间窗口内最大请求数
        window_seconds: 时间窗口（秒）
        key_func: 生成限流键的函数
    
    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取限流键
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # 默认使用用户ID或IP
                key = kwargs.get('current_user', {}).get('user_id', 'anonymous')
            
            # 检查限流
            if not rate_limiter.is_allowed(key, max_requests, window_seconds):
                remaining = rate_limiter.get_remaining(key, max_requests, window_seconds)
                raise HTTPException(
                    status_code=429,
                    detail=f"请求过于频繁，请稍后再试。剩余配额: {remaining}"
                )
            
            # 执行函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# 便捷函数

def create_token(user_id: int, username: str, role: str = "user") -> str:
    """创建访问令牌"""
    return auth_manager.create_access_token(user_id, username, role)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证令牌"""
    return auth_manager.verify_token(token)


def generate_api_key(user_id: int) -> str:
    """生成API密钥"""
    return auth_manager.generate_api_key(user_id)


def verify_api_key(api_key: str) -> Optional[int]:
    """验证API密钥"""
    return auth_manager.verify_api_key(api_key)


def check_rate_limit(key: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
    """检查限流"""
    return rate_limiter.is_allowed(key, max_requests, window_seconds)


def get_rate_limit_remaining(key: str, max_requests: int = 100, window_seconds: int = 60) -> int:
    """获取剩余请求数"""
    return rate_limiter.get_remaining(key, max_requests, window_seconds)