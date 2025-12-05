#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import sys
import base64
import io
import random
from PIL import Image
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 启用CORS以允许前端访问

# 模拟花卉类型列表
flower_types = ['玫瑰', '郁金香', '向日葵', '百合', '康乃馨', '牡丹', '菊花', '兰花']

@app.route('/')
def index():
    """返回前端HTML页面"""
    return send_from_directory('.', 'index.html')

@app.route('/api/detect', methods=['POST'])
def detect():
    """花卉识别API接口"""
    try:
        # 获取请求中的图片数据
        data = request.get_json()
        if 'image' not in data:
            return jsonify({'error': '请求中缺少图片数据'}), 400
        
        # 解码base64图片
        image_data = data['image'].split(',')[1]  # 去除data:image/xxx;base64,前缀
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # 模拟花卉识别（生成随机结果）
        results = []
        # 生成1-3个随机花卉检测结果
        for _ in range(random.randint(1, 3)):
            # 随机生成边界框
            img_width, img_height = image.size
            bbox = [
                random.randint(0, img_width // 2),  # xmin
                random.randint(0, img_height // 2),  # ymin
                random.randint(img_width // 2, img_width),  # xmax
                random.randint(img_height // 2, img_height)  # ymax
            ]
            results.append({
                'name': random.choice(flower_types),
                'confidence': round(random.uniform(0.8, 0.99), 4),
                'bbox': bbox
            })
        
        # 处理识别结果
        detection_results = []
        for result in results:
            detection_results.append({
                'name': result['name'],
                'confidence': float(result['confidence']),
                'bbox': result['bbox']
            })
        
        return jsonify({
            'success': True,
            'results': detection_results
        })
        
    except Exception as e:
        print(f"识别过程中发生错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':

    
    # 启动Flask服务器
    app.run(host='0.0.0.0', port=5000, debug=True)
