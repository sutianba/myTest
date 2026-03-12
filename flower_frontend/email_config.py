#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""邮箱配置和验证邮件发送功能"""

import os
import secrets
import time
import uuid
import smtplib
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EmailSender')

# 导入配置管理
from config import config

# 邮箱配置（支持环境变量和配置文件）
EMAIL_HOST = config.SMTP_SERVER
EMAIL_PORT = config.SMTP_PORT
EMAIL_FROM = config.SMTP_USER
EMAIL_PASSWORD = config.SMTP_PASSWORD
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

# 验证链接基础URL
VERIFY_URL_BASE = os.environ.get('VERIFY_URL_BASE', 'http://localhost:5000/api/verify-email')

# 邮件发送配置
MAX_RETRY_COUNT = int(os.environ.get('MAX_RETRY_COUNT', 3))
RETRY_DELAY = int(os.environ.get('RETRY_DELAY', 2))  # 秒
MIN_SEND_INTERVAL = int(os.environ.get('MIN_SEND_INTERVAL', 60))  # 秒，防止频繁发送

# Token存储（实际生产环境应使用Redis等缓存）
email_verify_tokens = {}

# 发送时间记录（用于防止频繁发送）
email_send_times = {}

# 开发/生产环境区分
DEBUG_MODE = os.environ.get('DEBUG_MODE', 'False').lower() == 'true'

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

def is_allowed_to_send(email):
    """检查是否允许发送邮件（防止频繁发送）"""
    current_time = time.time()
    
    if email in email_send_times:
        last_send_time = email_send_times[email]
        if current_time - last_send_time < MIN_SEND_INTERVAL:
            return False, f'请等待{MIN_SEND_INTERVAL}秒后再发送'
    
    return True, None

def update_send_time(email):
    """更新邮件发送时间"""
    email_send_times[email] = time.time()

def clear_send_time(email):
    """清除发送时间记录"""
    if email in email_send_times:
        del email_send_times[email]

def create_html_content(username, verify_url):
    """创建HTML格式的邮件内容"""
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>邮箱验证 - 花卉识别系统</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- 头部 -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 32px;">花卉识别系统</h1>
            <p style="color: rgba(255, 255, 255, 0.9); margin: 10px 0 0;">欢迎加入我们！</p>
        </div>
        
        <!-- 主体内容 -->
        <div style="padding: 40px 30px;">
            <h2 style="color: #333; margin-top: 0;">尊敬的 {username}，您好！</h2>
            
            <p style="color: #666; line-height: 1.8; margin: 20px 0;">
                感谢您注册花卉识别系统！请点击下面的按钮完成邮箱验证，以激活您的账户并享受完整功能。
            </p>
            
            <!-- 验证按钮 -->
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verify_url}" 
                   style="display: inline-block; padding: 15px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; text-decoration: none; border-radius: 25px; font-size: 16px; 
                          font-weight: bold; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                          transition: all 0.3s; margin: 10px;"
                   onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(102, 126, 234, 0.6)';"
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(102, 126, 234, 0.4)';">
                    立即验证邮箱
                </a>
            </div>
            
            <p style="color: #999; font-size: 14px; margin: 10px 0;">
                如果按钮无法点击，请复制以下链接到浏览器中打开：
            </p>
            
            <p style="color: #666; font-size: 14px; margin: 10px 0; word-break: break-all;
                      background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef;">
                {verify_url}
            </p>
            
            <!-- 说明 -->
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #667eea;">
                <h3 style="color: #333; margin: 0 0 15px 0; font-size: 16px;">📌 注意事项</h3>
                <ul style="color: #666; line-height: 1.8; margin: 0; padding-left: 20px; font-size: 14px;">
                    <li>此验证链接24小时内有效</li>
                    <li>请确保您输入的邮箱地址正确</li>
                    <li>如果未收到邮件，请检查垃圾邮件文件夹</li>
                    <li>如需重新发送验证邮件，请登录后在个人中心操作</li>
                </ul>
            </div>
            
            <p style="color: #666; line-height: 1.8; margin: 20px 0;">
                如果您没有注册本账号，请忽略此邮件。您的账户将不会被创建。
            </p>
        </div>
        
        <!-- 底部 -->
        <div style="background-color: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e9ecef;">
            <p style="color: #999; font-size: 14px; margin: 10px 0;">
                © 2024 花卉识别系统. All rights reserved.
            </p>
            <p style="color: #999; font-size: 12px; margin: 10px 0;">
                此为系统邮件，请勿直接回复
            </p>
        </div>
    </div>
</body>
</html>
"""
    return html_content

def create_text_content(username, verify_url):
    """创建纯文本格式的邮件内容"""
    text_content = f"""您好，{username}！

欢迎注册花卉识别系统！请点击以下链接完成邮箱验证：

{verify_url}

该链接24小时内有效。如果链接无法点击，请复制以下链接到浏览器中打开：

{verify_url}

注意事项：
- 此验证链接24小时内有效
- 请确保您输入的邮箱地址正确
- 如果未收到邮件，请检查垃圾邮件文件夹

如果您没有注册本账号，请忽略此邮件。

—— 花卉识别系统团队
"""
    return text_content

def send_email_with_retry(to_email, subject, html_content, text_content, retry_count=0):
    """发送邮件（带重试机制）"""
    try:
        # 创建邮件对象
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = formataddr(('花卉识别系统', EMAIL_FROM))
        msg['To'] = to_email
        
        # 添加纯文本内容
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(part1)
        
        # 添加HTML内容
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part2)
        
        # 连接SMTP服务器
        if EMAIL_USE_SSL:
            server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, timeout=30)
        else:
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=30)
        
        server.set_debuglevel(0)
        
        # TLS加密
        if EMAIL_USE_TLS and not EMAIL_USE_SSL:
            server.starttls()
        
        # 登录
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        
        # 发送邮件
        server.sendmail(EMAIL_FROM, to_email, msg.as_string())
        
        # 关闭连接
        server.quit()
        
        logger.info(f"邮件发送成功: {to_email}")
        
        # 清除发送时间记录
        clear_send_time(to_email)
        
        return {'success': True, 'message': '邮件发送成功'}
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP认证失败: {str(e)} - 收件人: {to_email}")
        return {'success': False, 'error': 'SMTP认证失败，请检查邮箱和授权码'}
        
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"收件人被拒绝: {str(e)} - 收件人: {to_email}")
        return {'success': False, 'error': '收件人地址无效'}
        
    except smtplib.SMTPException as e:
        logger.error(f"SMTP发送失败 (尝试 {retry_count + 1}/{MAX_RETRY_COUNT}): {str(e)} - 收件人: {to_email}")
        
        if retry_count < MAX_RETRY_COUNT - 1:
            # 等待后重试
            time.sleep(RETRY_DELAY * (retry_count + 1))
            return send_email_with_retry(to_email, subject, html_content, text_content, retry_count + 1)
        else:
            return {'success': False, 'error': f'邮件发送失败: {str(e)}'}
            
    except Exception as e:
        logger.error(f"发送邮件时发生未知错误 (尝试 {retry_count + 1}/{MAX_RETRY_COUNT}): {str(e)} - 收件人: {to_email}")
        
        if retry_count < MAX_RETRY_COUNT - 1:
            time.sleep(RETRY_DELAY * (retry_count + 1))
            return send_email_with_retry(to_email, subject, html_content, text_content, retry_count + 1)
        else:
            return {'success': False, 'error': f'邮件发送失败: {str(e)}'}

def send_verification_email(email, username, token):
    """发送验证邮件"""
    try:
        # 检查是否允许发送
        allowed, error_msg = is_allowed_to_send(email)
        if not allowed:
            logger.warning(f"发送频率过高，拒绝发送: {email}")
            return {'success': False, 'error': error_msg}
        
        verify_url = generate_verify_url(token)
        
        # 构建邮件内容
        subject = '花卉识别系统 - 邮箱验证'
        html_content = create_html_content(username, verify_url)
        text_content = create_text_content(username, verify_url)
        
        # 开发环境模拟
        if DEBUG_MODE:
            logger.info(f"=== 开发环境：模拟发送邮件 ===")
            logger.info(f"收件人: {email}")
            logger.info(f"主题: {subject}")
            logger.info(f"验证链接: {verify_url}")
            logger.info(f"==================")
            
            # 清除发送时间记录（开发环境不限制频率）
            clear_send_time(email)
            
            return {'success': True, 'message': '邮件已模拟发送（开发环境）'}
        
        # 更新发送时间
        update_send_time(email)
        
        # 发送邮件（带重试）
        result = send_email_with_retry(email, subject, html_content, text_content)
        
        if result['success']:
            logger.info(f"验证邮件已发送: {email}")
        else:
            logger.error(f"邮件发送失败: {email} - {result.get('error', '未知错误')}")
        
        return result
        
    except Exception as e:
        logger.error(f"发送验证邮件时发生异常: {str(e)} - 收件人: {email}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': f'发送失败: {str(e)}'}

def clear_token(token):
    """清除token"""
    if token in email_verify_tokens:
        del email_verify_tokens[token]
