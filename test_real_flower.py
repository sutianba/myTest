#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
测试真实花朵图片的识别功能
"""

import base64
import requests
import io
from PIL import Image

# 设置测试图片路径
IMAGE_PATH = "./Example_IMG/_IMG_4.jpg"

# 设置API端点
API_ENDPOINT = "http://localhost:5000/api/detect"

def image_to_base64(image_path):
    """将图片转换为base64格式"""
    with Image.open(image_path) as img:
        # 转换为RGB格式以确保兼容性
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 保存为JPEG格式的BytesIO对象
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        
        # 转换为base64字符串
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # 添加base64头部
        return f"data:image/jpeg;base64,{img_str}"

def test_flower_recognition():
    """测试花卉识别API"""
    try:
        # 将图片转换为base64格式
        print(f"正在读取图片: {IMAGE_PATH}")
        base64_image = image_to_base64(IMAGE_PATH)
        print(f"图片转换成功，base64长度: {len(base64_image)}")
        
        # 准备请求数据
        data = {
            "image": base64_image
        }
        
        # 发送POST请求
        print(f"正在向API发送请求: {API_ENDPOINT}")
        response = requests.post(API_ENDPOINT, json=data)
        
        # 检查响应状态码
        if response.status_code == 200:
            # 解析响应数据
            result = response.json()
            print("API调用成功!")
            print(f"响应结果: {result}")
            
            if result["success"]:
                results = result["results"]
                detections = results["detections"]
                
                if detections:
                    for i, detection in enumerate(detections):
                        print(f"检测结果 {i+1}:")
                        print(f"  花卉名称: {detection['name']}")
                        print(f"  置信度: {detection['confidence']:.2f}")
                        print(f"  边界框: {detection['bbox']}")
                else:
                    print("未检测到花卉")
            else:
                print(f"识别失败: {result['error']}")
        else:
            print(f"API调用失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_flower_recognition()
