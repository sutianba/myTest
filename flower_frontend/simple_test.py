#!/usr/bin/env python3
# 简单测试Nominatim服务

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

def simple_test():
    print("开始简单测试...")
    try:
        geolocator = Nominatim(user_agent="flower_recognition_app", timeout=10)
        print("✓ 初始化地理编码器成功")
        
        lat, lon = 39.9075, 116.3972
        print(f"\n测试坐标：{lat}, {lon}")
        
        try:
            location = geolocator.reverse((lat, lon), language='zh-CN')
            if location:
                print("✓ 获取地址成功")
                print(f"  地址: {location.address}")
            else:
                print("✗ 未获取到地址信息")
        except GeocoderTimedOut:
            print("✗ 请求超时")
        except GeocoderServiceError as e:
            print(f"✗ 服务错误: {e}")
        except Exception as e:
            print(f"✗ 其他错误: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"✗ 初始化错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n测试结束")

if __name__ == "__main__":
    simple_test()