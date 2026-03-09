#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
JWT认证中间件
统一使用JWT作为认证机制，逐步移除Session依赖
"""

from functools import wraps
from flask import request, jsonify
from jwt_manager import get_current_user_from_token

def jwt_required(f):
    """
    JWT认证装饰器
    替代原来的 @login_required
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # 获取Token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'error': '未提供认证Token'}), 401
            
            token = auth_header.split(' ')[1]
            
            # 验证Token
            current_user = get_current_user_from_token(token)
            if not current_user:
                return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
            
            # 将用户信息添加到request对象，方便后续使用
            request.current_user = current_user
            
            return f(*args, **kwargs)
        except Exception as e:
            print(f"JWT认证过程中发生错误: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '认证失败'}), 401
    
    return decorated_function

def get_current_user():
    """
    获取当前用户信息
    在视图函数中使用: user = get_current_user()
    """
    if hasattr(request, 'current_user'):
        return request.current_user
    return None

def require_jwt_auth():
    """
    强制要求JWT认证
    用于需要严格JWT认证的场景
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'error': '未提供认证Token'}), 401
            
            token = auth_header.split(' ')[1]
            current_user = get_current_user_from_token(token)
            if not current_user:
                return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
            
            request.current_user = current_user
            return f(*args, **kwargs)
        return decorated_function
    return decorator
