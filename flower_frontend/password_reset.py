#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""找回密码邮件发送功能"""

import os
import time
import secrets
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
        logging.FileHandler('password_reset.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PasswordReset')

# 邮箱配置（支持环境变量和配置文件）
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.163.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'your_email@163.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'your_email_password')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'

# 重置链接基础URL
RESET_URL_BASE = os.environ.get('RESET_URL_BASE', 'http://localhost:5000')

# 邮件发送配置
MAX_RETRY_COUNT = int(os.environ.get('MAX_RETRY_COUNT', 3))
RETRY_DELAY = int(os.environ.get('RETRY_DELAY', 2))  # 秒
MIN_SEND_INTERVAL = int(os.environ.get('MIN_SEND_INTERVAL', 60))  # 秒，防止重复发送

# Token存储（实际生产环境应使用Redis等缓存）
password_reset_tokens = {}

# 发送时间记录（用于防止频繁发送）
password_reset_send_times = {}

# 开发/生产环境区分
DEBUG_MODE = os.environ.get('DEBUG_MODE', 'False').lower() == 'true'


def generate_reset_token(user_id: int, email: str) -> str:
    """生成密码重置token"""
    token = secrets.token_urlsafe(32)
    
    # 存储token信息
    password_reset_tokens[token] = {
        'user_id': user_id,
        'email': email,
        'created_at': time.time(),
        'expires_at': time.time() + 3600,  # 1小时有效
        'used': False
    }
    
    return token


def verify_reset_token(token: str) -> dict:
    """验证token是否有效"""
    if token not in password_reset_tokens:
        return {'success': False, 'error': '验证链接无效或已过期'}
    
    token_data = password_reset_tokens[token]
    
    # 检查是否已使用
    if token_data['used']:
        return {'success': False, 'error': '验证链接已被使用'}
    
    # 检查是否过期
    if time.time() > token_data['expires_at']:
        del password_reset_tokens[token]
        return {'success': False, 'error': '验证链接已过期'}
    
    return {'success': True, 'data': token_data}


def mark_reset_token_as_used(token: str):
    """标记token为已使用"""
    if token in password_reset_tokens:
        password_reset_tokens[token]['used'] = True
        password_reset_tokens[token]['used_at'] = time.time()


def generate_reset_url(token: str) -> str:
    """生成重置链接"""
    return f"{RESET_URL_BASE}/reset-password?token={token}"


def is_allowed_to_send(email: str) -> tuple:
    """检查是否允许发送邮件（防止频繁发送）"""
    current_time = time.time()
    
    if email in password_reset_send_times:
        last_send_time = password_reset_send_times[email]
        if current_time - last_send_time < MIN_SEND_INTERVAL:
            return False, f'请等待{MIN_SEND_INTERVAL}秒后再发送'
    
    return True, None


def update_send_time(email: str):
    """更新邮件发送时间"""
    password_reset_send_times[email] = time.time()


def clear_send_time(email: str):
    """清除发送时间记录"""
    if email in password_reset_send_times:
        del password_reset_send_times[email]


def create_html_content(username: str, reset_url: str) -> str:
    """创建HTML格式的邮件内容"""
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>重置密码 - 花卉识别系统</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- 头部 -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 32px;">花卉识别系统</h1>
            <p style="color: rgba(255, 255, 255, 0.9); margin: 10px 0 0;">密码重置请求</p>
        </div>
        
        <!-- 主体内容 -->
        <div style="padding: 40px 30px;">
            <h2 style="color: #333; margin-top: 0;">尊敬的 {username}，您好！</h2>
            
            <p style="color: #666; line-height: 1.8; margin: 20px 0;">
                我们收到了您重置密码的请求。请点击下面的按钮重置您的密码。
            </p>
            
            <!-- 重置按钮 -->
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="display: inline-block; padding: 15px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; text-decoration: none; border-radius: 25px; font-size: 16px; 
                          font-weight: bold; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                          transition: all 0.3s; margin: 10px;"
                   onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(102, 126, 234, 0.6)';"
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(102, 126, 234, 0.4)';">
                    重置密码
                </a>
            </div>
            
            <p style="color: #999; font-size: 14px; margin: 10px 0;">
                如果按钮无法点击，请复制以下链接到浏览器中打开：
            </p>
            
            <p style="color: #666; font-size: 14px; margin: 10px 0; word-break: break-all;
                      background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef;">
                {reset_url}
            </p>
            
            <!-- 说明 -->
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #667eea;">
                <h3 style="color: #333; margin: 0 0 15px 0; font-size: 16px;">📌 注意事项</h3>
                <ul style="color: #666; line-height: 1.8; margin: 0; padding-left: 20px; font-size: 14px;">
                    <li>此重置链接1小时内有效</li>
                    <li>请确保您输入的邮箱地址正确</li>
                    <li>如果未收到邮件，请检查垃圾邮件文件夹</li>
                    <li>如果您没有申请重置密码，请忽略此邮件</li>
                </ul>
            </div>
            
            <p style="color: #666; line-height: 1.8; margin: 20px 0;">
                为了您的账户安全，重置密码后建议立即登录并修改密码。
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


def create_text_content(username: str, reset_url: str) -> str:
    """创建纯文本格式的邮件内容"""
    text_content = f"""您好，{username}！

我们收到了您重置密码的请求。请点击以下链接重置您的密码：

{reset_url}

该链接1小时内有效。如果链接无法点击，请复制以下链接到浏览器中打开：

{reset_url}

注意事项：
- 此重置链接1小时内有效
- 请确保您输入的邮箱地址正确
- 如果未收到邮件，请检查垃圾邮件文件夹
- 如果您没有申请重置密码，请忽略此邮件

为了您的账户安全，重置密码后建议立即登录并修改密码。

—— 花卉识别系统团队
"""
    return text_content


def send_reset_email(to_email: str, username: str, token: str, retry_count: int = 0) -> dict:
    """发送重置密码邮件（带重试机制）"""
    try:
        # 创建邮件对象
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header('花卉识别系统 - 重置密码', 'utf-8')
        msg['From'] = formataddr(('花卉识别系统', EMAIL_FROM))
        msg['To'] = to_email
        
        # 添加纯文本内容
        reset_url = generate_reset_url(token)
        part1 = MIMEText(create_text_content(username, reset_url), 'plain', 'utf-8')
        msg.attach(part1)
        
        # 添加HTML内容
        part2 = MIMEText(create_html_content(username, reset_url), 'html', 'utf-8')
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
        
        logger.info(f"重置密码邮件发送成功: {to_email}")
        
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
            return send_reset_email(to_email, username, token, retry_count + 1)
        else:
            return {'success': False, 'error': f'邮件发送失败: {str(e)}'}
            
    except Exception as e:
        logger.error(f"发送邮件时发生未知错误 (尝试 {retry_count + 1}/{MAX_RETRY_COUNT}): {str(e)} - 收件人: {to_email}")
        
        if retry_count < MAX_RETRY_COUNT - 1:
            time.sleep(RETRY_DELAY * (retry_count + 1))
            return send_reset_email(to_email, username, token, retry_count + 1)
        else:
            return {'success': False, 'error': f'邮件发送失败: {str(e)}'}


def send_password_reset_email(email: str, username: str) -> dict:
    """发送密码重置邮件"""
    try:
        # 检查是否允许发送
        allowed, error_msg = is_allowed_to_send(email)
        if not allowed:
            logger.warning(f"发送频率过高，拒绝发送: {email}")
            return {'success': False, 'error': error_msg}
        
        # 生成token
        token = generate_reset_token(0, email)  # user_id会在验证时获取
        
        reset_url = generate_reset_url(token)
        
        # 构建邮件内容
        subject = '花卉识别系统 - 重置密码'
        html_content = create_html_content(username, reset_url)
        text_content = create_text_content(username, reset_url)
        
        # 开发环境模拟
        if DEBUG_MODE:
            logger.info(f"=== 开发环境：模拟发送邮件 ===")
            logger.info(f"收件人: {email}")
            logger.info(f"主题: {subject}")
            logger.info(f"重置链接: {reset_url}")
            logger.info(f"==================")
            
            # 清除发送时间记录（开发环境不限制频率）
            clear_send_time(email)
            
            return {'success': True, 'message': '邮件已模拟发送（开发环境）'}
        
        # 更新发送时间
        update_send_time(email)
        
        # 发送邮件（带重试）
        result = send_reset_email(email, username, token)
        
        if result['success']:
            logger.info(f"重置密码邮件已发送: {email}")
        else:
            logger.error(f"邮件发送失败: {email} - {result.get('error', '未知错误')}")
        
        return result
        
    except Exception as e:
        logger.error(f"发送重置密码邮件时发生异常: {str(e)} - 收件人: {email}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': f'发送失败: {str(e)}'}


def clear_token(token: str):
    """清除token"""
    if token in password_reset_tokens:
        del password_reset_tokens[token]
