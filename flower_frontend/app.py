#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import sys
import base64
import io
import random
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# 导入图片日期提取所需模块
from PIL import Image
from PIL.ExifTags import TAGS

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
    
    # 提取图片日期信息
    image_date = "未知"
    try:
        # 创建临时文件保存图片
        temp_file_path = "temp_image.jpg"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(image_bytes)
        
        # 使用Pillow提取EXIF信息
        with Image.open(temp_file_path) as img:
            exif_data = img._getexif()
            if exif_data:
                # 获取所有EXIF标签
                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name == 'DateTimeOriginal' or tag_name == 'DateTime':
                        image_date = str(value)
                        break
        
        # 删除临时文件
        os.remove(temp_file_path)
    except Exception as e:
        print(f"提取图片日期失败: {e}")
        image_date = "未知"

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
    
    # 返回包含识别结果和日期信息的响应
    return {
        'detections': detection_results,
        'date': image_date
    }

if __name__ == '__main__':
    # 启动Flask服务器
    app.run(host='0.0.0.0', port=5000, debug=True)
