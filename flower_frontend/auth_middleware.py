#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""鉴权中间件"""

from functools import wraps
from flask import request, jsonify, g
import jwt
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ==================== JWT配置 ====================

from config import config

SECRET_KEY = config.JWT_SECRET_KEY
ALGORITHM = config.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = config.JWT_REFRESH_TOKEN_EXPIRE_DAYS

# ==================== JWT工具函数 ====================

def generate_access_token(user_id: int, username: str, role: str = 'user') -> str:
    """生成访问令牌"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'type': 'access',
        'exp': datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def generate_refresh_token(user_id: int, username: str) -> str:
    """生成刷新令牌"""
    payload = {
        'user_id': user_id,
        'username': username,
        'type': 'refresh',
        'exp': datetime.utcnow() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """解码令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            'valid': True,
            'payload': payload
        }
    except jwt.ExpiredSignatureError:
        return {
            'valid': False,
            'error': 'token_expired',
            'message': '令牌已过期'
        }
    except jwt.InvalidTokenError as e:
        return {
            'valid': False,
            'error': 'token_invalid',
            'message': f'令牌无效: {str(e)}'
        }

def verify_token(token: str) -> tuple[bool, dict]:
    """验证令牌"""
    result = decode_token(token)
    if not result['valid']:
        return False, {'error': result['error'], 'message': result['message']}
    
    payload = result['payload']
    
    # 检查令牌类型
    if payload.get('type') != 'access':
        return False, {'error': 'token_type_error', 'message': '令牌类型错误'}
    
    return True, payload

# ==================== 鉴权装饰器 ====================

def auth_required(f):
    """需要认证的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头获取token
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'code': 2001,
                'message': '未授权，缺少认证信息',
                'data': None,
                'timestamp': datetime.now().isoformat()
            }), 401
        
        # 提取Bearer token
        try:
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
        except IndexError:
            return jsonify({
                'code': 2001,
                'message': '未授权，认证格式错误',
                'data': None,
                'timestamp': datetime.now().isoformat()
            }), 401
        
        # 验证token
        is_valid, result = verify_token(token)
        if not is_valid:
            error_code = 2002 if result.get('error') == 'token_expired' else 2003
            return jsonify({
                'code': error_code,
                'message': result.get('message', '令牌无效'),
                'data': None,
                'timestamp': datetime.now().isoformat()
            }), 401
        
        # 将用户信息存储到g对象中
        g.user_id = result.get('user_id')
        g.username = result.get('username')
        g.role = result.get('role', 'user')
        
        return f(*args, **kwargs)
    
    return decorated_function

def role_required(*required_roles):
    """需要特定角色的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查是否已认证
            if not hasattr(g, 'user_id'):
                return jsonify({
                    'code': 2001,
                    'message': '未授权，请先登录',
                    'data': None,
                    'timestamp': datetime.now().isoformat()
                }), 401
            
            # 检查角色
            user_role = g.role if hasattr(g, 'role') else 'user'
            if user_role not in required_roles:
                return jsonify({
                    'code': 2004,
                    'message': '权限不足',
                    'data': None,
                    'timestamp': datetime.now().isoformat()
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def admin_required(f):
    """需要管理员权限的装饰器"""
    return role_required('admin')(f)

def optional_auth(f):
    """可选认证的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 尝试从请求头获取token
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
                is_valid, result = verify_token(token)
                
                if is_valid:
                    g.user_id = result.get('user_id')
                    g.username = result.get('username')
                    g.role = result.get('role', 'user')
                else:
                    g.user_id = None
                    g.username = None
                    g.role = None
            except Exception as e:
                logger.warning(f"Token解析失败: {str(e)}")
                g.user_id = None
                g.username = None
                g.role = None
        else:
            g.user_id = None
            g.username = None
            g.role = None
        
        return f(*args, **kwargs)
    
    return decorated_function

# ==================== 权限检查函数 ====================

def check_permission(user_role: str, required_role: str) -> bool:
    """检查用户权限"""
    # 管理员拥有所有权限
    if user_role == 'admin':
        return True
    
    # 普通用户只能访问普通用户权限
    if user_role == 'user' and required_role == 'user':
        return True
    
    return False

def get_current_user() -> dict:
    """获取当前登录用户信息"""
    return {
        'user_id': getattr(g, 'user_id', None),
        'username': getattr(g, 'username', None),
        'role': getattr(g, 'role', None)
    }

def is_authenticated() -> bool:
    """检查用户是否已认证"""
    return hasattr(g, 'user_id') and g.user_id is not None

def is_admin() -> bool:
    """检查用户是否是管理员"""
    return hasattr(g, 'role') and g.role == 'admin'

# ==================== Token刷新 ====================

def refresh_access_token(refresh_token: str) -> tuple[bool, dict]:
    """刷新访问令牌"""
    try:
        # 解码刷新令牌
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 检查令牌类型
        if payload.get('type') != 'refresh':
            return False, {'error': 'token_type_error', 'message': '令牌类型错误'}
        
        # 生成新的访问令牌
        user_id = payload.get('user_id')
        username = payload.get('username')
        role = payload.get('role', 'user')
        
        new_access_token = generate_access_token(user_id, username, role)
        
        return True, {
            'access_token': new_access_token,
            'token_type': 'Bearer',
            'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    except jwt.ExpiredSignatureError:
        return False, {'error': 'token_expired', 'message': '刷新令牌已过期'}
    except jwt.InvalidTokenError as e:
        return False, {'error': 'token_invalid', 'message': f'刷新令牌无效: {str(e)}'}
