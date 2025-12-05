#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import sys
import base64
import io
import torch
from PIL import Image
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 启用CORS以允许前端访问

# 加载YOLOv5花卉识别模型
# 确保testflowers.pt文件存在于正确的目录中
flower_model = torch.hub.load('../..', 'custom', path='testflowers.pt', source='local', force_reload=True)
flower_model.conf = 0.25  # 设置置信度阈值
flower_model.iou = 0.45   # 设置NMS IOU阈值

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
