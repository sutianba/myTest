#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# 你可以在 http://127.0.0.1:5000 网站进行查看
import os
import sys
import base64
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
import hashlib
import secrets
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# 导入邮箱验证功能
from email_config import generate_verification_token, send_verification_email, verify_token, mark_token_as_used

# 导入密码哈希功能
from password_hash import hash_password, verify_password

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
try:
    flower_model = torch.hub.load('..', 'custom', path='../yolov5s.pt', source='local', force_reload=True)
    flower_model.conf = 0.25  # 降低置信度阈值，保留更多检测结果
    flower_model.iou = 0.5   # 保持NMS IOU阈值
    print("成功加载YOLOv5花卉识别模型")
except Exception as e:
    print(f"无法加载YOLOv5模型: {e}")
    raise RuntimeError("无法加载YOLOv5模型，请检查模型文件是否存在") from e

# 路由保护装饰器
def login_required(f):
    """检查用户是否已登录的装饰器"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            # 用户未登录，重定向到登录页面
            return jsonify({'success': False, 'error': '用户未登录'}), 401
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
    """用户登录API接口"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'})

        connection = get_db_connection()
        cursor = connection.cursor()
        
        check_query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(check_query, (username,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '用户名或密码错误'})
        
        # 检查用户状态
        if user['status'] != 'active':
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '账号未激活，请先验证邮箱'})
        
        # 验证密码
        if not verify_password(password, user['password_hash']):
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '用户名或密码错误'})
        
        # 生成JWT token
        payload = {
            'user_id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }
        token = jwt.encode(payload, app.secret_key, algorithm='HS256')
        
        # 设置session
        session['username'] = user['username']
        session['user_id'] = user['id']
        session['token'] = token
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'token': token,
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

@app.route('/api/logout', methods=['POST'])
def logout():
    """用户登出API接口"""
    try:
        session.clear()
        return jsonify({'success': True, 'message': '已成功登出'})
    except Exception as e:
        print(f"登出过程中发生错误: {type(e).__name__}: {str(e)}")
        return jsonify({'success': False, 'error': '登出失败，请稍后重试'})

@app.route('/api/user_info', methods=['GET'])
def get_user_info():
    """获取当前用户信息"""
    try:
        if 'username' not in session:
            return jsonify({'success': False, 'error': '用户未登录'})
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        check_query = "SELECT id, username, email, role, created_at FROM users WHERE username = %s"
        cursor.execute(check_query, (session['username'],))
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
    """检查用户认证状态"""
    try:
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
