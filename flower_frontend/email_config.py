#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""邮箱配置和验证邮件发送功能"""

import os
import secrets
import time
import uuid
from datetime import datetime, timedelta

# 邮箱配置
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.163.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'your_email@163.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'your_email_password')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

# 验证链接基础URL
VERIFY_URL_BASE = os.environ.get('VERIFY_URL_BASE', 'http://localhost:5000/api/verify-email')

# Token存储（实际生产环境应使用Redis等缓存）
email_verify_tokens = {}

def generate_verification_token(user_id, email):
    """生成邮箱验证token"""
    token = secrets.token_urlsafe(32)
    
    # 存储token信息
    email_verify_tokens[token] = {
        'user_id': user_id,
        'email': email,
        'created_at': time.time(),
        'expires_at': time.time() + 86400,  # 24小时有效
        'used': False
    }
    
    return token

def verify_token(token):
    """验证token是否有效"""
    if token not in email_verify_tokens:
        return {'success': False, 'error': '验证链接无效或已过期'}
    
    token_data = email_verify_tokens[token]
    
    # 检查是否已使用
    if token_data['used']:
        return {'success': False, 'error': '验证链接已被使用'}
    
    # 检查是否过期
    if time.time() > token_data['expires_at']:
        del email_verify_tokens[token]
        return {'success': False, 'error': '验证链接已过期'}
    
    return {'success': True, 'data': token_data}

def mark_token_as_used(token):
    """标记token为已使用"""
    if token in email_verify_tokens:
        email_verify_tokens[token]['used'] = True
        email_verify_tokens[token]['used_at'] = time.time()

def generate_verify_url(token):
    """生成验证链接"""
    return f"{VERIFY_URL_BASE}?token={token}"

def send_verification_email(email, username, token):
    """发送验证邮件"""
    try:
        verify_url = generate_verify_url(token)
        
        # 构建邮件内容
        subject = '花卉识别系统 - 邮箱验证'
        content = f"""您好，{username}！

欢迎注册花卉识别系统！请点击以下链接完成邮箱验证：

{verify_url}

该链接24小时内有效。如果链接无法点击，请复制以下链接到浏览器中打开：

{verify_url}

如果您没有注册本账号，请忽略此邮件。

—— 花卉识别系统团队
"""
        
        # 这里需要实现实际的邮件发送逻辑
        # 由于当前环境限制，这里仅打印日志
        print(f"=== 邮件发送模拟 ===")
        print(f"收件人: {email}")
        print(f"主题: {subject}")
        print(f"内容: {content}")
        print(f"==================")
        
        return {'success': True, 'message': '验证邮件已发送'}
        
    except Exception as e:
        print(f"发送验证邮件失败: {str(e)}")
        return {'success': False, 'error': f'发送失败: {str(e)}'}

def clear_token(token):
    """清除token"""
    if token in email_verify_tokens:
        del email_verify_tokens[token]
