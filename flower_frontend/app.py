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

# 导入图片EXIF信息提取所需模块
from PIL import Image # 用于打开和处理图片
from PIL.ExifTags import TAGS # 用于将EXIF标签ID映射到标签名称
import exifread # 用于提取图片EXIF信息
from geopy.geocoders import Nominatim # 用于根据经纬度获取地址信息
from geopy.exc import GeocoderTimedOut, GeocoderServiceError # 用于处理地理编码超时和服务错误
import time # 用于处理时间相关操作

app = Flask(__name__)
CORS(app)  # 启用CORS以允许前端访问

# 设置密钥用于会话管理
app.secret_key = secrets.token_hex(16)

# 配置线程池用于异步处理
thread_pool = ThreadPoolExecutor(max_workers=4)  # 根据系统CPU核心数调整

# 定义静态文件目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 使用SQLite数据库
import sqlite3

# SQLite数据库路径
DATABASE_PATH = os.path.join(BASE_DIR, 'flower_recognition.db')

# 初始化SQLite数据库
def init_sqlite_db():
    try:
        print("[调试] 开始执行init_sqlite_db函数")
        print("正在尝试连接到SQLite数据库...")
        
        # 连接到SQLite数据库（如果不存在则创建）
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        
        print("成功连接到SQLite数据库")
        
        print("正在检查或创建users表...")
        
        # 创建users表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        connection.commit()
        print("数据库表初始化成功")
        connection.close()
    except Exception as e:
        print(f"数据库初始化失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        print("请检查SQLite数据库配置")

# 获取数据库连接
def get_db_connection():
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        # 设置返回结果为字典类型
        connection.row_factory = sqlite3.Row
        return connection
    except Exception as e:
        print(f"获取数据库连接失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

# 初始化数据库
# 启用SQLite数据库初始化功能
init_sqlite_db()

# 加载YOLOv5模型
import torch

# 使用正确路径加载模型
try:
    flower_model = torch.hub.load('..', 'custom', path='../testflowers.pt', source='local', force_reload=True)
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
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    """返回前端页面"""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/login.html')
def login_page():
    """返回登录页面"""
    return send_from_directory(BASE_DIR, 'login.html')

@app.route('/<path:filename>')
def serve_file(filename):
    """返回指定的文件"""
    return send_from_directory(BASE_DIR, filename)

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录API接口"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'})

        # 验证用户
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # 查询用户
        query = "SELECT * FROM users WHERE username = ? AND password_hash = ?"
        cursor.execute(query, (username, hashed_password))
        user = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if user:
            # 登录成功，设置会话
            session['username'] = username
            session['role'] = user['role']
            return jsonify({'success': True, 'message': '登录成功', 'role': user['role']})
        else:
            return jsonify({'success': False, 'error': '用户名或密码错误'})
    except Exception as e:
        print(f"登录过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '登录失败，请稍后重试'})

@app.route('/api/logout', methods=['POST'])
def logout():
    """用户登出API接口"""
    try:
        # 清除会话
        session.pop('username', None)
        session.pop('role', None)
        return jsonify({'success': True, 'message': '登出成功'})
    except Exception as e:
        print(f"登出过程中发生错误: {str(e)}")
        return jsonify({'success': False, 'error': '登出失败，请稍后重试'})

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册API接口"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'})
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': '密码长度不能少于6位'})

        # 检查用户名是否已存在
        connection = get_db_connection()
        cursor = connection.cursor()
        
        check_query = "SELECT * FROM users WHERE username = ?"
        cursor.execute(check_query, (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '用户名已存在'})
        
        # 密码哈希处理
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # 插入新用户，默认为user角色
        insert_query = "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)"
        cursor.execute(insert_query, (username, hashed_password, 'user'))
        connection.commit()
        
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': '注册成功，请登录'})
    except Exception as e:
        print(f"注册过程中发生错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '注册失败，请稍后重试'})


@app.route('/api/check_login')
def check_login():
    """检查用户是否已登录"""
    if 'username' in session:
        return jsonify({'success': True, 'username': session['username'], 'role': session.get('role', 'user')})
    else:
        return jsonify({'success': False, 'error': '未登录'})

@app.route('/api/detect', methods=['POST'])
def detect_flower():
    """花卉识别API接口"""
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 支持单图片和多图片请求
        if 'image' in data:
            # 单图片请求
            image_data = data['image']
            results = process_single_image(image_data)
            return jsonify({'success': True, 'results': results})
        elif 'images' in data:
            # 多图片请求 - 使用线程池异步处理
            images_data = data['images']
            
            # 使用线程池并行处理多张图片
            futures = []
            for i, image_data in enumerate(images_data):
                # 提交任务到线程池
                future = thread_pool.submit(process_single_image, image_data)
                futures.append((i, future))
            
            # 收集所有结果
            all_results = []
            for i, future in futures:
                try:
                    results = future.result()  # 获取任务结果
                    all_results.append({
                        'image_index': i,
                        'results': results
                    })
                except Exception as e:
                    print(f"处理第 {i} 张图片时出错: {e}")
                    all_results.append({
                        'image_index': i,
                        'error': str(e),
                        'results': None
                    })
            
            return jsonify({'success': True, 'all_results': all_results})
        else:
            return jsonify({'success': False, 'error': '缺少图片数据'}), 400

    except Exception as e:
        print(f"识别过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'识别服务不可用，请稍后重试: {str(e)}'}), 500


def convert_to_decimal(coord, ref):
    """将EXIF格式的经纬度转换为十进制格式"""
    # coord通常是一个包含三个元素的列表：度、分、秒
    d, m, s = 0, 0, 0
    
    # 处理exifread返回的格式
    if hasattr(coord, 'values'):
        coord_values = coord.values
    else:
        coord_values = coord
    
    if len(coord_values) >= 3:
        # 处理度
        if hasattr(coord_values[0], 'num') and hasattr(coord_values[0], 'den'):
            d = coord_values[0].num / coord_values[0].den
        else:
            d = float(coord_values[0])
        
        # 处理分
        if hasattr(coord_values[1], 'num') and hasattr(coord_values[1], 'den'):
            m = coord_values[1].num / coord_values[1].den
        else:
            m = float(coord_values[1])
        
        # 处理秒
        if hasattr(coord_values[2], 'num') and hasattr(coord_values[2], 'den'):
            s = coord_values[2].num / coord_values[2].den
        else:
            s = float(coord_values[2])
    
    # 计算十进制坐标
    decimal = d + (m / 60.0) + (s / 3600.0)
    
    # 根据参考方向调整符号
    if ref in ['S', 'W']:
        decimal = -decimal
    
    return decimal


# 广西和广东地区经纬度范围数据库（包含部分城市的区信息）
guangxi_guangdong_cities = {
    "guangxi": {
        "province_name": "广西壮族自治区",
        "cities": {
            "南宁市": {"lat_min": 22.7, "lat_max": 23.3, "lon_min": 108.1, "lon_max": 108.5, "districts": {}},
            "柳州市": {"lat_min": 23.6, "lat_max": 24.4, "lon_min": 108.9, "lon_max": 109.7, "districts": {}},
            "桂林市": {"lat_min": 24.7, "lat_max": 25.5, "lon_min": 110.1, "lon_max": 110.7, "districts": {}},
            "梧州市": {"lat_min": 22.8, "lat_max": 23.6, "lon_min": 111.1, "lon_max": 111.7, "districts": {}},
            "北海市": {"lat_min": 20.8, "lat_max": 21.6, "lon_min": 108.8, "lon_max": 109.6, "districts": {}},
            "防城港市": {"lat_min": 21.3, "lat_max": 22.1, "lon_min": 107.5, "lon_max": 108.5, "districts": {}},
            "钦州市": {"lat_min": 21.7, "lat_max": 22.7, "lon_min": 108.4, "lon_max": 109.2, "districts": {}},
            "贵港市": {"lat_min": 22.8, "lat_max": 23.8, "lon_min": 109.2, "lon_max": 109.8, "districts": {}},
            "玉林市": {"lat_min": 22.1, "lat_max": 23.1, "lon_min": 109.8, "lon_max": 110.6, "districts": {}},
            "百色市": {"lat_min": 23.5, "lat_max": 24.5, "lon_min": 106.2, "lon_max": 107.0, "districts": {}},
            "贺州市": {"lat_min": 23.7, "lat_max": 24.5, "lon_min": 111.1, "lon_max": 112.0, "districts": {}},
            "河池市": {"lat_min": 23.9, "lat_max": 25.1, "lon_min": 107.6, "lon_max": 108.6, "districts": {}},
            "来宾市": {"lat_min": 23.3, "lat_max": 24.1, "lon_min": 108.6, "lon_max": 109.4, "districts": {}},
            "崇左市": {"lat_min": 22.1, "lat_max": 23.1, "lon_min": 107.1, "lon_max": 108.2, "districts": {}}
        }
    },
    "guangdong": {
        "province_name": "广东省",
        "cities": {
            "广州市": {
                "lat_min": 22.7, "lat_max": 23.3, "lon_min": 113.1, "lon_max": 113.6,
                "districts": {
                    "越秀区": {"lat_min": 23.12, "lat_max": 23.16, "lon_min": 113.24, "lon_max": 113.30},
                    "天河区": {"lat_min": 23.11, "lat_max": 23.24, "lon_min": 113.32, "lon_max": 113.40},
                    "海珠区": {"lat_min": 23.05, "lat_max": 23.15, "lon_min": 113.22, "lon_max": 113.32},
                    "荔湾区": {"lat_min": 23.06, "lat_max": 23.15, "lon_min": 113.16, "lon_max": 113.26},
                    "白云区": {"lat_min": 23.10, "lat_max": 23.30, "lon_min": 113.10, "lon_max": 113.30},
                    "黄埔区": {"lat_min": 23.05, "lat_max": 23.25, "lon_min": 113.35, "lon_max": 113.55},
                    "番禺区": {"lat_min": 22.80, "lat_max": 23.00, "lon_min": 113.20, "lon_max": 113.50},
                    "花都区": {"lat_min": 23.20, "lat_max": 23.40, "lon_min": 112.90, "lon_max": 113.20},
                    "南沙区": {"lat_min": 22.60, "lat_max": 22.80, "lon_min": 113.30, "lon_max": 113.60},
                    "从化区": {"lat_min": 23.40, "lat_max": 23.70, "lon_min": 113.30, "lon_max": 114.00},
                    "增城区": {"lat_min": 23.10, "lat_max": 23.50, "lon_min": 113.50, "lon_max": 114.00}
                }
            },
            "深圳市": {
                "lat_min": 22.3, "lat_max": 22.8, "lon_min": 113.7, "lon_max": 114.6,
                "districts": {
                    "罗湖区": {"lat_min": 22.53, "lat_max": 22.57, "lon_min": 114.04, "lon_max": 114.12},
                    "福田区": {"lat_min": 22.51, "lat_max": 22.57, "lon_min": 113.93, "lon_max": 114.04},
                    "南山区": {"lat_min": 22.42, "lat_max": 22.55, "lon_min": 113.87, "lon_max": 114.00},
                    "宝安区": {"lat_min": 22.44, "lat_max": 22.70, "lon_min": 113.72, "lon_max": 114.00},
                    "龙岗区": {"lat_min": 22.53, "lat_max": 22.80, "lon_min": 114.08, "lon_max": 114.30},
                    "盐田区": {"lat_min": 22.57, "lat_max": 22.68, "lon_min": 114.22, "lon_max": 114.32},
                    "龙华区": {"lat_min": 22.54, "lat_max": 22.70, "lon_min": 113.90, "lon_max": 114.08},
                    "坪山区": {"lat_min": 22.65, "lat_max": 22.80, "lon_min": 114.15, "lon_max": 114.40},
                    "光明区": {"lat_min": 22.70, "lat_max": 22.80, "lon_min": 113.90, "lon_max": 114.05},
                    "大鹏新区": {"lat_min": 22.40, "lat_max": 22.60, "lon_min": 114.20, "lon_max": 114.60}
                }
            },
            "珠海市": {"lat_min": 21.8, "lat_max": 22.4, "lon_min": 113.2, "lon_max": 113.7, "districts": {}},
            "汕头市": {"lat_min": 23.1, "lat_max": 23.5, "lon_min": 116.4, "lon_max": 117.2, "districts": {}},
            "佛山市": {"lat_min": 22.9, "lat_max": 23.3, "lon_min": 112.9, "lon_max": 113.3, "districts": {}},
            "韶关市": {"lat_min": 24.5, "lat_max": 25.4, "lon_min": 113.4, "lon_max": 114.3, "districts": {}},
            "湛江市": {"lat_min": 20.8, "lat_max": 21.5, "lon_min": 110.2, "lon_max": 110.9, "districts": {}},
            "肇庆市": {"lat_min": 23.1, "lat_max": 23.8, "lon_min": 112.2, "lon_max": 112.8, "districts": {}},
            "江门市": {"lat_min": 22.3, "lat_max": 22.8, "lon_min": 112.4, "lon_max": 113.0, "districts": {}},
            "茂名市": {"lat_min": 21.3, "lat_max": 21.8, "lon_min": 110.7, "lon_max": 111.3, "districts": {}},
            "惠州市": {"lat_min": 22.8, "lat_max": 23.5, "lon_min": 114.3, "lon_max": 114.9, "districts": {}},
            "梅州市": {"lat_min": 24.0, "lat_max": 24.4, "lon_min": 116.0, "lon_max": 116.4, "districts": {}},
            "汕尾市": {"lat_min": 22.7, "lat_max": 23.1, "lon_min": 115.2, "lon_max": 116.0, "districts": {}},
            "河源市": {"lat_min": 23.6, "lat_max": 24.3, "lon_min": 114.4, "lon_max": 115.2, "districts": {}},
            "阳江市": {"lat_min": 21.7, "lat_max": 22.3, "lon_min": 111.4, "lon_max": 112.0, "districts": {}},
            "清远市": {"lat_min": 23.4, "lat_max": 24.2, "lon_min": 112.9, "lon_max": 113.5, "districts": {}},
            "东莞市": {"lat_min": 22.8, "lat_max": 23.1, "lon_min": 113.6, "lon_max": 114.1, "districts": {}},
            "中山市": {"lat_min": 22.4, "lat_max": 22.7, "lon_min": 113.1, "lon_max": 113.5, "districts": {}},
            "潮州市": {"lat_min": 23.4, "lat_max": 23.7, "lon_min": 116.3, "lon_max": 116.7, "districts": {}},
            "揭阳市": {"lat_min": 22.9, "lat_max": 23.5, "lon_min": 115.8, "lon_max": 116.4, "districts": {}},
            "云浮市": {"lat_min": 22.7, "lat_max": 23.2, "lon_min": 111.9, "lon_max": 112.4, "districts": {}}
        }
    }
}


def match_location_by_coordinates(lat, lon):
    """
    根据经纬度匹配广西或广东的城市和区
    使用简单的矩形范围匹配
    """
    # 检查是否在广东范围内
    for city_name, city_info in guangxi_guangdong_cities["guangdong"]["cities"].items():
        if city_info["lat_min"] <= lat <= city_info["lat_max"] and city_info["lon_min"] <= lon <= city_info["lon_max"]:
            # 进一步检查是否在该城市的某个区内
            for district_name, district_coords in city_info["districts"].items():
                if district_coords["lat_min"] <= lat <= district_coords["lat_max"] and district_coords["lon_min"] <= lon <= district_coords["lon_max"]:
                    return {
                        "province": guangxi_guangdong_cities["guangdong"]["province_name"],
                        "city": city_name,
                        "district": district_name
                    }
            # 如果没有匹配到区，返回城市信息
            return {
                "province": guangxi_guangdong_cities["guangdong"]["province_name"],
                "city": city_name,
                "district": "未知区"
            }
    
    # 检查是否在广西范围内
    for city_name, city_info in guangxi_guangdong_cities["guangxi"]["cities"].items():
        if city_info["lat_min"] <= lat <= city_info["lat_max"] and city_info["lon_min"] <= lon <= city_info["lon_max"]:
            # 进一步检查是否在该城市的某个区内
            for district_name, district_coords in city_info["districts"].items():
                if district_coords["lat_min"] <= lat <= district_coords["lat_max"] and district_coords["lon_min"] <= lon <= district_coords["lon_max"]:
                    return {
                        "province": guangxi_guangdong_cities["guangxi"]["province_name"],
                        "city": city_name,
                        "district": district_name
                    }
            # 如果没有匹配到区，返回城市信息
            return {
                "province": guangxi_guangdong_cities["guangxi"]["province_name"],
                "city": city_name,
                "district": "未知区"
            }
    
    # 默认返回未知
    return {
        "province": "未知省份",
        "city": "未知城市",
        "district": "未知区"
    }


def get_address_from_coordinates(lat, lon, max_retries=1):
    """
    通过经纬度获取地址信息
    优先使用geopy和Nominatim服务，失败时返回None
    优化：减少超时时间和重试次数，提高响应速度
    """
    try:
        # 暂时禁用Nominatim服务以提高速度
        # geolocator = Nominatim(user_agent="flower_recognition_app", timeout=2)
        # 
        # # 重试机制
        # for attempt in range(max_retries):
        #     try:
        #         location = geolocator.reverse((lat, lon), language='zh-CN')
        #         if location:
        #             return location.raw.get('address', {})
        #     except GeocoderTimedOut:
        #         print(f"地理编码请求超时，第 {attempt + 1} 次尝试...")
        #     except GeocoderServiceError as e:
        #         print(f"地理编码服务错误: {e}，第 {attempt + 1} 次尝试...")
        #     except Exception as e:
        #         print(f"获取地址信息时出错: {e}")
        #         break
        
        # 直接返回None，使用本地经纬度匹配，避免网络请求延迟
        return None
    except Exception as e:
        print(f"初始化地理编码器时出错: {e}")
    
    # 如果无法获取地址信息，返回None，后续会使用本地经纬度匹配
    return None


def format_address(address):
    """格式化地址信息，提取省、市、区等关键部分"""
    if not address:
        return {
            'formatted_address': "地址信息不可用",
            'province': "未知省份",
            'city': "未知城市",
            'district': "未知区"
        }
    
    # 尝试提取关键地址组件
    country = address.get('country', '未知国家')
    province = address.get('state', '') or address.get('province', '') or '未知省份'
    city = address.get('city', '') or address.get('district', '') or '未知城市'
    district = address.get('county', '') or address.get('district', '') or ''
    town = address.get('town', '') or address.get('county', '') or ''
    street = address.get('road', '') or address.get('street', '') or ''
    number = address.get('house_number', '')
    
    # 如果district与city相同，尝试从town中提取district
    if district and district == city and town:
        district = town
    
    # 构建完整地址
    address_parts = [country, province, city]
    if district and district != city:
        address_parts.append(district)
    if town and town != district:
        address_parts.append(town)
    if street:
        address_parts.append(street)
        if number:
            address_parts.append(number)
    
    # 移除空字符串并连接
    formatted_address = '，'.join(filter(None, address_parts))
    
    # 返回结构化地址信息
    return {
        'formatted_address': formatted_address,
        'province': province,
        'city': city,
        'district': district if district and district != city else "未知区"
    }


def process_single_image(image_data):
    """处理单个图片的识别"""
    # 移除base64头部
    if image_data.startswith('data:image/'):
        image_data = image_data.split(',')[1]

    # 解码base64图片数据
    try:
        image_bytes = base64.b64decode(image_data)
        print(f"成功解码base64数据，大小: {len(image_bytes)} 字节")
    except Exception as e:
        print(f"base64解码失败: {e}")
        raise ValueError("图片数据格式错误，无法解码") from e
    
    # 提取图片EXIF信息
    image_info = {
        'date_time': "未知",
        'location': {
            'has_location': False,
            'latitude': None,
            'longitude': None,
            'formatted_address': "无GPS信息",
            'province': "未知省份",
            'city': "未知城市",
            'district': "未知区",
            'raw_gps': None
        },
        'camera_info': {
            'make': "未知",
            'model': "未知"
        },
        'image_details': {
            'width': 0,
            'height': 0
        }
    }
    
    # 先提取EXIF信息
    try:
        # 直接从内存中读取EXIF信息
        image_bytes_io = io.BytesIO(image_bytes)
        
        # 使用exifread提取EXIF信息
        exif_tags = exifread.process_file(image_bytes_io)
        
        # 获取拍摄时间
        if 'Image DateTime' in exif_tags:
            image_info['date_time'] = str(exif_tags['Image DateTime'])
        elif 'EXIF DateTimeOriginal' in exif_tags:
            image_info['date_time'] = str(exif_tags['EXIF DateTimeOriginal'])
        elif 'EXIF DateTimeDigitized' in exif_tags:
            image_info['date_time'] = str(exif_tags['EXIF DateTimeDigitized'])
        
        # 获取相机信息
        if 'Image Make' in exif_tags:
            image_info['camera_info']['make'] = str(exif_tags['Image Make'])
        if 'Image Model' in exif_tags:
            image_info['camera_info']['model'] = str(exif_tags['Image Model'])
        
        # 获取GPS位置信息
        if all(key in exif_tags for key in ['GPS GPSLongitudeRef', 'GPS GPSLongitude', 
                                           'GPS GPSLatitudeRef', 'GPS GPSLatitude']):
            try:
                # 获取原始的经纬度信息
                lon_ref = exif_tags['GPS GPSLongitudeRef'].printable
                lon = exif_tags['GPS GPSLongitude']
                lat_ref = exif_tags['GPS GPSLatitudeRef'].printable
                lat = exif_tags['GPS GPSLatitude']
                
                # 转换为十进制格式
                dec_lat = convert_to_decimal(lat, lat_ref)
                dec_lon = convert_to_decimal(lon, lon_ref)
                
                try:
                    # 获取地址信息
                    address = get_address_from_coordinates(dec_lat, dec_lon)
                    if address:
                        address_info = format_address(address)
                        formatted_address = address_info['formatted_address']
                        province = address_info['province']
                        city = address_info['city']
                        district = address_info['district']
                    else:
                        # 当Nominatim服务失败时，使用本地经纬度匹配广西和广东地区
                        location_match = match_location_by_coordinates(dec_lat, dec_lon)
                        formatted_address = f"{location_match['province']}, {location_match['city']}, {location_match['district']}"
                        province = location_match['province']
                        city = location_match['city']
                        district = location_match['district']
                except Exception as e:
                    # 当获取地址信息或格式化地址时出错，直接使用本地经纬度匹配
                    print(f"获取或格式化地址时出错: {e}")
                    location_match = match_location_by_coordinates(dec_lat, dec_lon)
                    formatted_address = f"{location_match['province']}, {location_match['city']}, {location_match['district']}"
                    province = location_match['province']
                    city = location_match['city']
                    district = location_match['district']
                
                # 更新位置信息
                image_info['location'] = {
                    'has_location': True,
                    'latitude': dec_lat,
                    'longitude': dec_lon,
                    'formatted_address': formatted_address,
                    'province': province,
                    'city': city,
                    'district': district,
                    'raw_gps': {
                        'lat_ref': lat_ref,
                        'lat': str(lat),
                        'lon_ref': lon_ref,
                        'lon': str(lon)
                    }
                }
            except Exception as e:
                print(f"处理GPS信息时出错: {e}")
    except Exception as e:
        print(f"提取图片EXIF信息失败: {e}")

    # 使用YOLOv5模型进行花卉识别 - 直接处理BytesIO对象，避免重复加载
    image_io = io.BytesIO(image_bytes)
    image_for_model = Image.open(image_io)
    # 调整图片大小以提高处理速度
    image_for_model = image_for_model.resize((640, 640))
    # 更新图片尺寸信息
    image_info['image_details']['width'] = image_for_model.width
    image_info['image_details']['height'] = image_for_model.height
    
    # 使用YOLOv5模型进行花卉识别
    model_results = flower_model(image_for_model)
    
    # 解析识别结果 - 直接获取最高置信度结果
    detection_results = []
    model_data = model_results.pandas().xyxy[0]
    if not model_data.empty:
        # 直接获取置信度最高的结果
        best_result = model_data.loc[model_data['confidence'].idxmax()]
        detection_results.append({
            'name': best_result['name'],
            'confidence': float(best_result['confidence']),
            'bbox': [
                int(best_result['xmin']),
                int(best_result['ymin']),
                int(best_result['xmax']),
                int(best_result['ymax'])
            ]
        })
    
    # 返回包含识别结果和EXIF信息的响应
    return {
        'detections': detection_results,
        'exif_info': image_info
    }

if __name__ == '__main__':
    # 启动Flask服务器
    app.run(host='0.0.0.0', port=5000, debug=True)
