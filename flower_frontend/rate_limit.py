#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""请求频率限制装饰器 - 防止暴力破解和DDoS攻击"""

import functools
import time
from collections import defaultdict
from flask import request, jsonify, g


class RateLimiter:
    """请求频率限制器"""
    
    def __init__(self, max_requests=5, window_seconds=60):
        """
        初始化频率限制器
        
        Args:
            max_requests: 时间窗口内允许的最大请求数
            window_seconds: 时间窗口（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, key):
        """检查是否允许请求"""
        now = time.time()
        
        # 获取该key的请求记录
        user_requests = self.requests[key]
        
        # 移除时间窗口外的旧请求
        user_requests = [req_time for req_time in user_requests if now - req_time < self.window_seconds]
        
        # 检查是否超过限制
        if len(user_requests) >= self.max_requests:
            return False, f"请求过于频繁，请在{self.window_seconds}秒后重试"
        
        # 添加当前请求
        user_requests.append(now)
        self.requests[key] = user_requests
        
        return True, None


# 创建默认的频率限制器实例
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)  # 每分钟最多10次请求


def rate_limit(max_requests=10, window_seconds=60):
    """请求频率限制装饰器
    
    使用示例：
        @app.route('/api/login')
        @rate_limit(max_requests=5, window_seconds=60)
        def login_route():
            return jsonify({'success': True})
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取限制key（使用IP地址）
            ip_address = request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown')
            
            # 创建频率限制器实例
            limiter = RateLimiter(max_requests=max_requests, window_seconds=window_seconds)
            
            # 检查是否允许请求
            allowed, error_msg = limiter.is_allowed(ip_address)
            
            if not allowed:
                return jsonify({
                    'success': False,
                    'error': error_msg or '请求过于频繁，请稍后重试'
                }), 429  # HTTP 429 Too Many Requests
            
            # 添加响应头
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(max_requests)
                response.headers['X-RateLimit-Remaining'] = str(max_requests - len(limiter.requests[ip_address]))
                response.headers['X-RateLimit-Reset'] = str(int(time.time()) + window_seconds)
            
            return response
        
        return decorated_function
    
    return decorator


def rate_limit_by_user(max_requests=20, window_seconds=60):
    """基于用户的请求频率限制装饰器
    
    使用示例：
        @app.route('/api/user/profile')
        @rate_limit_by_user(max_requests=10, window_seconds=60)
        def profile_route():
            return jsonify({'success': True})
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取用户ID
            from flask import g
            user_id = getattr(g, 'current_user', {}).get('user_id', 'unknown')
            
            # 创建频率限制器实例
            limiter = RateLimiter(max_requests=max_requests, window_seconds=window_seconds)
            
            # 检查是否允许请求
            allowed, error_msg = limiter.is_allowed(user_id)
            
            if not allowed:
                return jsonify({
                    'success': False,
                    'error': error_msg or '操作过于频繁，请稍后重试'
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
