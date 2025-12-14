#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
调试完整的坐标处理流程
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入需要的函数
from app import get_address_from_coordinates, match_location_by_coordinates, convert_to_decimal

print("=== 调试完整坐标处理流程 ===")
print(f"Python版本: {sys.version}")

# 模拟用户提供的坐标
user_lat = 22.654097
user_lon = 113.816981
print(f"\n用户坐标: lat={user_lat}, lon={user_lon}")

# 1. 测试match_location_by_coordinates函数
print("\n1. 测试match_location_by_coordinates函数:")
location_match = match_location_by_coordinates(user_lat, user_lon)
print(f"   结果: {location_match}")

# 2. 测试get_address_from_coordinates函数
print("\n2. 测试get_address_from_coordinates函数:")
address = get_address_from_coordinates(user_lat, user_lon)
print(f"   返回值类型: {type(address)}")
print(f"   返回值: {address}")

# 3. 模拟实际应用中的流程
print("\n3. 模拟实际应用中的处理流程:")
address = get_address_from_coordinates(user_lat, user_lon)
if address:
    print(f"   Nominatim返回了地址信息: {address}")
    # 这里可以添加format_address的测试
else:
    print(f"   Nominatim服务失败，使用本地匹配")
    location_match = match_location_by_coordinates(user_lat, user_lon)
    print(f"   本地匹配结果: {location_match}")

# 4. 测试convert_to_decimal函数（模拟EXIF数据）
print("\n4. 测试convert_to_decimal函数:")
# 模拟EXIF格式的经纬度数据
exif_lat = [(22, 1), (39, 1), (14, 1)]  # 22°39'14"N
exif_lon = [(113, 1), (49, 1), (11, 1)]  # 113°49'11"E

# 将元组转换为模拟exifread的对象
class MockEXIFTag:
    def __init__(self, values):
        self.values = values

# 模拟exifread返回的对象
lat_obj = MockEXIFTag(exif_lat)
lon_obj = MockEXIFTag(exif_lon)

# 测试转换
converted_lat = convert_to_decimal(lat_obj, 'N')
converted_lon = convert_to_decimal(lon_obj, 'E')

print(f"   原始EXIF纬度: {exif_lat} -> 转换后: {converted_lat} (类型: {type(converted_lat)})")
print(f"   原始EXIF经度: {exif_lon} -> 转换后: {converted_lon} (类型: {type(converted_lon)})")

# 测试转换后的坐标是否能匹配
print(f"\n5. 测试转换后的坐标是否能匹配:")
location_match = match_location_by_coordinates(converted_lat, converted_lon)
print(f"   匹配结果: {location_match}")
