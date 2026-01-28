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

# 导入数据库操作模块
from db import (
    create_user, get_user_by_username, get_user_by_id, verify_password,
    create_post, get_posts, get_post_by_id, update_post, delete_post,
    create_comment, get_comments_by_post_id, delete_comment,
    like_post, unlike_post, is_post_liked_by_user,
    follow_user, unfollow_user, is_following, get_user_following, get_user_followers,
    check_user_permission
)

app = Flask(__name__)
CORS(app)  # 启用CORS以允许前端访问

# 定义静态文件目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# JWT配置
app.config['SECRET_KEY'] = 'flower_recognition_secret_key'
app.config['JWT_EXPIRATION_DELTA'] = 3600  # JWT过期时间（秒）

# JWT相关导入
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

# 加载YOLOv5模型
import torch

# 使用正确路径加载模型
flower_model = None
try:
    flower_model = torch.hub.load('..', 'custom', path='../testflowers.pt', source='local', force_reload=True)
    flower_model.conf = 0.5  # 提高置信度阈值，只保留高置信度结果
    flower_model.iou = 0.5   # 提高NMS IOU阈值，更严格地过滤重叠边界框
    print("成功加载YOLOv5花卉识别模型")
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

# JWT工具函数
def generate_jwt(user_id, username):
    """生成JWT令牌"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': time.time() + app.config['JWT_EXPIRATION_DELTA']
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def verify_jwt(token):
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# 认证中间件
def auth_required(f):
    """认证装饰器"""
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
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
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# 权限验证中间件
def permission_required(permission):
    """权限验证装饰器"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'user_id'):
                return jsonify({'success': False, 'error': '需要认证'}), 401
            
            if not check_user_permission(g.user_id, permission):
                return jsonify({'success': False, 'error': '权限不足'}), 403
            
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

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
            # 多图片请求
            images_data = data['images']
            all_results = []
            
            for i, image_data in enumerate(images_data):
                results = process_single_image(image_data)
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


def process_single_image(image_data):
    """处理单个图片的识别"""
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
    
    try:
        # 创建临时文件保存图片
        temp_file_path = "temp_image.jpg"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(image_bytes)
        
        # 使用exifread提取EXIF信息
        with open(temp_file_path, 'rb') as f:
            exif_tags = exifread.process_file(f)
            
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
            except Exception as e:
                print(f"处理GPS信息时出错: {e}")
        
        # 删除临时文件
        os.remove(temp_file_path)
    except Exception as e:
        print(f"提取图片EXIF信息失败: {e}")

    # 使用YOLOv5模型进行花卉识别
    model_results = flower_model(image)
    
    # 解析识别结果
    results = []
    for result in model_results.pandas().xyxy[0].to_dict(orient='records'):
        results.append({
            'name': result['name'],
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
    if results:
        # 按置信度降序排序
        results.sort(key=lambda x: x['confidence'], reverse=True)
        # 只添加置信度最高的结果
        detection_results.append({
            'name': results[0]['name'],
            'confidence': float(results[0]['confidence']),
            'bbox': results[0]['bbox']
        })
    else:
        # 如果没有识别到任何结果，返回空列表
        detection_results = []
    
    # 返回包含识别结果和EXIF信息的响应
    return {
        'detections': detection_results,
        'exif_info': image_info
    }

# 认证相关API
@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        if not username or not password or not email:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        # 检查用户名是否已存在
        if get_user_by_username(username):
            return jsonify({'success': False, 'error': '用户名已存在'}), 400
        
        # 创建用户
        user_id = create_user(username, password, email)
        
        # 生成JWT令牌
        token = generate_jwt(user_id, username)
        
        return jsonify({'success': True, 'user_id': user_id, 'username': username, 'token': token})
    except Exception as e:
        print(f"注册过程中发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
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
        if not verify_password(user['id'], password):
            return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
        
        # 生成JWT令牌
        token = generate_jwt(user['id'], user['username'])
        
        return jsonify({'success': True, 'user_id': user['id'], 'username': user['username'], 'token': token})
    except Exception as e:
        print(f"登录过程中发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 帖子相关API
@app.route('/api/posts', methods=['GET'])
def get_posts_api():
    """获取帖子列表"""
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
    try:
        data = request.get_json()
        content = data.get('content')
        image_url = data.get('image_url')
        
        if not content:
            return jsonify({'success': False, 'error': '帖子内容不能为空'}), 400
        
        post_id = create_post(g.user_id, content, image_url)
        
        return jsonify({'success': True, 'post_id': post_id})
    except Exception as e:
        print(f"创建帖子时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
@auth_required
def update_post_api(post_id):
    """更新帖子"""
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
    try:
        # 获取帖子信息
        post = get_post_by_id(post_id)
        if not post:
            return jsonify({'success': False, 'error': '帖子不存在'}), 404
        
        # 检查权限（只有帖子作者可以删除）
        if post['user_id'] != g.user_id:
            return jsonify({'success': False, 'error': '无权限删除此帖子'}), 403
        
        delete_post(post_id)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"删除帖子时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 评论相关API
@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_comments_api(post_id):
    """获取帖子评论"""
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
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({'success': False, 'error': '评论内容不能为空'}), 400
        
        # 检查帖子是否存在
        post = get_post_by_id(post_id)
        if not post:
            return jsonify({'success': False, 'error': '帖子不存在'}), 404
        
        comment_id = create_comment(post_id, g.user_id, content)
        
        return jsonify({'success': True, 'comment_id': comment_id})
    except Exception as e:
        print(f"创建评论时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@auth_required
def delete_comment_api(comment_id):
    """删除评论"""
    try:
        # 这里简化处理，实际应该检查评论是否存在以及用户是否有权限删除
        delete_comment(comment_id)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"删除评论时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 点赞相关API
@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@auth_required
def like_post_api(post_id):
    """点赞帖子"""
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
    try:
        is_following_status = is_following(g.user_id, user_id)
        
        return jsonify({'success': True, 'is_following': is_following_status})
    except Exception as e:
        print(f"检查关注状态时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/following', methods=['GET'])
def get_user_following_api(user_id):
    """获取用户关注的人"""
    try:
        following = get_user_following(user_id)
        
        return jsonify({'success': True, 'following': following})
    except Exception as e:
        print(f"获取关注列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/followers', methods=['GET'])
def get_user_followers_api(user_id):
    """获取用户的粉丝"""
    try:
        followers = get_user_followers(user_id)
        
        return jsonify({'success': True, 'followers': followers})
    except Exception as e:
        print(f"获取粉丝列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # 启动Flask服务器
    app.run(host='0.0.0.0', port=5000, debug=True)
