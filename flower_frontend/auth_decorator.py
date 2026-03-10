#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""认证装饰器 - 统一处理Token验证和权限检查"""

import functools
from flask import request, jsonify
from jwt_manager import get_current_user_from_token, verify_token as verify_jwt_token


def require_auth(f):
    """要求认证的装饰器
    
    使用示例：
        @app.route('/api/protected')
        @require_auth
        def protected_route():
            return jsonify({'success': True, 'user': g.current_user})
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取Token
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'success': False,
                'error': '未提供认证Token'
            }), 401
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Token格式错误，应为Bearer Token'
            }), 401
        
        # 提取Token
        token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Token不能为空'
            }), 401
        
        # 验证Token
        try:
            verify_result = verify_jwt_token(token)
            
            if not verify_result['success']:
                return jsonify({
                    'success': False,
                    'error': verify_result.get('error', 'Token无效或已过期')
                }), 401
            
            # 将用户信息存入flask.g，供后续使用
            from flask import g
            g.current_user = verify_result['data']
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Token验证失败: {str(e)}'
            }), 401
    
    return decorated_function


def require_admin(f):
    """要求管理员权限的装饰器
    
    使用示例：
        @app.route('/api/admin/users')
        @require_admin
        def admin_route():
            return jsonify({'success': True})
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # 先进行认证
        auth_result = require_auth(lambda: None)(*args, **kwargs)
        
        # 如果认证失败，直接返回
        if isinstance(auth_result, tuple) and len(auth_result) == 2:
            return auth_result
        
        # 检查是否为管理员
        from flask import g
        if g.current_user.get('role') != 'admin':
            return jsonify({
                'success': False,
                'error': '需要管理员权限'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f):
    """可选认证的装饰器（允许未认证访问，但如果有Token则验证）
    
    使用示例：
        @app.route('/api/public')
        @optional_auth
        def public_route():
            if hasattr(g, 'current_user'):
                return jsonify({'user': g.current_user})
            return jsonify({'message': '未登录'})
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # 尝试获取Token
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            if token:
                try:
                    verify_result = verify_jwt_token(token)
                    
                    if verify_result['success']:
                        from flask import g
                        g.current_user = verify_result['data']
                except Exception:
                    pass
        
        return f(*args, **kwargs)
    
    return decorated_function
