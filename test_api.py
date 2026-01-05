#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
测试花卉识别API接口
"""
import requests
import json

# API地址
api_url = "http://localhost:5000/api/detect"

# 创建一个简单的测试图片（1x1像素的红色图片）
def create_test_image_base64():
    """创建一个简单的测试图片并转换为base64"""
    # 1x1像素的红色图片的base64编码
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

def test_api():
    """测试API接口"""
    try:
        # 构建请求数据
        payload = {
            "image": create_test_image_base64()
        }
        
        print("正在发送测试请求...")
        # 发送POST请求
        response = requests.post(api_url, json=payload, timeout=30)
        
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
                            for det in detections:
                                print(f"识别结果: {det['name']}, 置信度: {det['confidence']:.2f}")
                        exif_info = results.get("exif_info")
                        if exif_info:
                            print(f"图片尺寸: {exif_info['image_details']['width']}x{exif_info['image_details']['height']}")
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
