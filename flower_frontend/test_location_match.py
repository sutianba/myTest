#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
测试经纬度匹配功能
"""

# 导入需要的函数和数据
from app import match_location_by_coordinates, guangxi_guangdong_cities

# 测试用例
print("=== 测试广西和广东地区经纬度匹配功能 ===")

# 测试用户提供的坐标：22.654097, 113.816981
print("\n1. 测试用户提供的坐标：22.654097, 113.816981")
result = match_location_by_coordinates(22.654097, 113.816981)
print(f"   匹配结果: {result}")

# 测试其他几个坐标点
print("\n2. 测试广州坐标：23.1291, 113.2644")
result = match_location_by_coordinates(23.1291, 113.2644)
print(f"   匹配结果: {result}")

print("\n3. 测试深圳坐标：22.5431, 114.0579")
result = match_location_by_coordinates(22.5431, 114.0579)
print(f"   匹配结果: {result}")

print("\n4. 测试南宁坐标：22.8170, 108.3661")
result = match_location_by_coordinates(22.8170, 108.3661)
print(f"   匹配结果: {result}")

print("\n5. 测试桂林坐标：25.2744, 110.2920")
result = match_location_by_coordinates(25.2744, 110.2920)
print(f"   匹配结果: {result}")

print("\n6. 测试非广西广东坐标（北京）：39.9042, 116.4074")
result = match_location_by_coordinates(39.9042, 116.4074)
print(f"   匹配结果: {result}")

# 输出数据库中的城市数量
print("\n=== 数据库统计 ===")
guangxi_count = len(guangxi_guangdong_cities["guangxi"]["cities"])
guangdong_count = len(guangxi_guangdong_cities["guangdong"]["cities"])
print(f"广西城市数量: {guangxi_count}")
print(f"广东城市数量: {guangdong_count}")
print(f"总城市数量: {guangxi_count + guangdong_count}")

print("\n=== 测试完成 ===")
