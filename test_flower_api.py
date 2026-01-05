#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
使用真实花卉图片测试识别API
"""
import requests
import json
import base64
import os
from PIL import Image
import io

def create_flower_image():
    """创建一个简单的花卉图案图片"""
    # 创建一个200x200的白色背景图片
    image = Image.new('RGB', (200, 200), color='white')
    
    # 在图片上绘制一个简单的红色花朵形状
    pixels = image.load()
    
    # 绘制花朵中心
    for x in range(80, 120):
        for y in range(80, 120):
            distance = ((x-100)**2 + (y-100)**2)**0.5
            if distance < 20:
                pixels[x, y] = (255, 215, 0)  # 金黄色中心
    
    # 绘制花瓣
    petal_positions = [
        (100, 50),   # 上
        (150, 100),  # 右
        (100, 150),  # 下
        (50, 100)    # 左
    ]
    
    for (cx, cy) in petal_positions:
        for x in range(cx-30, cx+30):
            for y in range(cy-30, cy+30):
                distance = ((x-cx)**2 + (y-cy)**2)**0.5
                if distance < 30:
                    pixels[x, y] = (255, 0, 0)  # 红色花瓣
    
    # 保存到内存
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return img_byte_arr

def test_api():
    """测试API接口"""
    try:
        # 创建测试图片
        image_bytes = create_flower_image()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # 构建请求数据
        payload = {
            "image": f"data:image/jpeg;base64,{base64_image}"
        }
        
        print("正在发送测试请求...")
        # 发送POST请求
        response = requests.post("http://localhost:5000/api/detect", json=payload, timeout=30)
        
        print(f"HTTP状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        # 解析响应
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("success"):
                    print("\n识别成功!")
                    results = data.get("results")
                    if results:
                        detections = results.get("detections")
                        if detections:
                            print("检测到以下花卉:")
                            for det in detections:
                                print(f"- {det['name']}: 置信度 {det['confidence']:.2f}")
                        else:
                            print("未检测到任何花卉")
                        
                        exif_info = results.get("exif_info")
                        if exif_info:
                            print(f"\n图片信息:")
                            print(f"- 尺寸: {exif_info['image_details']['width']}x{exif_info['image_details']['height']}")
                else:
                    print(f"识别失败: {data.get('error')}")
            except json.JSONDecodeError:
                print("响应内容不是有效的JSON格式")
        else:
            print(f"请求失败，HTTP状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()
