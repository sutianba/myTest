#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# 你可以在 http://127.0.0.1:5000 网站进行查看
import os
import sys
import base64
import io
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# 导入图片EXIF信息提取所需模块
from PIL import Image
from PIL.ExifTags import TAGS
import exifread
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

app = Flask(__name__)
CORS(app)  # 启用CORS以允许前端访问

# 定义静态文件目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 加载YOLOv5模型
import torch

# 使用正确路径加载模型
try:
    flower_model = torch.hub.load('..', 'custom', path='../testflowers.pt', source='local', force_reload=True)
    flower_model.conf = 0.5  # 提高置信度阈值，只保留高置信度结果
    flower_model.iou = 0.5   # 提高NMS IOU阈值，更严格地过滤重叠边界框
    print("成功加载YOLOv5花卉识别模型")
except Exception as e:
    print(f"无法加载YOLOv5模型: {e}")
    raise RuntimeError("无法加载YOLOv5模型，请检查模型文件是否存在") from e

@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory(BASE_DIR, 'index.html')

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
        return jsonify({'error': str(e)}), 500


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

if __name__ == '__main__':
    # 启动Flask服务器
    app.run(host='0.0.0.0', port=5000, debug=True)
