#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# 你可以在 http://127.0.0.1:5000 网站进行查看
import os
import sys
import base64
import io
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor

# imghdr 在 Python 3.13 中已被移除，使用替代方案
def get_image_type(filepath):
    """检测图片类型"""
    try:
        from PIL import Image
        with Image.open(filepath) as img:
            return img.format.lower() if img.format else None
    except:
        # 通过文件头检测
        with open(filepath, 'rb') as f:
            header = f.read(32)
            if header.startswith(b'\xff\xd8'):
                return 'jpeg'
            elif header.startswith(b'\x89PNG'):
                return 'png'
            elif header.startswith(b'RIFF') and header[8:12] == b'WEBP':
                return 'webp'
            elif header.startswith(b'GIF'):
                return 'gif'
        return None
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, make_response
from flask_cors import CORS
import hashlib
import secrets
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入邮箱验证功能
from email_config import generate_verification_token, send_verification_email, verify_token, mark_token_as_used

# 导入密码哈希功能
from password_hash import hash_password, verify_password

# 导入安全防护功能
from security import (
    record_login_failure, 
    record_login_success, 
    check_login_failure_limit,
    check_login_cooldown,
    get_login_failures_count,
    clear_login_failures
)

# 导入JWT管理功能
from jwt_manager import (
    generate_access_token,
    generate_refresh_token,
    verify_token as verify_jwt_token,
    add_to_blacklist,
    invalidate_user_tokens,
    refresh_access_token,
    get_current_user_from_token,
    ACCESS_TOKEN_EXPIRY,
    REFRESH_TOKEN_EXPIRY
)

# 导入验证码功能
from captcha import generate_captcha, verify_captcha, clear_captcha

# 导入安全上传功能
from upload_manager import (
    validate_upload,
    save_upload_file,
    cleanup_failed_upload,
    get_upload_dir,
    MAX_FILE_SIZE
)

# 导入个人账户功能
from account_manager import (
    get_user_profile, update_user_profile, upload_avatar,
    generate_password_reset_token, verify_password_reset_token, mark_password_reset_token_as_used,
    reset_user_password, change_user_password,
    generate_email_change_token, verify_email_change_token, mark_email_change_token_as_used,
    change_user_email, delete_user_account, ban_user, unban_user,
    log_user_action, get_user_action_logs, check_user_banned, get_user_info
)

from password_reset import (
    generate_reset_token, verify_reset_token, mark_reset_token_as_used,
    send_password_reset_email
)

from email_change import (
    generate_change_token, verify_change_token, mark_change_token_as_used,
    send_email_change_email
)

from account_api import account_api

# 导入管理员后台功能
from admin_api import admin_api

# 导入图片EXIF信息提取所需模块
from PIL import Image # 用于打开和处理图片
from PIL.ExifTags import TAGS # 用于将EXIF标签ID映射到标签名称
import exifread # 用于提取图片EXIF信息
from geopy.geocoders import Nominatim # 用于根据经纬度获取地址信息
from geopy.exc import GeocoderTimedOut, GeocoderServiceError # 用于处理地理编码超时和服务错误
import time # 用于处理时间相关操作

app = Flask(__name__)
CORS(app, 
    supports_credentials=True,
    origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
    allow_headers=['Content-Type', 'Authorization'],
    methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
)  # 启用CORS以允许前端访问，并支持会话cookie

# 设置密钥用于JWT认证
app.secret_key = secrets.token_hex(16)

# 设置JWT Secret Key
from jwt_manager import set_secret_key
set_secret_key(app.secret_key)

# 配置线程池用于异步处理
thread_pool = ThreadPoolExecutor(max_workers=4)  # 根据系统CPU核心数调整

# 定义静态文件目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # 项目根目录

# 使用MySQL数据库
import sys
sys.path.append(BASE_DIR)
from db_config import get_db_connection, init_mysql_db

# 初始化数据库
# 启用MySQL数据库初始化功能
init_mysql_db()

# 路由保护装饰器
def login_required(f):
    """检查用户是否已登录的装饰器（使用JWT认证）"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取Token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': '未提供认证Token'}), 401
        
        token = auth_header.split(' ')[1]
        
        # 验证Token
        current_user = get_current_user_from_token(token)
        if not current_user:
            return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
        
        # 将用户信息添加到kwargs
        kwargs['current_user'] = current_user
        return f(*args, **kwargs)
    return decorated_function

# ==================== 邮箱注册相关API ====================

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册API接口（需要邮箱验证）"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        if not username or not password or not email:
            return jsonify({'success': False, 'error': '用户名、密码和邮箱不能为空'})
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': '密码长度不能少于6位'})

        # 检查用户名是否已存在
        connection = get_db_connection()
        cursor = connection.cursor()
        
        check_query = "SELECT * FROM users WHERE username = %s OR email = %s"
        cursor.execute(check_query, (username, email))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '用户名或邮箱已存在'})
        
        # 密码哈希处理
        password_hash = hash_password(password)
        if not password_hash:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '密码加密失败'})
        
        # 创建待验证用户记录
        insert_query = """
            INSERT INTO users (username, email, password_hash, status) 
            VALUES (%s, %s, %s, 'unverified')
        """
        cursor.execute(insert_query, (username, email, password_hash))
        user_id = cursor.lastrowid
        connection.commit()
        
        # 生成验证token
        token = generate_verification_token(user_id, email)
        
        # 发送验证邮件
        result = send_verification_email(email, username, token)
        
        cursor.close()
        connection.close()
        
        if result['success']:
            return jsonify({
                'success': True, 
                'message': '注册成功！请前往邮箱完成验证',
                'email': email
            })
        else:
            return jsonify({
                'success': False, 
                'error': result.get('error', '注册成功但邮件发送失败，请重试')
            })
            
    except Exception as e:
        print(f"注册过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '注册失败，请稍后重试'})

@app.route('/api/verify-email', methods=['GET'])
def verify_email():
    """邮箱验证API"""
    try:
        token = request.args.get('token')
        
        if not token:
            return jsonify({'success': False, 'error': '验证链接无效'})
        
        # 验证token
        verify_result = verify_token(token)
        
        if not verify_result['success']:
            return jsonify({'success': False, 'error': verify_result['error']})
        
        token_data = verify_result['data']
        user_id = token_data['user_id']
        
        # 更新用户状态为已激活
        connection = get_db_connection()
        cursor = connection.cursor()
        
        update_query = "UPDATE users SET status = 'active' WHERE id = %s"
        cursor.execute(update_query, (user_id,))
        connection.commit()
        
        # 标记token为已使用
        mark_token_as_used(token)
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True, 
            'message': '邮箱验证成功！账号已激活',
            'redirect': '/login.html'
        })
        
    except Exception as e:
        print(f"邮箱验证过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '验证失败，请重试'})

@app.route('/api/resend_verification', methods=['POST'])
def resend_verification():
    """重新发送验证邮件"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': '邮箱不能为空'})
        
        # 查找用户
        connection = get_db_connection()
        cursor = connection.cursor()
        
        check_query = "SELECT * FROM users WHERE email = %s AND status = 'unverified'"
        cursor.execute(check_query, (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '未找到待验证的账号'})
        
        user_id = user['id']
        username = user['username']
        
        # 生成新的验证token
        token = generate_verification_token(user_id, email)
        
        # 发送验证邮件
        result = send_verification_email(email, username, token)
        
        cursor.close()
        connection.close()
        
        if result['success']:
            return jsonify({'success': True, 'message': '验证邮件已重新发送'})
        else:
            return jsonify({'success': False, 'error': result.get('error', '邮件发送失败')})
            
    except Exception as e:
        print(f"重新发送验证邮件过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '发送失败，请稍后重试'})

# ==================== 原有登录API ====================

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录API接口（集成安全防护）"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        captcha_id = data.get('captcha_id')
        captcha_text = data.get('captcha_text')
        
        # 获取客户端IP地址
        ip_address = request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown')
        
        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'})

        # 验证图形验证码
        if captcha_id and captcha_text:
            success, message = verify_captcha(captcha_id, captcha_text)
            if not success:
                return jsonify({'success': False, 'error': message})
        
        # 检查登录失败限制
        allowed, error_msg = check_login_failure_limit(username, ip_address)
        if not allowed:
            return jsonify({'success': False, 'error': error_msg})
        
        # 检查登录冷却时间
        allowed, error_msg = check_login_cooldown(username, ip_address)
        if not allowed:
            return jsonify({'success': False, 'error': error_msg})

        connection = get_db_connection()
        cursor = connection.cursor()
        
        check_query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(check_query, (username,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            connection.close()
            record_login_failure(username, ip_address, '用户名不存在')
            return jsonify({'success': False, 'error': '用户名或密码错误'})
        
        # 检查用户状态
        if user['status'] != 'active':
            cursor.close()
            connection.close()
            record_login_failure(username, ip_address, '账号未激活')
            return jsonify({'success': False, 'error': '账号未激活，请先验证邮箱'})
        
        # 验证密码
        if not verify_password(password, user['password_hash']):
            cursor.close()
            connection.close()
            record_login_failure(username, ip_address, '密码错误')
            return jsonify({'success': False, 'error': '用户名或密码错误'})
        
        # 登录成功
        record_login_success(username, ip_address)
        
        # 生成JWT Token（Access Token + Refresh Token）
        access_token = generate_access_token(user['id'], user['username'], user['role'])
        refresh_token = generate_refresh_token(user['id'], user['username'])
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': ACCESS_TOKEN_EXPIRY,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
        })
        
    except Exception as e:
        print(f"登录过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '登录失败，请稍后重试'})

@app.route('/api/captcha', methods=['GET'])
def get_captcha():
    """获取图形验证码"""
    try:
        captcha_id, base64_str = generate_captcha()
        
        return jsonify({
            'success': True,
            'captcha_id': captcha_id,
            'image': f'data:image/png;base64,{base64_str}'
        })
    except Exception as e:
        print(f"获取验证码过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '获取验证码失败'})

@app.route('/api/verify-captcha', methods=['POST'])
def verify_captcha_api():
    """验证图形验证码"""
    try:
        data = request.get_json()
        captcha_id = data.get('captcha_id')
        captcha_text = data.get('captcha_text')
        
        if not captcha_id or not captcha_text:
            return jsonify({'success': False, 'error': '缺少验证码参数'})
        
        success, message = verify_captcha(captcha_id, captcha_text)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message})
            
    except Exception as e:
        print(f"验证验证码过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '验证失败'})

@app.route('/api/logout', methods=['POST'])
def logout():
    """用户登出API接口（集成Token黑名单）"""
    try:
        # 获取Token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            # 将Token加入黑名单
            payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            expires_at = datetime.datetime.utcfromtimestamp(payload['exp'])
            add_to_blacklist(token, expires_at)
        
        # 登出成功，清除前端存储的Token
        return jsonify({'success': True, 'message': '已成功登出'})
    except Exception as e:
        print(f"登出过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '登出失败，请稍后重试'})

@app.route('/api/refresh_token', methods=['POST'])
def refresh_token_endpoint():
    """刷新Access Token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'success': False, 'error': '缺少Refresh Token'})
        
        success, new_access_token, error = refresh_access_token(refresh_token)
        
        if success:
            return jsonify({
                'success': True,
                'access_token': new_access_token,
                'token_type': 'Bearer',
                'expires_in': ACCESS_TOKEN_EXPIRY
            })
        else:
            return jsonify({'success': False, 'error': error})
            
    except Exception as e:
        print(f"刷新Token过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '刷新Token失败，请重新登录'})

@app.route('/api/user_info', methods=['GET'])
def get_user_info():
    """获取当前用户信息（使用JWT认证）"""
    try:
        # 获取Token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': '未提供认证Token'})
        
        token = auth_header.split(' ')[1]
        
        # 验证Token
        current_user = get_current_user_from_token(token)
        if not current_user:
            return jsonify({'success': False, 'error': 'Token无效或已过期'})
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        check_query = "SELECT id, username, email, role, created_at FROM users WHERE username = %s"
        cursor.execute(check_query, (current_user['username'],))
        user = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if not user:
            return jsonify({'success': False, 'error': '用户不存在'})
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'created_at': user['created_at'].isoformat() if user['created_at'] else None
            }
        })
        
    except Exception as e:
        print(f"获取用户信息过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '获取用户信息失败'})

@app.route('/api/check_auth', methods=['GET'])
def check_auth():
    """检查用户认证状态（使用JWT认证）"""
    try:
        # 获取Token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'authenticated': False, 'error': '未提供认证Token'})
        
        token = auth_header.split(' ')[1]
        
        # 验证Token
        current_user = get_current_user_from_token(token)
        if not current_user:
            return jsonify({'success': False, 'authenticated': False, 'error': 'Token无效或已过期'})
        
        return jsonify({
            'success': True,
            'authenticated': True,
            'user': {
                'username': current_user['username']
            }
        })
    except Exception as e:
        print(f"检查认证状态过程中发生错误: {type(e).__name__}: {str(e)}")
        return jsonify({
            'success': False,
            'authenticated': False,
            'error': '检查失败'
        })

# ==================== 图片上传相关API ====================

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_image():
    """上传图片（安全版本）"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有找到文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名不能为空'})
        
        if file:
            filename = file.filename
            upload_dir = os.path.join(BASE_DIR, 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            
            try:
                results = flower_model(filepath)
                predictions = results.pandas().xyxy[0].to_dict(orient='records')
                
                if predictions:
                    result_str = ', '.join([f"{row['name']} ({row['conf']:.2f})" for row in predictions])
                else:
                    result_str = '未识别到花卉'
                
                connection = get_db_connection()
                cursor = connection.cursor()
                
                insert_query = """
                    INSERT INTO recognition_results (user_id, image_path, result, confidence) 
                    VALUES (%s, %s, %s, %s)
                """
                confidence = predictions[0]['conf'] if predictions else 0
                cursor.execute(insert_query, (session['user_id'], filepath, result_str, confidence))
                connection.commit()
                
                cursor.close()
                connection.close()
                
                return jsonify({
                    'success': True,
                    'result': result_str,
                    'predictions': predictions
                })
            except Exception as e:
                print(f"识别过程中发生错误: {type(e).__name__}: {str(e)}")
                return jsonify({'success': False, 'error': f'识别失败: {str(e)}'})
        
    except Exception as e:
        print(f"上传过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '上传失败，请稍后重试'})

@app.route('/api/results', methods=['GET'])
@login_required
def get_results():
    """获取识别结果列表"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT id, image_path, result, confidence, created_at 
            FROM recognition_results 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 50
        """
        cursor.execute(query, (session['user_id'],))
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        formatted_results = []
        for r in results:
            formatted_results.append({
                'id': r['id'],
                'image_path': r['image_path'],
                'result': r['result'],
                'confidence': float(r['confidence']) if r['confidence'] else 0,
                'created_at': r['created_at'].isoformat() if r['created_at'] else None
            })
        
        return jsonify({
            'success': True,
            'results': formatted_results
        })
        
    except Exception as e:
        print(f"获取识别结果过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '获取结果失败'})

@app.route('/api/results/<int:result_id>', methods=['DELETE'])
@login_required
def delete_result(result_id):
    """删除识别结果"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        delete_query = "DELETE FROM recognition_results WHERE id = %s AND user_id = %s"
        cursor.execute(delete_query, (result_id, session['user_id']))
        connection.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        connection.close()
        
        if affected_rows > 0:
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'error': '删除失败或记录不存在'})
        
    except Exception as e:
        print(f"删除识别结果过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '删除失败，请稍后重试'})

@app.route('/api/recognize', methods=['POST'])
@login_required
def recognize():
    """识别图片API"""
    try:
        data = request.get_json()
        image_path = data.get('image_path')
        
        if not image_path:
            return jsonify({'success': False, 'error': '图片路径不能为空'})
        
        results = flower_model(image_path)
        predictions = results.pandas().xyxy[0].to_dict(orient='records')
        
        if predictions:
            result_str = ', '.join([f"{row['name']} ({row['conf']:.2f})" for row in predictions])
        else:
            result_str = '未识别到花卉'
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        insert_query = """
            INSERT INTO recognition_results (user_id, image_path, result, confidence) 
            VALUES (%s, %s, %s, %s)
        """
        confidence = predictions[0]['conf'] if predictions else 0
        cursor.execute(insert_query, (session['user_id'], image_path, result_str, confidence))
        connection.commit()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'result': result_str,
            'predictions': predictions
        })
        
    except Exception as e:
        print(f"识别过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '识别失败，请稍后重试'})

# ==================== 静态文件服务 ====================

@app.route('/')
def index():
    """首页路由"""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """静态文件服务"""
    return send_from_directory(BASE_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
