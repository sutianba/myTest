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

# 设置密钥用于会话管理
app.secret_key = secrets.token_hex(16)

# 配置session cookie以支持跨域
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

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

# 加载YOLOv5模型
import torch

# 使用正确路径加载模型
MODEL_PATH = os.path.join(PROJECT_ROOT, 'testflowers.pt')
print(f"正在加载模型: {MODEL_PATH}")

try:
    # 检查模型文件是否存在
    if not os.path.exists(MODEL_PATH):
        print(f"警告: 模型文件不存在: {MODEL_PATH}")
        print("将使用模拟模式运行")
        flower_model = None
    else:
        # 加载YOLOv5模型
        flower_model = torch.hub.load('ultralytics/yolov5', 'custom', path=MODEL_PATH, force_reload=True)
        flower_model.conf = 0.25  # 降低置信度阈值，保留更多检测结果
        flower_model.iou = 0.5   # 保持NMS IOU阈值
        print("成功加载YOLOv5花卉识别模型")
except Exception as e:
    print(f"无法加载YOLOv5模型: {e}")
    print("将使用模拟模式运行")
    flower_model = None

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
        
        # 清除session
        session.clear()
        
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
        if 'username' in session:
            return jsonify({
                'success': True,
                'authenticated': True,
                'user': {'username': session['username']}
            })
        else:
            return jsonify({
                'success': True,
                'authenticated': False
            })
    except Exception as e:
        print(f"检查认证状态过程中发生错误: {type(e).__name__}: {str(e)}")
        return jsonify({
            'success': False,
            'authenticated': False,
            'error': '检查失败'
        })

# ==================== 图片识别相关API ====================

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_image():
    """上传图片进行识别"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有找到文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名不能为空'})
        
        # 文件大小限制（10MB）
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        if file.content_length > MAX_FILE_SIZE:
            return jsonify({'success': False, 'error': '文件大小超过限制（最大10MB）'})
        
        # 文件类型白名单校验
        ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
        if '.' not in file.filename:
            return jsonify({'success': False, 'error': '无效的文件名'})
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({'success': False, 'error': '不支持的文件类型，只允许 jpg、jpeg、png、webp'})
        
        # 生成随机文件名，防止文件覆盖
        new_filename = f"{uuid.uuid4()}.{ext}"
        upload_dir = os.path.join(BASE_DIR, 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        filepath = os.path.join(upload_dir, new_filename)
        
        try:
            # 保存文件
            file.save(filepath)
            
            # MIME类型校验
            img_type = get_image_type(filepath)
            if not img_type:
                os.remove(filepath)
                return jsonify({'success': False, 'error': '无效的图片文件'})
            
            # 图片压缩
            try:
                from PIL import Image
                img = Image.open(filepath)
                # 压缩到最大800x800
                img.thumbnail((800, 800))
                img.save(filepath, optimize=True, quality=85)
            except Exception as e:
                print(f"图片压缩失败: {e}")
                # 压缩失败不影响识别，继续处理
            
            # 识别图片
            if flower_model is None:
                # 模拟模式：随机返回识别结果
                import random
                mock_plants = ['玫瑰', '郁金香', '薰衣草', '仙人掌', '绿萝']
                predictions = [{
                    'name': random.choice(mock_plants),
                    'conf': round(random.uniform(0.7, 0.95), 2),
                    'xmin': 10, 'ymin': 10, 'xmax': 100, 'ymax': 100
                }]
                result_str = f"{predictions[0]['name']} ({predictions[0]['conf']:.2f})"
            else:
                results = flower_model(filepath)
                predictions = results.pandas().xyxy[0].to_dict(orient='records')
                
                if predictions:
                    result_str = ', '.join([f"{row['name']} ({row['conf']:.2f})" for row in predictions])
                else:
                    result_str = '未识别到花卉'
            
            # 保存识别结果到数据库
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
            # 上传失败清理
            if os.path.exists(filepath):
                os.remove(filepath)
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

@app.route('/api/detect', methods=['POST'])
@login_required
def detect_flower():
    """花卉识别API接口（接收Base64图片）"""
    try:
        # 获取请求数据
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({'success': False, 'error': '缺少图片数据'})
        
        base64_image = data['image']
        
        # 限制Base64大小（约10MB）
        MAX_BASE64_SIZE = 10 * 1024 * 1024 * 1.33  # Base64会增加约33%大小
        if len(base64_image) > MAX_BASE64_SIZE:
            return jsonify({'success': False, 'error': '图片大小超过限制（最大10MB）'})
        
        # 验证Base64格式
        if not base64_image.startswith('data:image/'):
            return jsonify({'success': False, 'error': '无效的图片格式'})
        
        # 提取文件扩展名
        import re
        match = re.search(r'data:image/(\w+);base64,', base64_image)
        if not match:
            return jsonify({'success': False, 'error': '无效的图片格式'})
        
        ext = match.group(1)
        # 白名单校验
        ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({'success': False, 'error': '不支持的文件类型'})
        
        # 生成随机文件名
        new_filename = f"{uuid.uuid4()}.{ext}"
        upload_dir = os.path.join(BASE_DIR, 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        filepath = os.path.join(upload_dir, new_filename)
        
        try:
            # 解码Base64
            import base64
            img_data = base64.b64decode(base64_image.split(',')[1])
            
            # 保存图片
            with open(filepath, 'wb') as f:
                f.write(img_data)
            
            # MIME类型校验
            img_type = get_image_type(filepath)
            if not img_type:
                os.remove(filepath)
                return jsonify({'success': False, 'error': '无效的图片文件'})
            
            # 图片压缩
            try:
                from PIL import Image
                img = Image.open(filepath)
                img.thumbnail((800, 800))
                img.save(filepath, optimize=True, quality=85)
            except Exception as e:
                print(f"图片压缩失败: {e}")
            
            # 识别图片
            results = flower_model(filepath)
            predictions = results.pandas().xyxy[0].to_dict(orient='records')
            
            if predictions:
                result_str = ', '.join([f"{row['name']} ({row['conf']:.2f})" for row in predictions])
            else:
                result_str = '未识别到花卉'
            
            # 保存识别结果
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
            
            # 构建结果
            formatted_results = []
            for pred in predictions:
                formatted_results.append({
                    'name': pred['name'],
                    'confidence': float(pred['conf']),
                    'bbox': [
                        float(pred['xmin']),
                        float(pred['ymin']),
                        float(pred['xmax']),
                        float(pred['ymax'])
                    ]
                })
            
            return jsonify({
                'success': True,
                'results': formatted_results
            })
        except Exception as e:
            # 清理文件
            if os.path.exists(filepath):
                os.remove(filepath)
            print(f"识别过程中发生错误: {type(e).__name__}: {str(e)}")
            return jsonify({'success': False, 'error': f'识别失败: {str(e)}'})
        
    except Exception as e:
        print(f"检测过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '检测失败，请稍后重试'})

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

@app.route('/api/results/<int:result_id>/correct', methods=['POST'])
@login_required
def correct_result(result_id):
    """用户手动纠正识别结果"""
    try:
        data = request.get_json()
        correct_name = data.get('correct_name')
        
        if not correct_name:
            return jsonify({'success': False, 'error': '请提供正确的植物名称'})
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        check_query = "SELECT * FROM recognition_results WHERE id = %s AND user_id = %s"
        cursor.execute(check_query, (result_id, session['user_id']))
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '记录不存在或无权访问'})
        
        update_query = """
            UPDATE recognition_results 
            SET result = %s, 
                corrected = 1,
                original_result = %s,
                corrected_at = NOW()
            WHERE id = %s
        """
        cursor.execute(update_query, (correct_name, result['result'], result_id))
        connection.commit()
        
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': '识别结果已纠正'})
        
    except Exception as e:
        print(f"纠正识别结果过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '纠正失败，请稍后重试'})

@app.route('/api/results/<int:result_id>/feedback', methods=['POST'])
@login_required
def submit_feedback(result_id):
    """提交错误反馈（识别错了）"""
    try:
        data = request.get_json()
        feedback_type = data.get('feedback_type', 'wrong')
        feedback_comment = data.get('comment', '')
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        check_query = "SELECT * FROM recognition_results WHERE id = %s AND user_id = %s"
        cursor.execute(check_query, (result_id, session['user_id']))
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '记录不存在或无权访问'})
        
        check_feedback = "SELECT * FROM recognition_feedback WHERE result_id = %s"
        cursor.execute(check_feedback, (result_id,))
        existing_feedback = cursor.fetchone()
        
        if existing_feedback:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '已提交过反馈'})
        
        insert_query = """
            INSERT INTO recognition_feedback (result_id, user_id, feedback_type, comment)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (result_id, session['user_id'], feedback_type, feedback_comment))
        connection.commit()
        
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': '反馈已提交，感谢您的帮助'})
        
    except Exception as e:
        print(f"提交反馈过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '提交失败，请稍后重试'})

@app.route('/api/results/<int:result_id>/rename', methods=['POST'])
@login_required
def rename_result(result_id):
    """重命名识别结果标签"""
    try:
        data = request.get_json()
        new_name = data.get('new_name')
        
        if not new_name:
            return jsonify({'success': False, 'error': '请提供新的名称'})
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        check_query = "SELECT * FROM recognition_results WHERE id = %s AND user_id = %s"
        cursor.execute(check_query, (result_id, session['user_id']))
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '记录不存在或无权访问'})
        
        update_query = """
            UPDATE recognition_results 
            SET result = %s,
                renamed = 1,
                renamed_at = NOW()
            WHERE id = %s
        """
        cursor.execute(update_query, (new_name, result_id))
        connection.commit()
        
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': '标签已重命名'})
        
    except Exception as e:
        print(f"重命名标签过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '重命名失败，请稍后重试'})

@app.route('/api/results/filter', methods=['GET'])
@login_required
def filter_results():
    """筛选识别历史记录"""
    try:
        min_confidence = request.args.get('min_confidence', type=float)
        max_confidence = request.args.get('max_confidence', type=float)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        corrected_only = request.args.get('corrected_only', 'false').lower() == 'true'
        search = request.args.get('search', '')
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT id, image_path, result, confidence, created_at, corrected, renamed
            FROM recognition_results 
            WHERE user_id = %s
        """
        params = [session['user_id']]
        
        if min_confidence is not None:
            query += " AND confidence >= %s"
            params.append(min_confidence)
        
        if max_confidence is not None:
            query += " AND confidence <= %s"
            params.append(max_confidence)
        
        if start_date:
            query += " AND created_at >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND created_at <= %s"
            params.append(end_date)
        
        if corrected_only:
            query += " AND corrected = 1"
        
        if search:
            query += " AND result LIKE %s"
            params.append(f'%{search}%')
        
        query += " ORDER BY created_at DESC LIMIT 100"
        
        cursor.execute(query, params)
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
                'created_at': r['created_at'].isoformat() if r['created_at'] else None,
                'corrected': bool(r['corrected']),
                'renamed': bool(r['renamed'])
            })
        
        return jsonify({
            'success': True,
            'results': formatted_results
        })
        
    except Exception as e:
        print(f"筛选识别结果过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '筛选失败，请稍后重试'})

@app.route('/api/results/check-duplicate', methods=['POST'])
@login_required
def check_duplicate():
    """检查相同图片是否已识别过"""
    try:
        data = request.get_json()
        image_hash = data.get('image_hash')
        
        if not image_hash:
            return jsonify({'success': False, 'error': '缺少图片哈希值'})
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        check_query = """
            SELECT id, result, confidence, created_at
            FROM recognition_results
            WHERE user_id = %s AND image_hash = %s
            ORDER BY created_at DESC
            LIMIT 1
        """
        cursor.execute(check_query, (session['user_id'], image_hash))
        existing_result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if existing_result:
            return jsonify({
                'success': True,
                'is_duplicate': True,
                'existing_result': {
                    'id': existing_result['id'],
                    'result': existing_result['result'],
                    'confidence': float(existing_result['confidence']) if existing_result['confidence'] else 0,
                    'created_at': existing_result['created_at'].isoformat() if existing_result['created_at'] else None
                }
            })
        else:
            return jsonify({
                'success': True,
                'is_duplicate': False
            })
        
    except Exception as e:
        print(f"检查重复识别过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '检查失败，请稍后重试'})

# ==================== 植物信息API ====================

@app.route('/api/plants', methods=['GET'])
def get_plants():
    """获取植物列表"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT id, name, scientific_name, category, family, image_url
            FROM plants
            ORDER BY name
            LIMIT 100
        """
        cursor.execute(query)
        plants = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        formatted_plants = []
        for plant in plants:
            formatted_plants.append({
                'id': plant['id'],
                'name': plant['name'],
                'scientificName': plant['scientific_name'],
                'category': plant['category'],
                'family': plant['family'],
                'imageUrl': plant['image_url']
            })
        
        return jsonify({
            'success': True,
            'plants': formatted_plants
        })
        
    except Exception as e:
        print(f"获取植物列表过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '获取失败，请稍后重试'})

@app.route('/api/plants/<int:plant_id>', methods=['GET'])
def get_plant_detail(plant_id):
    """获取植物详细信息"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT * FROM plants WHERE id = %s
        """
        cursor.execute(query, (plant_id,))
        plant = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if not plant:
            return jsonify({'success': False, 'error': '植物不存在'})
        
        formatted_plant = {
            'id': plant['id'],
            'name': plant['name'],
            'scientificName': plant['scientific_name'],
            'category': plant['category'],
            'family': plant['family'],
            'description': plant['description'],
            'imageUrl': plant['image_url'],
            'bloomingSeason': plant['blooming_season'],
            'growthStage': plant['growth_stage'],
            'sunlightRequirements': plant['sunlight_requirements'],
            'waterNeeds': plant['water_needs'],
            'origin': plant['origin'],
            'toxicity': plant['toxicity'],
            'careTips': plant['care_tips'],
            'plantingInstructions': plant['planting_instructions'],
            'propagationMethods': plant['propagation_methods'],
            'pestsAndDiseases': plant['pests_and_diseases'],
            'similarPlants': plant['similar_plants'],
            'benefits': plant['benefits'],
            'otherNames': plant['other_names'].split(',') if plant['other_names'] else []
        }
        
        return jsonify({
            'success': True,
            'plant': formatted_plant
        })
        
    except Exception as e:
        print(f"获取植物详情过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '获取失败，请稍后重试'})

@app.route('/api/plants/search', methods=['GET'])
def search_plants():
    """搜索植物"""
    try:
        query = request.args.get('q', '')
        
        if not query:
            return jsonify({'success': False, 'error': '请输入搜索关键词'})
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        search_query = """
            SELECT id, name, scientific_name, category, family, image_url
            FROM plants
            WHERE name LIKE %s OR scientific_name LIKE %s OR other_names LIKE %s
            ORDER BY name
            LIMIT 20
        """
        search_term = f'%{query}%'
        cursor.execute(search_query, (search_term, search_term, search_term))
        plants = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        formatted_plants = []
        for plant in plants:
            formatted_plants.append({
                'id': plant['id'],
                'name': plant['name'],
                'scientificName': plant['scientific_name'],
                'category': plant['category'],
                'family': plant['family'],
                'imageUrl': plant['image_url']
            })
        
        return jsonify({
            'success': True,
            'plants': formatted_plants
        })
        
    except Exception as e:
        print(f"搜索植物过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '搜索失败，请稍后重试'})

@app.route('/api/plants/category/<category>', methods=['GET'])
def get_plants_by_category(category):
    """按分类获取植物"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT id, name, scientific_name, category, family, image_url
            FROM plants
            WHERE category = %s
            ORDER BY name
            LIMIT 50
        """
        cursor.execute(query, (category,))
        plants = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        formatted_plants = []
        for plant in plants:
            formatted_plants.append({
                'id': plant['id'],
                'name': plant['name'],
                'scientificName': plant['scientific_name'],
                'category': plant['category'],
                'family': plant['family'],
                'imageUrl': plant['image_url']
            })
        
        return jsonify({
            'success': True,
            'plants': formatted_plants
        })
        
    except Exception as e:
        print(f"按分类获取植物过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '获取失败，请稍后重试'})

# ==================== 园艺工具 API ====================

@app.route('/api/records/timeline', methods=['GET'])
@login_required
def get_records_by_timeline():
    """按时间查看识别记录（时间轴视图）"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        group_by = request.args.get('group_by', 'day')  # day, week, month
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT id, image_path, result, confidence, created_at, is_favorite, is_archived
            FROM recognition_results
            WHERE user_id = %s AND is_deleted = 0
        """
        params = [session['user_id']]
        
        if start_date:
            query += " AND DATE(created_at) >= %s"
            params.append(start_date)
        if end_date:
            query += " AND DATE(created_at) <= %s"
            params.append(end_date)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, tuple(params))
        records = cursor.fetchall()
        
        # 按时间分组
        timeline = {}
        for record in records:
            date_key = record['created_at'].strftime('%Y-%m-%d')
            if date_key not in timeline:
                timeline[date_key] = []
            timeline[date_key].append({
                'id': record['id'],
                'imagePath': record['image_path'],
                'result': record['result'],
                'confidence': float(record['confidence']) if record['confidence'] else 0,
                'createdAt': record['created_at'].isoformat(),
                'isFavorite': bool(record['is_favorite']),
                'isArchived': bool(record['is_archived'])
            })
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'timeline': timeline,
            'total': len(records)
        })
        
    except Exception as e:
        print(f"获取时间轴记录失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '获取失败'})

@app.route('/api/records/by-plant', methods=['GET'])
@login_required
def get_records_by_plant():
    """按植物名称查看记录"""
    try:
        plant_name = request.args.get('plant_name', '')
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT id, image_path, result, confidence, created_at, is_favorite, notes
            FROM recognition_results
            WHERE user_id = %s AND is_deleted = 0 AND result LIKE %s
            ORDER BY created_at DESC
        """
        cursor.execute(query, (session['user_id'], f'%{plant_name}%'))
        records = cursor.fetchall()
        
        formatted_records = []
        for record in records:
            formatted_records.append({
                'id': record['id'],
                'imagePath': record['image_path'],
                'result': record['result'],
                'confidence': float(record['confidence']) if record['confidence'] else 0,
                'createdAt': record['created_at'].isoformat(),
                'isFavorite': bool(record['is_favorite']),
                'notes': record['notes']
            })
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'records': formatted_records,
            'total': len(formatted_records)
        })
        
    except Exception as e:
        print(f"按植物名称获取记录失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '获取失败'})

@app.route('/api/records/<int:result_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(result_id):
    """收藏/取消收藏识别结果"""
    try:
        data = request.get_json()
        is_favorite = data.get('is_favorite', True)
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # 更新识别结果的收藏状态
        cursor.execute("""
            UPDATE recognition_results
            SET is_favorite = %s
            WHERE id = %s AND user_id = %s
        """, (1 if is_favorite else 0, result_id, session['user_id']))
        
        # 同时更新favorites表
        if is_favorite:
            cursor.execute("""
                INSERT IGNORE INTO favorites (user_id, result_id, favorite_type)
                VALUES (%s, %s, 'result')
            """, (session['user_id'], result_id))
        else:
            cursor.execute("""
                DELETE FROM favorites
                WHERE user_id = %s AND result_id = %s AND favorite_type = 'result'
            """, (session['user_id'], result_id))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': '已收藏' if is_favorite else '已取消收藏',
            'isFavorite': is_favorite
        })
        
    except Exception as e:
        print(f"收藏操作失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '操作失败'})

@app.route('/api/favorites', methods=['GET'])
@login_required
def get_favorites():
    """获取用户的所有收藏"""
    try:
        favorite_type = request.args.get('type', 'all')  # all, result, plant
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if favorite_type == 'result':
            query = """
                SELECT f.*, r.image_path, r.result, r.confidence, r.created_at as result_created_at
                FROM favorites f
                JOIN recognition_results r ON f.result_id = r.id
                WHERE f.user_id = %s AND f.favorite_type = 'result' AND r.is_deleted = 0
                ORDER BY f.created_at DESC
            """
            cursor.execute(query, (session['user_id'],))
        elif favorite_type == 'plant':
            query = """
                SELECT f.*, p.name, p.scientific_name, p.image_url, p.category
                FROM favorites f
                JOIN plants p ON f.plant_id = p.id
                WHERE f.user_id = %s AND f.favorite_type = 'plant'
                ORDER BY f.created_at DESC
            """
            cursor.execute(query, (session['user_id'],))
        else:
            # 获取所有收藏
            query = """
                SELECT f.*, 
                       r.image_path, r.result, r.confidence,
                       p.name as plant_name, p.scientific_name, p.image_url
                FROM favorites f
                LEFT JOIN recognition_results r ON f.result_id = r.id AND r.is_deleted = 0
                LEFT JOIN plants p ON f.plant_id = p.id
                WHERE f.user_id = %s
                ORDER BY f.created_at DESC
            """
            cursor.execute(query, (session['user_id'],))
        
        favorites = cursor.fetchall()
        
        formatted_favorites = []
        for fav in favorites:
            formatted_favorites.append({
                'id': fav['id'],
                'type': fav['favorite_type'],
                'createdAt': fav['created_at'].isoformat(),
                'data': {
                    'resultId': fav.get('result_id'),
                    'plantId': fav.get('plant_id'),
                    'imagePath': fav.get('image_path') or fav.get('image_url'),
                    'name': fav.get('result') or fav.get('plant_name'),
                    'scientificName': fav.get('scientific_name'),
                    'confidence': float(fav['confidence']) if fav.get('confidence') else None,
                    'category': fav.get('category')
                }
            })
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'favorites': formatted_favorites,
            'total': len(formatted_favorites)
        })
        
    except Exception as e:
        print(f"获取收藏失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '获取失败'})

@app.route('/api/tags', methods=['GET', 'POST'])
@login_required
def manage_tags():
    """标签管理"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if request.method == 'GET':
            # 获取所有标签
            cursor.execute("""
                SELECT t.*, COUNT(rt.result_id) as count
                FROM tags t
                LEFT JOIN result_tags rt ON t.id = rt.tag_id
                WHERE t.user_id = %s
                GROUP BY t.id
                ORDER BY t.created_at DESC
            """, (session['user_id'],))
            tags = cursor.fetchall()
            
            formatted_tags = []
            for tag in tags:
                formatted_tags.append({
                    'id': tag['id'],
                    'name': tag['name'],
                    'color': tag['color'],
                    'count': tag['count'],
                    'createdAt': tag['created_at'].isoformat()
                })
            
            cursor.close()
            connection.close()
            
            return jsonify({
                'success': True,
                'tags': formatted_tags
            })
            
        elif request.method == 'POST':
            # 创建新标签
            data = request.get_json()
            name = data.get('name', '').strip()
            color = data.get('color', '#4CAF50')
            
            if not name:
                return jsonify({'success': False, 'error': '标签名称不能为空'})
            
            cursor.execute("""
                INSERT INTO tags (user_id, name, color)
                VALUES (%s, %s, %s)
            """, (session['user_id'], name, color))
            
            connection.commit()
            tag_id = cursor.lastrowid
            cursor.close()
            connection.close()
            
            return jsonify({
                'success': True,
                'message': '标签创建成功',
                'tag': {
                    'id': tag_id,
                    'name': name,
                    'color': color
                }
            })
            
    except Exception as e:
        print(f"标签管理失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '操作失败'})

@app.route('/api/tags/<int:tag_id>', methods=['PUT', 'DELETE'])
@login_required
def update_tag(tag_id):
    """更新或删除标签"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if request.method == 'PUT':
            data = request.get_json()
            name = data.get('name', '').strip()
            color = data.get('color')
            
            if not name:
                return jsonify({'success': False, 'error': '标签名称不能为空'})
            
            cursor.execute("""
                UPDATE tags
                SET name = %s, color = %s
                WHERE id = %s AND user_id = %s
            """, (name, color, tag_id, session['user_id']))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return jsonify({
                'success': True,
                'message': '标签更新成功'
            })
            
        elif request.method == 'DELETE':
            cursor.execute("""
                DELETE FROM tags
                WHERE id = %s AND user_id = %s
            """, (tag_id, session['user_id']))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return jsonify({
                'success': True,
                'message': '标签删除成功'
            })
            
    except Exception as e:
        print(f"标签操作失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '操作失败'})

@app.route('/api/records/<int:result_id>/tags', methods=['POST', 'DELETE'])
@login_required
def manage_result_tags(result_id):
    """为识别结果添加/删除标签"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if request.method == 'POST':
            data = request.get_json()
            tag_ids = data.get('tag_ids', [])
            
            for tag_id in tag_ids:
                cursor.execute("""
                    INSERT IGNORE INTO result_tags (result_id, tag_id)
                    VALUES (%s, %s)
                """, (result_id, tag_id))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return jsonify({
                'success': True,
                'message': '标签添加成功'
            })
            
        elif request.method == 'DELETE':
            data = request.get_json()
            tag_ids = data.get('tag_ids', [])
            
            for tag_id in tag_ids:
                cursor.execute("""
                    DELETE FROM result_tags
                    WHERE result_id = %s AND tag_id = %s
                """, (result_id, tag_id))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return jsonify({
                'success': True,
                'message': '标签移除成功'
            })
            
    except Exception as e:
        print(f"标签操作失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '操作失败'})

@app.route('/api/records/batch-delete', methods=['POST'])
@login_required
def batch_delete_records():
    """批量删除识别结果（移动到回收站）"""
    try:
        data = request.get_json()
        result_ids = data.get('result_ids', [])
        permanent = data.get('permanent', False)  # 是否永久删除
        
        if not result_ids:
            return jsonify({'success': False, 'error': '未选择要删除的记录'})
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if permanent:
            # 永久删除
            for result_id in result_ids:
                cursor.execute("""
                    DELETE FROM recognition_results
                    WHERE id = %s AND user_id = %s
                """, (result_id, session['user_id']))
        else:
            # 软删除（移动到回收站）
            for result_id in result_ids:
                # 先获取原始数据
                cursor.execute("""
                    SELECT * FROM recognition_results
                    WHERE id = %s AND user_id = %s
                """, (result_id, session['user_id']))
                record = cursor.fetchone()
                
                if record:
                    # 保存到回收站
                    import json
                    cursor.execute("""
                        INSERT INTO recycle_bin (user_id, result_id, original_data, expires_at)
                        VALUES (%s, %s, %s, DATE_ADD(NOW(), INTERVAL 30 DAY))
                    """, (session['user_id'], result_id, json.dumps(dict(record), default=str)))
                    
                    # 标记为已删除
                    cursor.execute("""
                        UPDATE recognition_results
                        SET is_deleted = 1, deleted_at = NOW()
                        WHERE id = %s
                    """, (result_id,))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': f'已删除 {len(result_ids)} 条记录'
        })
        
    except Exception as e:
        print(f"批量删除失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '删除失败'})

@app.route('/api/records/batch-archive', methods=['POST'])
@login_required
def batch_archive_records():
    """批量归档识别结果"""
    try:
        data = request.get_json()
        result_ids = data.get('result_ids', [])
        is_archived = data.get('is_archived', True)
        
        if not result_ids:
            return jsonify({'success': False, 'error': '未选择要归档的记录'})
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        for result_id in result_ids:
            cursor.execute("""
                UPDATE recognition_results
                SET is_archived = %s
                WHERE id = %s AND user_id = %s
            """, (1 if is_archived else 0, result_id, session['user_id']))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        action = '归档' if is_archived else '取消归档'
        return jsonify({
            'success': True,
            'message': f'已{action} {len(result_ids)} 条记录'
        })
        
    except Exception as e:
        print(f"批量归档失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '归档失败'})

@app.route('/api/recycle-bin', methods=['GET'])
@login_required
def get_recycle_bin():
    """获取回收站内容"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT rb.*, r.image_path, r.result, r.confidence
            FROM recycle_bin rb
            JOIN recognition_results r ON rb.result_id = r.id
            WHERE rb.user_id = %s AND (rb.expires_at IS NULL OR rb.expires_at > NOW())
            ORDER BY rb.deleted_at DESC
        """, (session['user_id'],))
        items = cursor.fetchall()
        
        formatted_items = []
        for item in items:
            formatted_items.append({
                'id': item['id'],
                'resultId': item['result_id'],
                'imagePath': item['image_path'],
                'result': item['result'],
                'confidence': float(item['confidence']) if item['confidence'] else 0,
                'deletedAt': item['deleted_at'].isoformat(),
                'expiresAt': item['expires_at'].isoformat() if item['expires_at'] else None
            })
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'items': formatted_items,
            'total': len(formatted_items)
        })
        
    except Exception as e:
        print(f"获取回收站失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '获取失败'})

@app.route('/api/recycle-bin/<int:item_id>/restore', methods=['POST'])
@login_required
def restore_from_recycle_bin(item_id):
    """从回收站恢复记录"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # 获取回收站记录
        cursor.execute("""
            SELECT result_id FROM recycle_bin
            WHERE id = %s AND user_id = %s
        """, (item_id, session['user_id']))
        item = cursor.fetchone()
        
        if not item:
            return jsonify({'success': False, 'error': '记录不存在'})
        
        result_id = item['result_id']
        
        # 恢复记录
        cursor.execute("""
            UPDATE recognition_results
            SET is_deleted = 0, deleted_at = NULL
            WHERE id = %s AND user_id = %s
        """, (result_id, session['user_id']))
        
        # 从回收站删除
        cursor.execute("""
            DELETE FROM recycle_bin
            WHERE id = %s
        """, (item_id,))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': '记录已恢复'
        })
        
    except Exception as e:
        print(f"恢复记录失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '恢复失败'})

@app.route('/api/sync', methods=['POST'])
@login_required
def sync_data():
    """本地/云端同步"""
    try:
        data = request.get_json()
        device_id = data.get('device_id', 'unknown')
        sync_type = data.get('sync_type', 'bidirectional')  # upload, download, bidirectional
        local_data = data.get('local_data', {})
        last_sync_at = data.get('last_sync_at')
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # 获取云端数据
        cursor.execute("""
            SELECT id, image_path, result, confidence, is_favorite, is_archived, 
                   notes, location, weather, created_at, updated_at
            FROM recognition_results
            WHERE user_id = %s AND is_deleted = 0
        """, (session['user_id'],))
        cloud_records = cursor.fetchall()
        
        # 获取上次同步时间
        cursor.execute("""
            SELECT last_sync_at FROM sync_records
            WHERE user_id = %s AND device_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (session['user_id'], device_id))
        last_sync = cursor.fetchone()
        
        # 记录同步
        import json
        cursor.execute("""
            INSERT INTO sync_records (user_id, device_id, sync_type, sync_status, sync_data)
            VALUES (%s, %s, %s, 'completed', %s)
        """, (session['user_id'], device_id, sync_type, json.dumps({
            'records_count': len(cloud_records),
            'sync_type': sync_type
        })))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': '同步完成',
            'cloudData': {
                'records': [dict(r) for r in cloud_records],
                'lastSyncAt': last_sync['last_sync_at'].isoformat() if last_sync and last_sync['last_sync_at'] else None
            }
        })
        
    except Exception as e:
        print(f"同步失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '同步失败'})

@app.route('/api/settings', methods=['GET', 'PUT'])
@login_required
def user_settings():
    """用户设置管理"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if request.method == 'GET':
            cursor.execute("""
                SELECT * FROM user_settings
                WHERE user_id = %s
            """, (session['user_id'],))
            settings = cursor.fetchone()
            
            if not settings:
                # 创建默认设置
                cursor.execute("""
                    INSERT INTO user_settings (user_id)
                    VALUES (%s)
                """, (session['user_id'],))
                connection.commit()
                
                cursor.execute("""
                    SELECT * FROM user_settings
                    WHERE user_id = %s
                """, (session['user_id'],))
                settings = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            return jsonify({
                'success': True,
                'settings': {
                    'autoSync': bool(settings['auto_sync']),
                    'syncInterval': settings['sync_interval'],
                    'defaultView': settings['default_view'],
                    'theme': settings['theme'],
                    'language': settings['language']
                }
            })
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            cursor.execute("""
                UPDATE user_settings
                SET auto_sync = %s,
                    sync_interval = %s,
                    default_view = %s,
                    theme = %s,
                    language = %s
                WHERE user_id = %s
            """, (
                data.get('autoSync', True),
                data.get('syncInterval', 3600),
                data.get('defaultView', 'grid'),
                data.get('theme', 'auto'),
                data.get('language', 'zh-CN'),
                session['user_id']
            ))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return jsonify({
                'success': True,
                'message': '设置已更新'
            })
            
    except Exception as e:
        print(f"设置操作失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '操作失败'})

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
