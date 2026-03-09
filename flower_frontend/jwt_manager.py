#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""JWT Token管理模块 - 包含Access Token和Refresh Token机制"""

import jwt
import time
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import threading

# 配置参数
ACCESS_TOKEN_EXPIRY = 15 * 60  # Access Token有效期：15分钟
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60 * 60  # Refresh Token有效期：7天

# Token存储（内存缓存）
access_tokens: Dict[str, Dict] = {}
refresh_tokens: Dict[str, Dict] = {}

# 黑名单
blacklisted_access_tokens: set = set()
blacklisted_refresh_tokens: set = set()

# 线程锁
lock = threading.Lock()


def generate_access_token(user_id: int, username: str, role: str = 'user') -> str:
    """生成Access Token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(seconds=ACCESS_TOKEN_EXPIRY),
        'iat': datetime.utcnow(),
        'jti': secrets.token_urlsafe(16)  # Token唯一标识
    }
    
    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
    
    with lock:
        access_tokens[token] = payload.copy()
    
    return token


def generate_refresh_token(user_id: int, username: str) -> str:
    """生成Refresh Token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(seconds=REFRESH_TOKEN_EXPIRY),
        'iat': datetime.utcnow(),
        'jti': secrets.token_urlsafe(16)
    }
    
    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
    
    with lock:
        refresh_tokens[token] = payload.copy()
    
    return token


def verify_token(token: str, token_type: str = 'access') -> Tuple[bool, Optional[Dict], Optional[str]]:
    """验证Token"""
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        
        # 检查Token类型
        if payload.get('type') != token_type:
            return False, None, 'Token类型错误'
        
        # 检查是否在黑名单中
        with lock:
            if token in blacklisted_access_tokens or token in blacklisted_refresh_tokens:
                return False, None, 'Token已失效'
        
        return True, payload, None
        
    except jwt.ExpiredSignatureError:
        return False, None, 'Token已过期'
    except jwt.InvalidTokenError:
        return False, None, 'Token无效'


def add_to_blacklist(token: str, expires_at: datetime):
    """将Token加入黑名单"""
    with lock:
        blacklisted_access_tokens.add(token)
        blacklisted_refresh_tokens.add(token)
    
    # 清理过期黑名单（可选）
    cleanup_blacklist()


def cleanup_blacklist():
    """清理过期的黑名单Token"""
    current_time = datetime.utcnow()
    
    with lock:
        # 清理过期的Access Token
        expired_tokens = [
            token for token, payload in access_tokens.items()
            if datetime.utcfromtimestamp(payload['exp']) < current_time
        ]
        for token in expired_tokens:
            del access_tokens[token]
        
        # 清理过期的Refresh Token
        expired_tokens = [
            token for token, payload in refresh_tokens.items()
            if datetime.utcfromtimestamp(payload['exp']) < current_time
        ]
        for token in expired_tokens:
            del refresh_tokens[token]


def invalidate_user_tokens(user_id: int):
    """使某个用户的所有Token失效"""
    with lock:
        # 清除Access Tokens
        tokens_to_remove = [
            token for token, payload in access_tokens.items()
            if payload.get('user_id') == user_id
        ]
        for token in tokens_to_remove:
            del access_tokens[token]
            blacklisted_access_tokens.add(token)
        
        # 清除Refresh Tokens
        tokens_to_remove = [
            token for token, payload in refresh_tokens.items()
            if payload.get('user_id') == user_id
        ]
        for token in tokens_to_remove:
            del refresh_tokens[token]
            blacklisted_refresh_tokens.add(token)


def get_current_user_from_token(token: str) -> Optional[Dict]:
    """从Token中获取当前用户信息"""
    success, payload, error = verify_token(token, 'access')
    if success and payload:
        return {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'role': payload['role']
        }
    return None


def refresh_access_token(refresh_token: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """刷新Access Token"""
    success, payload, error = verify_token(refresh_token, 'refresh')
    
    if not success:
        return False, None, error
    
    # 生成新的Access Token
    new_access_token = generate_access_token(
        payload['user_id'],
        payload['username'],
        payload.get('role', 'user')
    )
    
    # 使旧的Refresh Token失效
    add_to_blacklist(refresh_token, datetime.utcnow() + timedelta(seconds=REFRESH_TOKEN_EXPIRY))
    
    return True, new_access_token, None
