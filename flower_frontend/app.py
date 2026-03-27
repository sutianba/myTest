#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# 你可以在 http://127.0.0.1:5000 网站进行查看
import os
import sys
import base64
import io
from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS

# 导入图片EXIF信息提取所需模块
from PIL import Image
from PIL.ExifTags import TAGS
import exifread
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

# 导入配置
from config import (
    TEST_MODE, USE_MODEL,
    MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USE_SSL, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER,
    VERIFICATION_CODE_EXPIRY, VERIFICATION_CODE_RATE_LIMIT
)

# 导入Flask-Mail
from flask_mail import Mail, Message

# 导入数据库操作模块
if not TEST_MODE:
    try:
        from db import (
            create_user, get_user_by_username, get_user_by_id, get_user_by_email, verify_password,
            create_post, get_posts, get_post_by_id, update_post, delete_post,
            create_comment, get_comments_by_post_id, delete_comment,
            like_post, unlike_post, is_post_liked_by_user,
            like_comment, unlike_comment, is_comment_liked,
            follow_user, unfollow_user, is_following, get_user_following, get_user_followers,
            create_email_code, verify_email_code, check_email_rate_limit,
            check_user_permission,
            # 超级管理员端函数
            create_system_log, get_system_logs, record_traffic, get_traffic_stats, get_traffic_by_endpoint,
            record_server_status, get_server_status, get_latest_server_metrics,
            record_admin_operation, get_admin_operations, get_all_admins, update_user_role, get_system_summary,
            # 用户管理函数
            get_users, update_any_user_role, reset_user_password,
            # 用户端新功能
            update_user_profile, get_user_recognition_history, delete_recognition_result, save_recognition_result,
            create_album, get_user_albums, get_album_by_id, update_album, delete_album,
            add_image_to_album, get_album_images, delete_album_image, move_image_to_album, get_album_categories,
            create_feedback, get_user_feedback, get_feedback_by_id, delete_feedback,
            get_all_feedback, respond_feedback,
            create_announcement, get_announcements, update_announcement, delete_announcement,
            move_to_recycle_bin, get_recycle_bin_items, restore_from_recycle_bin,
            permanently_delete, empty_recycle_bin
        )
        db_available = True
    except Exception as e:
        print(f"数据库模块导入失败: {str(e)}")
        print("应用启动失败: 数据库初始化错误")
        raise
else:
    print("测试模式: 跳过数据库初始化")
    db_available = False

app = Flask(__name__)
CORS(app)  # 启用CORS以允许前端访问

# 配置Flask-Mail
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = MAIL_USE_SSL
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER

# 初始化Mail
mail = Mail(app)

# 打印脱敏后的邮件配置
print("===== 邮件配置信息 =====")
print(f"MAIL_SERVER: {MAIL_SERVER}")
print(f"MAIL_PORT: {MAIL_PORT}")
print(f"MAIL_USE_TLS: {MAIL_USE_TLS}")
print(f"MAIL_USE_SSL: {MAIL_USE_SSL}")
print(f"MAIL_USERNAME: {MAIL_USERNAME}")
if MAIL_PASSWORD:
    masked_password = MAIL_PASSWORD[:2] + '***' if len(MAIL_PASSWORD) > 2 else MAIL_PASSWORD + '***'
    print(f"MAIL_PASSWORD: {masked_password}")
else:
    print("MAIL_PASSWORD: 未设置")
print(f"MAIL_DEFAULT_SENDER: {MAIL_DEFAULT_SENDER}")
print("=======================")

# 定义静态文件目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# JWT配置 - 从环境变量读取密钥，如无则使用随机生成的密钥
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', os.urandom(32).hex())
app.config['JWT_EXPIRATION_DELTA'] = 60 * 60 * 24 * 365  # JWT过期时间：365天（1年）

# JWT相关导入
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# 发送验证码函数
def send_verification_email(email, code, purpose):
    """发送验证码邮件"""
    try:
        msg = Message(
            subject='植物花卉识别工具验证码',
            recipients=[email],
            sender=MAIL_DEFAULT_SENDER
        )
        
        if purpose == 'register':
            msg.body = f'您的注册验证码是：{code}\n\n验证码有效期为5分钟，请及时使用。\n\n请勿将验证码泄露给他人。'
        elif purpose == 'reset_password':
            msg.body = f'您的密码重置验证码是：{code}\n\n验证码有效期为5分钟，请及时使用。\n\n请勿将验证码泄露给他人。'
        else:
            msg.body = f'您的验证码是：{code}\n\n验证码有效期为5分钟，请及时使用。\n\n请勿将验证码泄露给他人。'
        
        mail.send(msg)
        print(f"邮件发送成功，收件邮箱: {email}")
        return True
    except Exception as e:
        import traceback
        print(f"邮件发送失败: {str(e)}")
        print(f"详细异常信息: {traceback.format_exc()}")
        return False

# 花卉名称中英文映射表
FLOWER_NAME_MAP = {
    'rose': '玫瑰',
    'tulip': '郁金香',
    'daisy': '雏菊',
    'sunflower': '向日葵',
    'dandelion': '蒲公英',
    'lily': '百合',
    'orchid': '兰花',
    'lotus': '荷花',
    'peony': '牡丹',
    'chrysanthemum': '菊花',
    'carnation': '康乃馨',
    'iris': '鸢尾花',
    'hydrangea': '绣球花',
    'lavender': '薰衣草',
    'jasmine': '茉莉花',
    'hibiscus': '木槿花',
    'magnolia': '玉兰花',
    'cherry_blossom': '樱花',
    'plum_blossom': '梅花',
    'peach_blossom': '桃花',
    'apple_blossom': '苹果花',
    'pear_blossom': '梨花',
    'apricot_blossom': '杏花',
    'azalea': '杜鹃花',
    'camellia': '山茶花',
    'gardenia': '栀子花',
    'osmanthus': '桂花',
    'narcissus': '水仙花',
    'begonia': '海棠花',
    'morning_glory': '牵牛花',
    'petunia': '矮牵牛',
    'marigold': '万寿菊',
    'pansy': '三色堇',
    'violet': '紫罗兰',
    'poppy': '罂粟花',
    'foxglove': '毛地黄',
    'lupine': '羽扇豆',
    'delphinium': '飞燕草',
    'snapdragon': '金鱼草',
    'zinnia': '百日菊',
    'cosmos': '波斯菊',
    'aster': '翠菊',
    'dahlia': '大丽花',
    'gladiolus': '唐菖蒲',
    'freesia': '小苍兰',
    'ranunculus': '花毛茛',
    'anemone': '银莲花',
    'gerbera': '非洲菊',
    'alstroemeria': '六出花',
    'lisianthus': '洋桔梗',
    'stock': '紫罗兰',
    'sweet_pea': '香豌豆',
    'clematis': '铁线莲',
    'wisteria': '紫藤花',
    'bougainvillea': '三角梅',
    'frangipani': '鸡蛋花',
    'bird_of_paradise': '鹤望兰',
    'protea': '海神花',
    'banksia': '班克木',
    'waratah': '特洛皮',
    'kangaroo_paw': '袋鼠爪花',
    'grevillea': '银桦花',
    'bottlebrush': '红千层',
    'wattle': '金合欢',
    'boronia': '波罗尼亚',
    'flannel_flower': '绒花',
    'rice_flower': '米花',
    'waxflower': '蜡花',
    'blushing_bride': '脸红新娘',
    'thryptomene': '百里香',
    'tea_tree': '茶树花',
    'leptospermum': '薄子木',
    'chamelaucium': '蜡花',
    'verticordia': '羽毛花',
    'eryngium': '刺芹',
    'scabiosa': '蓝盆花',
    'craspedia': '金槌花',
    'billy_buttons': '金球菊',
    'statice': '补血草',
    'sea_holly': '海冬青',
    'carnation_pink': '粉康乃馨',
    'carnation_red': '红康乃馨',
    'carnation_white': '白康乃馨',
    'carnation_yellow': '黄康乃馨',
    'rose_red': '红玫瑰',
    'rose_pink': '粉玫瑰',
    'rose_white': '白玫瑰',
    'rose_yellow': '黄玫瑰',
    'rose_orange': '橙玫瑰',
    'rose_purple': '紫玫瑰',
    'rose_black': '黑玫瑰',
    'rose_blue': '蓝玫瑰',
    'rose_green': '绿玫瑰',
    'lily_white': '白百合',
    'lily_pink': '粉百合',
    'lily_orange': '橙百合',
    'lily_yellow': '黄百合',
    'lily_red': '红百合',
    'tulip_red': '红郁金香',
    'tulip_pink': '粉郁金香',
    'tulip_yellow': '黄郁金香',
    'tulip_purple': '紫郁金香',
    'tulip_white': '白郁金香',
    'tulip_orange': '橙郁金香',
    'orchid_phal': '蝴蝶兰',
    'orchid_cym': '大花蕙兰',
    'orchid_dend': '石斛兰',
    'orchid_onc': '文心兰',
    'orchid_milton': '堇花兰',
    'orchid_paph': '兜兰',
    'orchid_catt': '卡特兰',
}

def get_flower_name_cn(english_name):
    """获取花卉中文名称"""
    if not english_name:
        return '未知花卉'
    return FLOWER_NAME_MAP.get(english_name.lower(), english_name)

# 加载YOLOv5模型
flower_model = None
if USE_MODEL and not TEST_MODE:
    try:
        # 使用BASE_DIR构建绝对路径
        import torch
        yolo_path = os.path.join(BASE_DIR, '..')
        model_path = os.path.join(BASE_DIR, '..', 'testflowers.pt')
        flower_model = torch.hub.load(yolo_path, 'custom', path=model_path, source='local', force_reload=True)
        flower_model.conf = 0.5  # 提高置信度阈值，只保留高置信度结果
        flower_model.iou = 0.5   # 提高NMS IOU阈值，更严格地过滤重叠边界框
        print("成功加载YOLOv5植物花卉识别工具模型")
    except Exception as e:
        print(f"无法加载YOLOv5模型: {e}")
        print("使用模拟模型进行测试...")
        # 创建一个模拟模型类，用于测试
        class MockFlowerModel:
            def __call__(self, image):
                # 模拟返回结果
                class MockResults:
                    def pandas(self):
                        class MockPandas:
                            @property
                            def xyxy(self):
                                return [type('obj', (object,), {'to_dict': lambda self, orient: []})()]
                        return MockPandas()
                return MockResults()
        flower_model = MockFlowerModel()
        flower_model.conf = 0.5
        flower_model.iou = 0.5
else:
    print("测试模式: 跳过模型加载")
    # 创建一个模拟模型类，用于测试
    class MockFlowerModel:
        def __call__(self, image):
            # 模拟返回结果
            class MockResults:
                def pandas(self):
                    class MockPandas:
                        @property
                        def xyxy(self):
                            return [type('obj', (object,), {'to_dict': lambda self, orient: []})()]
                    return MockPandas()
            return MockResults()
    flower_model = MockFlowerModel()
    flower_model.conf = 0.5
    flower_model.iou = 0.5

# JWT工具函数
def generate_jwt(user_id, username, role='user'):
    """生成JWT令牌"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': int(time.time()) + app.config['JWT_EXPIRATION_DELTA']
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def verify_jwt(token):
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError as e:
        print("JWT过期:", e)
        return None
    except jwt.InvalidTokenError as e:
        print("JWT无效:", e)
        return None
    except Exception as e:
        print("JWT验证失败:", e)
        return None

# 认证中间件
def auth_required(f):
    """认证装饰器"""
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        print("Authorization:", request.headers.get('Authorization'))
        if not token:
            return jsonify({'success': False, 'error': '未提供认证令牌'}), 401
        
        # 移除Bearer前缀
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = verify_jwt(token)
        if not payload:
            return jsonify({'success': False, 'error': '无效或过期的认证令牌'}), 401
        
        # 将用户信息存储到g对象
        g.user_id = payload['user_id']
        g.username = payload['username']
        g.role = payload.get('role', 'user')
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# 权限验证中间件
def permission_required(permission):
    """权限验证装饰器"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            # 从g对象中获取用户信息，而不是重新验证token
            if not hasattr(g, 'user_id'):
                return jsonify({'success': False, 'error': '未认证'}), 401
            
            try:
                print(f"检查权限: user_id={g.user_id}, permission={permission}")
                has_permission = check_user_permission(g.user_id, permission)
                print(f"权限检查结果: {has_permission}")
                if not has_permission:
                    return jsonify({'success': False, 'error': '权限不足'}), 403
            except Exception as e:
                print(f"检查权限时发生错误: user_id={g.user_id}, permission={permission}, error={str(e)}")
                # 权限检查失败时返回错误，不允许继续执行
                return jsonify({'success': False, 'error': '权限检查失败'}), 500
            
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

def admin_required(f):
    """管理员权限装饰器"""
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'error': '未提供认证令牌'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = verify_jwt(token)
        if not payload:
            return jsonify({'success': False, 'error': '无效或过期的认证令牌'}), 401
        
        g.user_id = payload['user_id']
        g.username = payload['username']
        g.role = payload.get('role', 'user')
        
        user_role = g.role
        if user_role not in ['super_admin', 'admin']:
            return jsonify({'success': False, 'error': '需要管理员权限'}), 403
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    """返回指定的文件"""
    return send_from_directory(BASE_DIR, filename)

@app.route('/api/detect', methods=['POST'])
def detect_flower():
    """植物花卉识别工具 API 接口"""
    try:
        data = request.get_json()
        
        print(f"\n=== /api/detect 请求信息 ===")
        print(f"请求数据：{data}")
        print(f"save_to_album = {data.get('save_to_album', False)}")
        
        user_id = None
        token = request.headers.get('Authorization')
        if token:
            if token.startswith('Bearer '):
                token = token[7:]
            payload = verify_jwt(token)
            if payload:
                user_id = payload.get('user_id')
                print(f"user_id = {user_id}")
        
        save_to_album = data.get('save_to_album', False)
        print(f"解析后的 save_to_album = {save_to_album}")
        print(f"===========================\n")
        
        if 'image' in data:
            image_data = data['image']
            results = process_single_image(image_data, user_id, save_to_album)
            return jsonify({'success': True, 'results': results})
        elif 'images' in data:
            images_data = data['images']
            all_results = []
            
            for i, image_data in enumerate(images_data):
                results = process_single_image(image_data, user_id, save_to_album)
                all_results.append({
                    'image_index': i,
                    'results': results
                })
            
            return jsonify({'success': True, 'all_results': all_results})
        else:
            return jsonify({'success': False, 'error': '缺少图片数据'}), 400

    except Exception as e:
        print(f"识别过程中发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


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


def get_address_from_coordinates(lat, lon, max_retries=3):
    """
    通过经纬度获取地址信息
    使用geopy和Nominatim服务进行逆地理编码
    """
    geolocator = Nominatim(user_agent="flower_recognition_app", timeout=10)
    
    # 重试机制
    for attempt in range(max_retries):
        try:
            location = geolocator.reverse((lat, lon), language='zh-CN')
            if location:
                return location.raw.get('address', {})
            return None
        except GeocoderTimedOut:
            print(f"地理编码请求超时，第 {attempt + 1} 次尝试...")
            time.sleep(1)
        except GeocoderServiceError as e:
            print(f"地理编码服务错误: {e}，第 {attempt + 1} 次尝试...")
            time.sleep(1)
        except Exception as e:
            print(f"获取地址信息时出错: {e}")
            break
    
    print("多次尝试后仍无法获取地址信息")
    return None


def format_address(address):
    """格式化地址信息，提取关键部分"""
    if not address:
        return "地址信息不可用"
    
    # 尝试提取关键地址组件
    country = address.get('country', '未知国家')
    province = address.get('state', '') or address.get('province', '') or '未知省份'
    city = address.get('city', '') or address.get('district', '') or '未知城市'
    town = address.get('town', '') or address.get('county', '') or ''
    street = address.get('road', '') or address.get('street', '') or ''
    number = address.get('house_number', '')
    
    # 构建完整地址
    address_parts = [country, province, city]
    if town:
        address_parts.append(town)
    if street:
        address_parts.append(street)
        if number:
            address_parts.append(number)
    
    # 移除空字符串并连接
    return '，'.join(filter(None, address_parts))


def get_season(month):
    """根据月份获取季节"""
    if 3 <= month <= 5:
        return "春季"
    elif 6 <= month <= 8:
        return "夏季"
    elif 9 <= month <= 11:
        return "秋季"
    else:
        return "冬季"

def process_single_image(image_data, user_id=None, save_to_album=False):
    """处理单个图片的识别"""
    print(f"process_single_image called with save_to_album={save_to_album}, user_id={user_id}")
    # 测试模式下的处理
    if TEST_MODE:
        # 移除base64头部
        if image_data.startswith('data:image/'):
            image_data = image_data.split(',')[1]

        # 解码base64图片数据
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        # 调整图片大小以提高处理速度
        image = image.resize((640, 640))
        
        # 提取图片EXIF信息
        image_info = {
            'date_time': "2024:03:15 10:30:00",
            'location': {
                'has_location': True,
                'latitude': 39.9042,
                'longitude': 116.4074,
                'formatted_address': "北京市",
                'raw_gps': None
            },
            'camera_info': {
                'make': "未知",
                'model': "未知"
            },
            'image_details': {
                'width': image.width,
                'height': image.height
            }
        }
        
        # 模拟识别结果
        detection_results = [{
            'name': '测试花卉',
            'confidence': 0.95,
            'bbox': [100, 100, 200, 200]
        }]
        
        # 生成分类信息
        shoot_time = image_info['date_time']
        shoot_year = 2024
        shoot_month = 3
        shoot_season = "春季"
        latitude = image_info['location']['latitude']
        longitude = image_info['location']['longitude']
        location_text = image_info['location']['formatted_address']
        region_label = "华北地区"
        
        # 生成分类标签
        classification_tags = ["测试花卉", shoot_season, region_label]
        final_category = "-".join(classification_tags)
        
        # 返回包含识别结果和EXIF信息的响应
        return_result = {
            'detections': detection_results,
            'exif_info': image_info,
            'test_mode': True,
            'message': '测试模式下的模拟识别结果',
            'shoot_time': shoot_time,
            'shoot_year': shoot_year,
            'shoot_month': shoot_month,
            'shoot_season': shoot_season,
            'latitude': latitude,
            'longitude': longitude,
            'location_text': location_text,
            'region_label': region_label,
            'classification_tags': classification_tags,
            'final_category': final_category
        }
        
        return return_result
    
    # 正式模式下的处理
    saved_album_info = None
    
    # 移除base64头部
    if image_data.startswith('data:image/'):
        image_data = image_data.split(',')[1]

    # 解码base64图片数据
    image_bytes = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(image_bytes))
    # 调整图片大小以提高处理速度
    image = image.resize((640, 640))
    
    # 提取图片EXIF信息
    image_info = {
        'date_time': "未知",
        'location': {
            'has_location': False,
            'latitude': None,
            'longitude': None,
            'formatted_address': "无GPS信息",
            'raw_gps': None
        },
        'camera_info': {
            'make': "未知",
            'model': "未知"
        },
        'image_details': {
            'width': image.width,
            'height': image.height
        }
    }
    
    # 初始化分类信息
    shoot_time = "未获取到"
    shoot_year = None
    shoot_month = None
    shoot_season = "未获取到"
    latitude = None
    longitude = None
    location_text = "未获取到"
    region_label = "未获取到"
    
    try:
        # 创建临时文件保存图片
        temp_file_path = "temp_image.jpg"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(image_bytes)
        
        # 使用exifread提取EXIF信息
        with open(temp_file_path, 'rb') as f:
            exif_tags = exifread.process_file(f)
            
            # 获取拍摄时间
            if 'EXIF DateTimeOriginal' in exif_tags:
                shoot_time = str(exif_tags['EXIF DateTimeOriginal'])
            elif 'Image DateTime' in exif_tags:
                shoot_time = str(exif_tags['Image DateTime'])
            elif 'EXIF DateTimeDigitized' in exif_tags:
                shoot_time = str(exif_tags['EXIF DateTimeDigitized'])
            
            # 解析拍摄时间
            if shoot_time != "未获取到":
                try:
                    # 格式：2024:03:15 10:30:00
                    date_part = shoot_time.split(' ')[0]
                    year, month, day = map(int, date_part.split(':'))
                    shoot_year = year
                    shoot_month = month
                    shoot_season = get_season(month)
                except Exception as e:
                    print(f"解析时间失败: {e}")
        
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
                
                # 获取地址信息
                address = get_address_from_coordinates(dec_lat, dec_lon)
                formatted_address = format_address(address)
                
                # 更新位置信息
                image_info['location'] = {
                    'has_location': True,
                    'latitude': dec_lat,
                    'longitude': dec_lon,
                    'formatted_address': formatted_address,
                    'raw_gps': {
                        'lat_ref': lat_ref,
                        'lat': str(lat),
                        'lon_ref': lon_ref,
                        'lon': str(lon)
                    }
                }
                
                # 更新分类信息
                latitude = dec_lat
                longitude = dec_lon
                location_text = formatted_address
                
                # 简单的区域标签生成
                if latitude is not None and longitude is not None:
                    if 32 <= latitude <= 42 and 110 <= longitude <= 122:
                        region_label = "华北地区"
                    elif 23 <= latitude <= 32 and 108 <= longitude <= 123:
                        region_label = "华南地区"
                    elif 32 <= latitude <= 40 and 105 <= longitude <= 115:
                        region_label = "西北地区"
                    elif 42 <= latitude <= 53 and 120 <= longitude <= 135:
                        region_label = "东北地区"
                    else:
                        region_label = "其他地区"
            except Exception as e:
                print(f"处理GPS信息时出错: {e}")
        
        # 删除临时文件
        os.remove(temp_file_path)
    except Exception as e:
        print(f"提取图片EXIF信息失败: {e}")

    # 使用YOLOv5模型进行植物花卉识别
    model_results = flower_model(image)
    
    # 解析识别结果
    results = []
    for result in model_results.pandas().xyxy[0].to_dict(orient='records'):
        english_name = result['name']
        chinese_name = get_flower_name_cn(english_name)
        results.append({
            'name': chinese_name,
            'name_en': english_name,
            'confidence': round(result['confidence'], 4),
            'bbox': [
                int(result['xmin']),
                int(result['ymin']),
                int(result['xmax']),
                int(result['ymax'])
            ]
        })
    
    # 处理识别结果：只保留置信度最高的结果
    detection_results = []
    flower_type = "未识别"
    confidence = 0.0
    classification_tags = []
    final_category = "未识别"
    
    if results:
        # 按置信度降序排序
        results.sort(key=lambda x: x['confidence'], reverse=True)
        # 只添加置信度最高的结果
        top_result = results[0]
        detection_results.append({
            'name': top_result['name'],
            'name_en': top_result.get('name_en', ''),
            'confidence': float(top_result['confidence']),
            'bbox': top_result['bbox']
        })
        flower_type = top_result['name']
        confidence = top_result['confidence']
        
        # 生成分类标签
        classification_tags = [flower_type]
        if shoot_season != "未获取到":
            classification_tags.append(shoot_season)
        if region_label != "未获取到":
            classification_tags.append(region_label)
        
        # 生成最终分类
        final_category = "-".join(classification_tags)
    
    # 更新image_info
    image_info['date_time'] = shoot_time
    
    # 返回包含识别结果和EXIF信息的响应
    return_result = {
        'detections': detection_results,
        'exif_info': image_info,
        'flower_type': flower_type,
        'confidence': confidence,
        'shoot_time': shoot_time,
        'shoot_year': shoot_year,
        'shoot_month': shoot_month,
        'shoot_season': shoot_season,
        'latitude': latitude,
        'longitude': longitude,
        'location_text': location_text,
        'region_label': region_label,
        'classification_tags': classification_tags,
        'final_category': final_category
    }
    
    if save_to_album and user_id:
        print(f"开始保存到相册: save_to_album={save_to_album}, user_id={user_id}, detection_results={detection_results}")
        try:
            # 1. 确定花卉名称和置信度
            flower_name = None
            confidence = None
            if detection_results:
                flower_name = detection_results[0]['name']
                confidence = detection_results[0]['confidence']
                final_category = flower_name
            else:
                flower_name = "未知花卉"
                confidence = 0.0
                final_category = "未知"
            
            # 2. 保存图片文件
            timestamp = int(time.time())
            image_filename = f"recognition_{user_id}_{timestamp}.jpg"
            uploads_dir = os.path.join(BASE_DIR, 'static', 'uploads', 'recognition')
            os.makedirs(uploads_dir, exist_ok=True)
            image_path = os.path.join(uploads_dir, image_filename)
            
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
            
            relative_path = f"/static/uploads/recognition/{image_filename}"
            print(f"保存图片成功, relative_path={relative_path}")
            
            # 3. 保存识别结果
            print(f"保存识别结果: user_id={user_id}, relative_path={relative_path}, flower_name={flower_name}, confidence={confidence}")

            # 获取相机信息和图片尺寸
            camera_make = image_info.get('camera_info', {}).get('make')
            camera_model = image_info.get('camera_info', {}).get('model')
            image_width = image_info.get('image_details', {}).get('width')
            image_height = image_info.get('image_details', {}).get('height')

            result_id = save_recognition_result(
                user_id,
                relative_path,
                flower_name,
                confidence,
                shoot_time=shoot_time,
                shoot_year=shoot_year,
                shoot_month=shoot_month,
                shoot_season=shoot_season,
                latitude=latitude,
                longitude=longitude,
                location_text=location_text,
                region_label=region_label,
                final_category=final_category,
                camera_make=camera_make,
                camera_model=camera_model,
                image_width=image_width,
                image_height=image_height
            )
            print(f"保存识别结果成功, result_id={result_id}")
            
            # 4. 处理相册逻辑
            album = None
            if detection_results:
                # 有识别结果，尝试按花卉分类保存
                print(f"获取用户相册: user_id={user_id}, flower_name={flower_name}")
                albums = get_user_albums(user_id, flower_name)
                print(f"获取到相册: {albums}")
                
                if albums:
                    album = albums[0]
                    print(f"使用现有相册: {album}")
                else:
                    print(f"创建新相册: user_id={user_id}, name={flower_name}相册, category={flower_name}")
                    album_id = create_album(user_id, f"{flower_name}相册", flower_name)
                    print(f"创建相册成功, album_id={album_id}")
                    album = get_album_by_id(album_id, user_id)
                    print(f"获取新相册: {album}")
            
            # 5. 添加图片到相册（如果没有相册，add_image_to_album会自动创建默认相册）
            album_id = album['id'] if album else None
            print(f"添加图片到相册: album_id={album_id}, user_id={user_id}, relative_path={relative_path}, flower_name={flower_name}, confidence={confidence}, result_id={result_id}")
            image_id = add_image_to_album(album_id, user_id, relative_path, flower_name, confidence, result_id)
            
            if image_id:
                print(f"添加图片到相册成功")
                # 获取最终使用的相册信息
                if not album:
                    # 使用了默认相册，获取默认相册信息
                    from db import get_user_albums as db_get_user_albums
                    default_albums = db_get_user_albums(user_id, '默认')
                    if default_albums:
                        album = default_albums[0]
                
                saved_album_info = {
                    'album_id': album['id'] if album else '默认相册',
                    'album_name': album['name'] if album else '默认相册',
                    'category': album['category'] if album else '默认',
                    'image_path': relative_path
                }
                
                return_result['saved_to_album'] = saved_album_info
                print(f"保存到相册完成, saved_album_info={saved_album_info}")
            else:
                print("图片已存在于相册中，跳过保存")
        except Exception as e:
            print(f"保存到相册失败: {e}")
            import traceback
            traceback.print_exc()
            return_result['save_error'] = str(e)
    else:
        print(f"不保存到相册: save_to_album={save_to_album}, user_id={user_id}")
    
    return return_result

# 认证相关API
@app.route('/api/auth/send-code', methods=['POST'])
def send_verification_code():
    """发送验证码"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持发送验证码'}), 503
    
    try:
        data = request.get_json()
        email = data.get('email')
        purpose = data.get('purpose')  # register 或 reset_password
        
        if not email or not purpose:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        if purpose not in ['register', 'reset_password']:
            return jsonify({'success': False, 'error': '无效的验证码用途'}), 400
        
        # 检查频率限制
        if check_email_rate_limit(email, purpose, VERIFICATION_CODE_RATE_LIMIT):
            return jsonify({'success': False, 'error': '发送验证码过于频繁，请稍后再试'}), 429
        
        # 对于密码重置，检查邮箱是否存在且对应管理员账号
        if purpose == 'reset_password':
            user = get_user_by_email(email)
            if not user:
                return jsonify({'success': False, 'error': '邮箱不存在'}), 400
            if user['role'] != 'admin':
                return jsonify({'success': False, 'error': '只有管理员可以通过邮箱重置密码'}), 400
        
        # 生成并保存验证码
        code = create_email_code(email, purpose, VERIFICATION_CODE_EXPIRY)
        
        # 发送验证码邮件
        if not send_verification_email(email, code, purpose):
            return jsonify({'success': False, 'error': '发送验证码失败，请检查SMTP配置或网络连接'}), 500
        
        return jsonify({'success': True, 'message': '验证码已发送，请查收邮箱'})
    except Exception as e:
        import traceback
        print(f"发送验证码过程中发生错误: {str(e)}")
        print(f"详细异常信息: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'发送验证码失败: {str(e)}'}), 500

@app.route('/api/test_email', methods=['POST'])
def test_email():
    """测试邮件发送功能"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持发送邮件'}), 503
    
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': '缺少邮箱参数'}), 400
        
        # 生成测试验证码
        import random
        import string
        code = ''.join(random.choices(string.digits, k=6))
        
        # 发送测试邮件
        if not send_verification_email(email, code, 'test'):
            return jsonify({'success': False, 'error': '邮件发送失败，请检查SMTP配置或网络连接'}), 500
        
        return jsonify({'success': True, 'message': '测试邮件已发送，请查收邮箱'})
    except Exception as e:
        import traceback
        print(f"测试邮件发送过程中发生错误: {str(e)}")
        print(f"详细异常信息: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'测试邮件发送失败: {str(e)}'}), 500

@app.route('/api/upload/post-image', methods=['POST'])
@auth_required
def upload_post_image():
    """上传帖子图片"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持上传图片'}), 503
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '缺少文件参数'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'}), 400
        
        # 检查文件类型
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return jsonify({'success': False, 'error': '只支持图片文件'}), 400
        
        # 确保上传目录存在
        upload_dir = os.path.join(BASE_DIR, 'static', 'uploads', 'posts')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        # 添加时间戳，避免文件名冲突
        timestamp = int(time.time())
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(upload_dir, filename)
        
        # 保存文件
        file.save(filepath)
        
        # 生成相对路径，用于存储到数据库
        relative_path = f"/static/uploads/posts/{filename}"
        
        return jsonify({'success': True, 'image_url': relative_path})
    except Exception as e:
        import traceback
        print(f"上传图片时发生错误: {str(e)}")
        print(f"详细异常信息: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'上传失败: {str(e)}'}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持注册功能'}), 503
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role', 'user')
        code = data.get('code')  # 验证码
        
        # 验证角色值
        if role not in ['user', 'admin']:
            return jsonify({'success': False, 'error': '无效的角色'}), 400
        
        # 验证必填字段
        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
        
        # 管理员注册时邮箱和验证码必填
        if role == 'admin':
            if not email:
                return jsonify({'success': False, 'error': '管理员注册时邮箱不能为空'}), 400
            if not code:
                return jsonify({'success': False, 'error': '管理员注册时验证码不能为空'}), 400
            
            # 验证验证码
            if not verify_email_code(email, code, 'register'):
                return jsonify({'success': False, 'error': '验证码无效或已过期'}), 400
        
        # 检查用户名是否已存在
        if get_user_by_username(username):
            return jsonify({'success': False, 'error': '用户名已存在'}), 400
        
        # 检查邮箱是否已存在（如果提供了邮箱）
        if email and get_user_by_email(email):
            return jsonify({'success': False, 'error': '邮箱已存在'}), 400
        
        # 创建用户
        user_id = create_user(username, email, password, role)
        
        # 生成JWT令牌（包含角色信息）
        token = generate_jwt(user_id, username, role)
        
        return jsonify({'success': True, 'user_id': user_id, 'username': username, 'role': role, 'token': token, 'message': f'{"管理员" if role == "admin" else "普通用户"}注册成功'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        print(f"注册过程中发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持登录功能'}), 503
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        # 获取用户
        user = get_user_by_username(username)
        if not user:
            return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
        
        # 验证密码
        if not verify_password(user['password'], password):
            return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
        
        # 获取用户角色
        user_role = user.get('role', 'user')
        
        # 生成JWT令牌（包含角色信息）
        token = generate_jwt(user['id'], user['username'], user_role)
        
        return jsonify({
            'success': True, 
            'user_id': user['id'], 
            'username': user['username'], 
            'role': user_role,
            'token': token
        })
    except Exception as e:
        print(f"登录过程中发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """重置密码"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持重置密码'}), 503
    
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')
        new_password = data.get('new_password')
        
        if not email or not code or not new_password:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        # 验证验证码
        if not verify_email_code(email, code, 'reset_password'):
            return jsonify({'success': False, 'error': '验证码无效或已过期'}), 400
        
        # 获取用户
        user = get_user_by_email(email)
        if not user:
            return jsonify({'success': False, 'error': '用户不存在'}), 400
        
        if user['role'] != 'admin':
            return jsonify({'success': False, 'error': '只有管理员可以通过邮箱重置密码'}), 400
        
        # 生成新密码哈希
        password_hash = generate_password_hash(new_password)
        
        # 更新密码
        update_user_profile(user['id'], password_hash=password_hash)
        
        return jsonify({'success': True, 'message': '密码重置成功，请使用新密码登录'})
    except Exception as e:
        print(f"重置密码过程中发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 帖子相关API
@app.route('/api/posts', methods=['GET'])
def get_posts_api():
    """获取帖子列表"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持获取帖子功能'}), 503
    
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        posts = get_posts(limit, offset)
        return jsonify({'success': True, 'posts': posts})
    except Exception as e:
        print(f"获取帖子列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post_api(post_id):
    """获取帖子详情"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持获取帖子详情功能'}), 503
    
    try:
        post = get_post_by_id(post_id)
        if not post:
            return jsonify({'success': False, 'error': '帖子不存在'}), 404
        
        return jsonify({'success': True, 'post': post})
    except Exception as e:
        print(f"获取帖子详情时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/posts', methods=['POST'])
@auth_required
@permission_required('create_posts')
def create_post_api():
    """创建帖子"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持创建帖子功能'}), 503
    
    try:
        data = request.get_json()
        content = data.get('content')
        image_url = data.get('image_url')
        topics = data.get('topics')
        tags = data.get('tags')
        source_type = data.get('source_type')
        source_id = data.get('source_id')
        
        if not content:
            return jsonify({'success': False, 'error': '帖子内容不能为空'}), 400
        
        # 如果有来源信息，检查权限
        if source_type and source_id:
            if source_type == 'recognition':
                # 检查识别记录是否属于当前用户
                from db import get_recognition_result
                result = get_recognition_result(source_id)
                if not result or result.get('user_id') != g.user_id:
                    return jsonify({'success': False, 'error': '无权限分享此识别记录'}), 403
        
        post_id = create_post(g.user_id, content, image_url, topics, tags, source_type, source_id)
        
        return jsonify({'success': True, 'post_id': post_id})
    except Exception as e:
        print(f"创建帖子时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
@auth_required
def update_post_api(post_id):
    """更新帖子"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持更新帖子功能'}), 503
    
    try:
        data = request.get_json()
        content = data.get('content')
        image_url = data.get('image_url')
        
        if not content:
            return jsonify({'success': False, 'error': '帖子内容不能为空'}), 400
        
        # 获取帖子信息
        post = get_post_by_id(post_id)
        if not post:
            return jsonify({'success': False, 'error': '帖子不存在'}), 404
        
        # 检查权限（只有帖子作者可以更新）
        if post['user_id'] != g.user_id:
            return jsonify({'success': False, 'error': '无权限更新此帖子'}), 403
        
        update_post(post_id, content, image_url)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"更新帖子时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@auth_required
def delete_post_api(post_id):
    """删除帖子"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持删除帖子功能'}), 503
    
    try:
        post = get_post_by_id(post_id)
        if not post:
            return jsonify({'success': False, 'error': '帖子不存在'}), 404
        
        is_admin = g.role in ['super_admin', 'admin']
        if post['user_id'] != g.user_id and not is_admin:
            return jsonify({'success': False, 'error': '无权限删除此帖子'}), 403
        
        reason = '管理员删除' if is_admin and post['user_id'] != g.user_id else '用户删除'
        move_to_recycle_bin(g.user_id if not is_admin else post['user_id'], 'post', post_id, {'content': post['content'], 'image_url': post.get('image_url'), 'delete_reason': reason})
        delete_post(post_id)
        
        if is_admin and post['user_id'] != g.user_id:
            ip_address = request.remote_addr
            record_admin_operation(g.user_id, g.username, 'delete_post', 'post', post_id, f'删除用户帖子: {post["content"][:30]}...', ip_address)
        
        return jsonify({'success': True, 'message': '帖子已移入回收站'})
    except Exception as e:
        print(f"删除帖子时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 评论相关API
@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_comments_api(post_id):
    """获取帖子评论"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持获取评论功能'}), 503
    
    try:
        comments = get_comments_by_post_id(post_id)
        return jsonify({'success': True, 'comments': comments})
    except Exception as e:
        print(f"获取评论时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@auth_required
@permission_required('comment_posts')
def create_comment_api(post_id):
    """创建评论"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持创建评论功能'}), 503
    
    try:
        data = request.get_json()
        content = data.get('content')
        parent_comment_id = data.get('parent_comment_id')
        reply_to_user_id = data.get('reply_to_user_id')
        
        if not content:
            return jsonify({'success': False, 'error': '评论内容不能为空'}), 400
        
        # 检查帖子是否存在
        post = get_post_by_id(post_id)
        if not post:
            return jsonify({'success': False, 'error': '帖子不存在'}), 404
        
        comment_id = create_comment(post_id, g.user_id, content, parent_comment_id, reply_to_user_id)
        
        return jsonify({'success': True, 'comment_id': comment_id})
    except Exception as e:
        print(f"创建评论时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/comments', methods=['POST'])
@auth_required
@permission_required('comment_posts')
def create_comment_api_new():
    """创建评论（新接口）"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持创建评论功能'}), 503
    
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        content = data.get('content')
        parent_comment_id = data.get('parent_comment_id')
        reply_to_user_id = data.get('reply_to_user_id')
        
        if not post_id or not content:
            return jsonify({'success': False, 'error': '帖子ID和评论内容不能为空'}), 400
        
        # 检查帖子是否存在
        post = get_post_by_id(post_id)
        if not post:
            return jsonify({'success': False, 'error': '帖子不存在'}), 404
        
        comment_id = create_comment(post_id, g.user_id, content, parent_comment_id, reply_to_user_id)
        
        return jsonify({'success': True, 'comment_id': comment_id})
    except Exception as e:
        print(f"创建评论时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@auth_required
def delete_comment_api(comment_id):
    """删除评论"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持删除评论功能'}), 503
    
    try:
        # 这里简化处理，实际应该检查评论是否存在以及用户是否有权限删除
        delete_comment(comment_id)
        return jsonify({'success': True})
    except Exception as e:
        print(f"删除评论时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 评论点赞相关API
@app.route('/api/comments/<int:comment_id>/like', methods=['POST'])
@auth_required
def like_comment_api(comment_id):
    """点赞评论"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持点赞功能'}), 503
    
    try:
        # 检查评论是否存在
        comment = get_comment_by_id(comment_id)
        if not comment:
            return jsonify({'success': False, 'error': '评论不存在'}), 404
        
        result = like_comment(comment_id, g.user_id)
        if result:
            return jsonify({'success': True, 'message': '点赞成功'})
        else:
            return jsonify({'success': False, 'error': '已经点赞过了'}), 400
    except Exception as e:
        print(f"点赞评论时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/comments/<int:comment_id>/unlike', methods=['POST'])
@auth_required
def unlike_comment_api(comment_id):
    """取消点赞评论"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持取消点赞功能'}), 503
    
    try:
        # 检查评论是否存在
        comment = get_comment_by_id(comment_id)
        if not comment:
            return jsonify({'success': False, 'error': '评论不存在'}), 404
        
        result = unlike_comment(comment_id, g.user_id)
        if result:
            return jsonify({'success': True, 'message': '取消点赞成功'})
        else:
            return jsonify({'success': False, 'error': '没有点赞记录'}), 400
    except Exception as e:
        print(f"取消点赞时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 点赞相关API
@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@auth_required
def like_post_api(post_id):
    """点赞帖子"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持点赞功能'}), 503
    
    try:
        # 检查帖子是否存在
        post = get_post_by_id(post_id)
        if not post:
            return jsonify({'success': False, 'error': '帖子不存在'}), 404
        
        like_post(post_id, g.user_id)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"点赞时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>/unlike', methods=['POST'])
@auth_required
def unlike_post_api(post_id):
    """取消点赞"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持取消点赞功能'}), 503
    
    try:
        # 检查帖子是否存在
        post = get_post_by_id(post_id)
        if not post:
            return jsonify({'success': False, 'error': '帖子不存在'}), 404
        
        unlike_post(post_id, g.user_id)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"取消点赞时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>/is_liked', methods=['GET'])
@auth_required
def is_post_liked_api(post_id):
    """检查帖子是否被当前用户点赞"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持检查点赞状态功能'}), 503
    
    try:
        is_liked = is_post_liked_by_user(post_id, g.user_id)
        
        return jsonify({'success': True, 'is_liked': is_liked})
    except Exception as e:
        print(f"检查点赞状态时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 关注相关API
@app.route('/api/users/<int:user_id>/follow', methods=['POST'])
@auth_required
def follow_user_api(user_id):
    """关注用户"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持关注用户功能'}), 503
    
    try:
        # 不能关注自己
        if user_id == g.user_id:
            return jsonify({'success': False, 'error': '不能关注自己'}), 400
        
        follow_user(g.user_id, user_id)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"关注用户时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/unfollow', methods=['POST'])
@auth_required
def unfollow_user_api(user_id):
    """取消关注用户"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持取消关注用户功能'}), 503
    
    try:
        unfollow_user(g.user_id, user_id)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"取消关注时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/is_following', methods=['GET'])
@auth_required
def is_following_api(user_id):
    """检查是否关注了指定用户"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持检查关注状态功能'}), 503
    
    try:
        is_following_status = is_following(g.user_id, user_id)
        
        return jsonify({'success': True, 'is_following': is_following_status})
    except Exception as e:
        print(f"检查关注状态时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/following', methods=['GET'])
def get_user_following_api(user_id):
    """获取用户关注的人"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持获取关注列表功能'}), 503
    
    try:
        following = get_user_following(user_id)
        
        return jsonify({'success': True, 'following': following})
    except Exception as e:
        print(f"获取关注列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/followers', methods=['GET'])
def get_user_followers_api(user_id):
    """获取用户的粉丝"""
    if TEST_MODE:
        return jsonify({'success': False, 'error': '测试模式下不支持获取粉丝列表功能'}), 503
    
    try:
        followers = get_user_followers(user_id)
        
        return jsonify({'success': True, 'followers': followers})
    except Exception as e:
        print(f"获取粉丝列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================================
# 超级管理员端API接口
# ========================================

@app.route('/api/admin/system/summary', methods=['GET'])
@auth_required
@permission_required('admin')
def get_system_summary_api():
    """获取系统概要统计"""
    try:
        summary = get_system_summary()
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        print(f"获取系统概要统计时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/system/logs', methods=['GET'])
@auth_required
@permission_required('view_system_logs')
def get_system_logs_api():
    """获取系统日志"""
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        log_level = request.args.get('log_level')
        module = request.args.get('module')
        start_time = request.args.get('start_time', type=int)
        end_time = request.args.get('end_time', type=int)
        
        logs = get_system_logs(limit, offset, log_level, module, start_time, end_time)
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        print(f"获取系统日志时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/system/traffic', methods=['GET'])
@auth_required
@permission_required('view_traffic_stats')
def get_traffic_stats_api():
    """获取流量统计"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 100))
        
        stats = get_traffic_stats(start_date, end_date, limit)
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        print(f"获取流量统计时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/system/traffic/endpoints', methods=['GET'])
@auth_required
@permission_required('view_traffic_stats')
def get_traffic_by_endpoint_api():
    """按端点获取流量统计"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 20))
        
        stats = get_traffic_by_endpoint(start_date, end_date, limit)
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        print(f"获取端点流量统计时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/server/status', methods=['GET'])
@auth_required
@permission_required('monitor_server')
def get_server_status_api():
    """获取服务器状态"""
    try:
        metric_name = request.args.get('metric_name')
        limit = int(request.args.get('limit', 100))
        
        status = get_server_status(metric_name, limit)
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        print(f"获取服务器状态时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/server/metrics', methods=['GET'])
@auth_required
@permission_required('monitor_server')
def get_latest_server_metrics_api():
    """获取最新服务器指标"""
    try:
        metrics = get_latest_server_metrics()
        return jsonify({'success': True, 'metrics': metrics})
    except Exception as e:
        print(f"获取最新服务器指标时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/admins', methods=['GET'])
@auth_required
@permission_required('manage_admins')
def get_all_admins_api():
    """获取所有管理员"""
    try:
        admins = get_all_admins()
        return jsonify({'success': True, 'admins': admins})
    except Exception as e:
        print(f"获取管理员列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/admins/<int:user_id>/role', methods=['PUT'])
@auth_required
@permission_required('manage_admins')
def update_user_role_api(user_id):
    """更新用户角色"""
    try:
        data = request.get_json()
        role_name = data.get('role_name')
        
        if not role_name:
            return jsonify({'success': False, 'error': '缺少角色名称'}), 400
        
        success = update_user_role(user_id, role_name)
        
        # 记录管理员操作
        ip_address = request.remote_addr
        record_admin_operation(g.user_id, g.username, 'update_role', 'user', user_id, f'更新用户角色为 {role_name}', ip_address)
        
        return jsonify({'success': True, 'message': '角色更新成功'})
    except Exception as e:
        print(f"更新用户角色时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
@auth_required
@permission_required('manage_admins')
def get_users_api():
    """获取用户列表（支持搜索和分页）"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit
        search = request.args.get('search', '')
        role = request.args.get('role', '')
        
        users, total = get_users(search, role, limit, offset)
        return jsonify({'success': True, 'users': users, 'total': total})
    except Exception as e:
        print(f"获取用户列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
@auth_required
@permission_required('manage_admins')
def update_any_user_role_api(user_id):
    """更新任意用户角色（管理员功能）"""
    try:
        data = request.get_json()
        role = data.get('role')
        
        if not role:
            return jsonify({'success': False, 'error': '缺少角色参数'}), 400
        
        # 更新用户角色
        success = update_any_user_role(user_id, role)
        
        if success:
            # 记录管理员操作
            ip_address = request.remote_addr
            record_admin_operation(g.user_id, g.username, 'update_user_role', 'user', user_id, f'更新用户角色为 {role}', ip_address)
            return jsonify({'success': True, 'message': '角色更新成功'})
        else:
            return jsonify({'success': False, 'error': '角色更新失败'}), 500
    except Exception as e:
        print(f"更新用户角色时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/password', methods=['PUT'])
@auth_required
@permission_required('manage_admins')
def reset_user_password_api(user_id):
    """重置用户密码（管理员功能）"""
    try:
        data = request.get_json()
        new_password = data.get('password')
        
        if not new_password:
            return jsonify({'success': False, 'error': '缺少密码参数'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': '密码长度至少为6位'}), 400
        
        # 重置密码
        success = reset_user_password(user_id, new_password)
        
        if success:
            # 记录管理员操作
            ip_address = request.remote_addr
            record_admin_operation(g.user_id, g.username, 'reset_password', 'user', user_id, '重置用户密码', ip_address)
            return jsonify({'success': True, 'message': '密码重置成功'})
        else:
            return jsonify({'success': False, 'error': '密码重置失败'}), 500
    except Exception as e:
        print(f"重置用户密码时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/operations', methods=['GET'])
@auth_required
@permission_required('view_operations')
def get_admin_operations_api():
    """获取管理员操作记录（超级管理员可查看所有，普通管理员只能查看自己的）"""
    try:
        admin_id = request.args.get('admin_id', type=int)
        operation_type = request.args.get('operation_type')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # 如果不是超级管理员，只能查看自己的操作记录
        if g.role != 'super_admin':
            admin_id = g.user_id
        
        operations = get_admin_operations(admin_id, operation_type, limit, offset)
        return jsonify({'success': True, 'operations': operations})
    except Exception as e:
        print(f"获取管理员操作记录时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
@auth_required
def get_user_profile():
    """获取当前用户个人信息"""
    try:
        user = get_user_by_id(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': '用户不存在'}), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'created_at': user['created_at']
            }
        })
    except Exception as e:
        print(f"获取用户信息时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/profile', methods=['PUT'])
@auth_required
def update_user_profile_api():
    """更新当前用户个人信息"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        password_hash = None
        if password:
            password_hash = generate_password_hash(password)
        
        success = update_user_profile(g.user_id, email=email, password_hash=password_hash)
        
        if success:
            return jsonify({'success': True, 'message': '个人信息更新成功'})
        else:
            return jsonify({'success': False, 'error': '更新失败'})
    except Exception as e:
        print(f"更新用户信息时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recognition/history', methods=['GET'])
@auth_required
def get_recognition_history():
    """获取用户历史识别记录"""
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        results, total = get_user_recognition_history(g.user_id, limit, offset)
        
        return jsonify({
            'success': True,
            'results': results,
            'total': total
        })
    except Exception as e:
        print(f"获取历史识别记录时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recognition/results/<int:result_id>', methods=['DELETE'])
@auth_required
def delete_recognition_result_api(result_id):
    """删除识别记录"""
    try:
        results, _ = get_user_recognition_history(g.user_id)
        result_info = None
        for r in results:
            if r['id'] == result_id:
                result_info = r
                break

        if result_info:
            move_to_recycle_bin(g.user_id, 'recognition', result_id, {
                'image_path': result_info.get('image_path'),
                'result': result_info.get('result'),
                'confidence': result_info.get('confidence'),
                'shoot_time': result_info.get('shoot_time'),
                'shoot_month': result_info.get('shoot_month'),
                'shoot_season': result_info.get('shoot_season'),
                'location_text': result_info.get('location_text'),
                'region_label': result_info.get('region_label'),
                'camera_make': result_info.get('camera_make'),
                'camera_model': result_info.get('camera_model'),
                'image_width': result_info.get('image_width'),
                'image_height': result_info.get('image_height'),
                'final_category': result_info.get('final_category')
            })

        success = delete_recognition_result(result_id, g.user_id)

        if success:
            return jsonify({'success': True, 'message': '记录已移入回收站'})
        else:
            return jsonify({'success': False, 'error': '删除失败或记录不存在'})
    except Exception as e:
        print(f"删除识别记录时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/albums', methods=['GET'])
@auth_required
def get_albums():
    """获取用户相册列表"""
    try:
        category = request.args.get('category')
        
        albums = get_user_albums(g.user_id, category)
        
        return jsonify({
            'success': True,
            'albums': albums
        })
    except Exception as e:
        print(f"获取相册列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/albums', methods=['POST'])
@auth_required
def create_album_api():
    """创建新相册"""
    try:
        data = request.get_json()
        name = data.get('name')
        category = data.get('category')
        cover_image = data.get('cover_image')
        description = data.get('description')
        
        if not name or not category:
            return jsonify({'success': False, 'error': '相册名称和分类不能为空'}), 400
        
        album_id = create_album(g.user_id, name, category, cover_image, description)
        
        return jsonify({
            'success': True,
            'album_id': album_id,
            'message': '相册创建成功'
        })
    except Exception as e:
        print(f"创建相册时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/albums/<int:album_id>', methods=['GET'])
@auth_required
def get_album_detail(album_id):
    """获取相册详情"""
    try:
        album = get_album_by_id(album_id, g.user_id)
        
        if not album:
            return jsonify({'success': False, 'error': '相册不存在'}), 404
        
        images, total = get_album_images(album_id, g.user_id)
        
        return jsonify({
            'success': True,
            'album': album,
            'images': images,
            'total': total
        })
    except Exception as e:
        print(f"获取相册详情时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/albums/<int:album_id>', methods=['PUT'])
@auth_required
def update_album_api(album_id):
    """更新相册信息"""
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        
        success = update_album(album_id, g.user_id, name, description)
        
        if success:
            return jsonify({'success': True, 'message': '相册更新成功'})
        else:
            return jsonify({'success': False, 'error': '更新失败'})
    except Exception as e:
        print(f"更新相册时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/albums/<int:album_id>', methods=['DELETE'])
@auth_required
def delete_album_api(album_id):
    """删除相册"""
    try:
        success = delete_album(album_id, g.user_id)
        
        if success:
            return jsonify({'success': True, 'message': '相册删除成功'})
        else:
            return jsonify({'success': False, 'error': '删除失败'})
    except Exception as e:
        print(f"删除相册时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/albums/<int:album_id>/images', methods=['POST'])
@auth_required
def add_image_to_album_api(album_id):
    """添加图片到相册"""
    try:
        data = request.get_json()
        image_path = data.get('image_path')
        flower_name = data.get('flower_name')
        confidence = data.get('confidence')
        recognition_result_id = data.get('recognition_result_id')
        
        if not image_path:
            return jsonify({'success': False, 'error': '图片路径不能为空'}), 400
        
        album = get_album_by_id(album_id, g.user_id)
        if not album:
            return jsonify({'success': False, 'error': '相册不存在'}), 404
        
        image_id = add_image_to_album(album_id, g.user_id, image_path, flower_name, confidence, recognition_result_id)
        
        return jsonify({
            'success': True,
            'image_id': image_id,
            'message': '图片添加成功'
        })
    except Exception as e:
        print(f"添加图片到相册时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/albums/<int:album_id>/images/<int:image_id>', methods=['DELETE'])
@auth_required
def delete_album_image_api(album_id, image_id):
    """删除相册中的图片"""
    try:
        images, _ = get_album_images(album_id, g.user_id)
        image_info = None
        for img in images:
            if img['id'] == image_id:
                image_info = img
                break

        if image_info:
            # 尝试获取完整的识别信息
            recognition_result_id = image_info.get('recognition_result_id')
            recognition_info = {}

            if recognition_result_id:
                try:
                    result = get_recognition_result(recognition_result_id)
                    if result:
                        recognition_info = {
                            'result': result.get('result'),
                            'confidence': result.get('confidence'),
                            'shoot_time': result.get('shoot_time'),
                            'shoot_year': result.get('shoot_year'),
                            'shoot_month': result.get('shoot_month'),
                            'shoot_season': result.get('shoot_season'),
                            'location_text': result.get('location_text'),
                            'region_label': result.get('region_label'),
                            'camera_make': result.get('camera_make'),
                            'camera_model': result.get('camera_model'),
                            'image_width': result.get('image_width'),
                            'image_height': result.get('image_height'),
                            'final_category': result.get('final_category')
                        }
                except Exception as e:
                    print(f"获取识别结果信息失败: {e}")

            # 构建回收站 item_data
            recycle_item_data = {
                'image_path': image_info.get('image_path'),
                'flower_name': image_info.get('flower_name') or recognition_info.get('result', '未知花卉'),
                'confidence': image_info.get('confidence') or recognition_info.get('confidence', 0),
                'created_at': image_info.get('created_at'),
                'album_id': album_id,
                'album_name': image_info.get('album_name', '未分类'),
                'recognition_result_id': recognition_result_id,
                # 添加完整的识别信息
                'shoot_time': recognition_info.get('shoot_time'),
                'shoot_year': recognition_info.get('shoot_year'),
                'shoot_month': recognition_info.get('shoot_month'),
                'shoot_season': recognition_info.get('shoot_season'),
                'location_text': recognition_info.get('location_text'),
                'region_label': recognition_info.get('region_label'),
                'camera_make': recognition_info.get('camera_make'),
                'camera_model': recognition_info.get('camera_model'),
                'image_width': recognition_info.get('image_width'),
                'image_height': recognition_info.get('image_height'),
                'final_category': recognition_info.get('final_category')
            }

            move_to_recycle_bin(g.user_id, 'image', image_id, recycle_item_data)

        success = delete_album_image(image_id, album_id, g.user_id)

        if success:
            return jsonify({'success': True, 'message': '图片已移入回收站'})
        else:
            return jsonify({'success': False, 'error': '删除失败'})
    except Exception as e:
        print(f"删除图片时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/albums/<int:album_id>/images/<int:image_id>/move', methods=['POST'])
@auth_required
def move_album_image_api(album_id, image_id):
    """移动图片到另一个相册"""
    try:
        data = request.get_json()
        target_album_id = data.get('target_album_id')

        if not target_album_id:
            return jsonify({'success': False, 'error': '请选择目标相册'}), 400

        success = move_image_to_album(image_id, album_id, target_album_id, g.user_id)

        if success:
            return jsonify({'success': True, 'message': '图片移动成功'})
        else:
            return jsonify({'success': False, 'error': '移动失败'})
    except Exception as e:
        print(f"移动图片时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/albums/categories', methods=['GET'])
@auth_required
def get_album_categories_api():
    """获取相册分类列表"""
    try:
        categories = get_album_categories(g.user_id)
        
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        print(f"获取相册分类时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
@auth_required
def create_feedback_api():
    """提交用户反馈"""
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        feedback_type = data.get('feedback_type')
        
        if not title or not content or not feedback_type:
            return jsonify({'success': False, 'error': '标题、内容和类型不能为空'}), 400
        
        feedback_id = create_feedback(g.user_id, title, content, feedback_type)
        
        return jsonify({
            'success': True,
            'feedback_id': feedback_id,
            'message': '反馈提交成功'
        })
    except Exception as e:
        print(f"提交反馈时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/feedback', methods=['GET'])
@auth_required
def get_feedback_list():
    """获取用户反馈列表"""
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        results, total = get_user_feedback(g.user_id, limit, offset)
        
        return jsonify({
            'success': True,
            'feedback': results,
            'total': total
        })
    except Exception as e:
        print(f"获取反馈列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/feedback/<int:feedback_id>', methods=['GET'])
@auth_required
def get_feedback_detail(feedback_id):
    """获取反馈详情"""
    try:
        feedback = get_feedback_by_id(feedback_id, g.user_id)
        
        if not feedback:
            return jsonify({'success': False, 'error': '反馈不存在'}), 404
        
        return jsonify({
            'success': True,
            'feedback': feedback
        })
    except Exception as e:
        print(f"获取反馈详情时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/feedback/<int:feedback_id>', methods=['DELETE'])
@auth_required
def delete_feedback_api(feedback_id):
    """删除反馈"""
    try:
        success = delete_feedback(feedback_id, g.user_id)
        
        if success:
            return jsonify({'success': True, 'message': '反馈删除成功'})
        else:
            return jsonify({'success': False, 'error': '删除失败'})
    except Exception as e:
        print(f"删除反馈时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/feedback', methods=['GET'])
@auth_required
@permission_required('manage_users')
def get_all_feedback_api():
    """获取所有反馈（管理员）"""
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        results, total = get_all_feedback(status, limit, offset)
        
        return jsonify({
            'success': True,
            'feedback': results,
            'total': total
        })
    except Exception as e:
        print(f"获取所有反馈时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/feedback/<int:feedback_id>/respond', methods=['POST'])
@auth_required
@permission_required('manage_users')
def respond_feedback_api(feedback_id):
    """回复反馈（管理员）"""
    try:
        data = request.get_json()
        response = data.get('response')
        
        if not response:
            return jsonify({'success': False, 'error': '回复内容不能为空'}), 400
        
        success = respond_feedback(feedback_id, response)
        
        if success:
            ip_address = request.remote_addr
            record_admin_operation(g.user_id, g.username, 'respond_feedback', 'feedback', feedback_id, f'回复反馈: {response[:50]}...', ip_address)
            return jsonify({'success': True, 'message': '回复成功'})
        else:
            return jsonify({'success': False, 'error': '回复失败'})
    except Exception as e:
        print(f"回复反馈时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/announcements', methods=['POST'])
@admin_required
def create_announcement_api():
    """创建公告（管理员）"""
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        announcement_type = data.get('announcement_type', 'general')
        
        if not title or not content:
            return jsonify({'success': False, 'error': '标题和内容不能为空'}), 400
        
        announcement_id = create_announcement(title, content, announcement_type, g.user_id, g.username)
        
        ip_address = request.remote_addr
        record_admin_operation(g.user_id, g.username, 'create_announcement', 'announcement', announcement_id, f'创建公告: {title[:50]}', ip_address)
        
        return jsonify({'success': True, 'message': '公告创建成功', 'announcement_id': announcement_id})
    except Exception as e:
        print(f"创建公告时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/announcements', methods=['GET'])
@admin_required
def get_announcements_api():
    """获取公告列表（管理员）"""
    try:
        is_active = request.args.get('is_active')
        if is_active is not None:
            is_active = int(is_active)
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        results, total = get_announcements(is_active, limit, offset)
        
        return jsonify({
            'success': True,
            'announcements': results,
            'total': total
        })
    except Exception as e:
        print(f"获取公告列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/announcements/<int:announcement_id>', methods=['PUT'])
@admin_required
def update_announcement_api(announcement_id):
    """更新公告（管理员）"""
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        announcement_type = data.get('announcement_type', 'general')
        
        if not title or not content:
            return jsonify({'success': False, 'error': '标题和内容不能为空'}), 400
        
        success = update_announcement(announcement_id, title, content, announcement_type, g.user_id)
        
        if success:
            ip_address = request.remote_addr
            record_admin_operation(g.user_id, g.username, 'update_announcement', 'announcement', announcement_id, f'更新公告: {title[:50]}', ip_address)
            return jsonify({'success': True, 'message': '公告更新成功'})
        else:
            return jsonify({'success': False, 'error': '公告不存在或无权限'}), 404
    except Exception as e:
        print(f"更新公告时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/announcements/<int:announcement_id>', methods=['DELETE'])
@admin_required
def delete_announcement_api(announcement_id):
    """删除公告（管理员）"""
    try:
        success = delete_announcement(announcement_id, g.user_id)
        
        if success:
            ip_address = request.remote_addr
            record_admin_operation(g.user_id, g.username, 'delete_announcement', 'announcement', announcement_id, '删除公告', ip_address)
            return jsonify({'success': True, 'message': '公告删除成功'})
        else:
            return jsonify({'success': False, 'error': '公告不存在或无权限'}), 404
    except Exception as e:
        print(f"删除公告时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/announcements', methods=['GET'])
def get_public_announcements():
    """获取公开公告列表（所有用户可见）"""
    try:
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        results, total = get_announcements(is_active=1, limit=limit, offset=offset)
        
        return jsonify({
            'success': True,
            'announcements': results,
            'total': total
        })
    except Exception as e:
        print(f"获取公告列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recycle-bin', methods=['GET'])
@auth_required
def get_recycle_bin():
    """获取回收站项目列表"""
    try:
        item_type = request.args.get('item_type')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        results, total = get_recycle_bin_items(g.user_id, item_type, limit, offset)
        
        return jsonify({
            'success': True,
            'items': results,
            'total': total
        })
    except Exception as e:
        print(f"获取回收站项目时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recycle-bin/<int:recycle_id>/restore', methods=['POST'])
@auth_required
def restore_item(recycle_id):
    """从回收站恢复项目"""
    try:
        success, message = restore_from_recycle_bin(g.user_id, recycle_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 404
    except Exception as e:
        print(f"恢复项目时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recycle-bin/<int:recycle_id>', methods=['DELETE'])
@auth_required
def delete_permanently(recycle_id):
    """永久删除回收站项目"""
    try:
        success, message = permanently_delete(g.user_id, recycle_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 404
    except Exception as e:
        print(f"永久删除项目时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recycle-bin/empty', methods=['POST'])
@auth_required
def empty_recycle_bin_api():
    """清空回收站"""
    try:
        success = empty_recycle_bin(g.user_id)
        
        if success:
            return jsonify({'success': True, 'message': '回收站已清空'})
        else:
            return jsonify({'success': False, 'error': '清空失败'})
    except Exception as e:
        print(f"清空回收站时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 访问日志中间件
@app.before_request
def before_request():
    """请求前记录访问日志"""
    g.start_time = time.time()

@app.after_request
def after_request(response):
    """请求后记录访问日志"""
    try:
        response_time = int((time.time() - g.start_time) * 1000)
        endpoint = request.endpoint
        method = request.method
        ip_address = request.remote_addr
        user_id = g.user_id if hasattr(g, 'user_id') else None
        
        # 记录访问流量
        record_traffic(endpoint, method, ip_address, user_id, response.status_code, response_time)
        
        # 记录系统日志（如果是错误响应）
        if response.status_code >= 400:
            create_system_log('ERROR', 'API', f'{method} {endpoint} 返回 {response.status_code}', 
                           user_id, g.username if hasattr(g, 'username') else None, ip_address, request.user_agent.string)
    except Exception as e:
        print(f"记录访问日志时发生错误: {str(e)}")
    
    return response

if __name__ == '__main__':
    print('启动应用...')
    try:
        # 启动Flask服务器
        print('启动Flask服务器，监听在0.0.0.0:5000')
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f'应用启动失败: {str(e)}')
        import traceback
        traceback.print_exc()
