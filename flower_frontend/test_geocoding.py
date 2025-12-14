#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
测试脚本：检查经纬度转地址功能是否正常工作
使用与app.py相同的配置来测试Nominatim服务
"""

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import traceback

def test_get_address_from_coordinates(lat, lon, max_retries=2):
    """测试通过经纬度获取地址信息"""
    print(f"\n测试坐标：{lat}, {lon}")
    print("=" * 50)
    
    try:
        # 使用与app.py相同的配置
        geolocator = Nominatim(user_agent="flower_recognition_app", timeout=5)
        print(f"✓ 成功初始化Nominatim地理编码器")
        
        # 重试机制
        for attempt in range(max_retries):
            print(f"\n第 {attempt + 1}/{max_retries} 次尝试...")
            try:
                location = geolocator.reverse((lat, lon), language='zh-CN')
                if location:
                    print(f"✓ 成功获取地址信息")
                    print(f"  原始响应: {location.raw}")
                    print(f"  地址部分: {location.raw.get('address', {})}")
                    return True, location.raw.get('address', {})
                else:
                    print(f"✗ 未获取到地址信息")
            except GeocoderTimedOut:
                print(f"✗ 请求超时")
                if attempt < max_retries - 1:
                    time.sleep(0.5)
            except GeocoderServiceError as e:
                print(f"✗ 服务错误: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)
            except Exception as e:
                print(f"✗ 获取地址时发生其他错误: {e}")
                traceback.print_exc()
                break
    except Exception as e:
        print(f"✗ 初始化地理编码器时出错: {e}")
        traceback.print_exc()
    
    print(f"\n✗ 多次尝试后仍无法获取地址信息")
    return False, None

# 测试单个已知的坐标点
def main():
    print("开始测试Nominatim地理编码服务...")
    print()
    
    # 只测试一个坐标点（北京天安门）
    lat, lon = 39.9075, 116.3972
    print(f"测试坐标：{lat}, {lon} (北京天安门)")
    print()
    
    success, address = test_get_address_from_coordinates(lat, lon)
    
    print()
    print("=" * 50)
    if success:
        print("✅ 测试成功！Nominatim服务正常工作")
        print("地址信息:")
        for key, value in address.items():
            print(f"  {key}: {value}")
    else:
        print("❌ 测试失败！Nominatim服务可能不可用")
        print("可能的原因：")
        print("1. Nominatim服务暂时不可用")
        print("2. 网络连接问题")
        print("3. IP被Nominatim服务限制")
        print("4. 配置参数错误")

if __name__ == "__main__":
    main()