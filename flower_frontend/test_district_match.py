#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
测试经纬度匹配函数是否能正确识别到区一级信息
"""

import sys
import os

# 添加当前目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import match_location_by_coordinates

def test_district_matching():
    """测试区一级匹配"""
    print("开始测试经纬度区一级匹配功能...")
    
    # 测试用例：深圳宝安区坐标
    print("\n测试1: 深圳宝安区")
    lat, lon = 22.568472, 113.828484  # 宝安区中心坐标
    result = match_location_by_coordinates(lat, lon)
    print(f"坐标: {lat}, {lon}")
    print(f"结果: {result}")
    assert result["province"] == "广东省", f"期望省份: 广东省, 实际: {result['province']}"
    assert result["city"] == "深圳市", f"期望城市: 深圳市, 实际: {result['city']}"
    assert result["district"] == "宝安区", f"期望区: 宝安区, 实际: {result['district']}"
    print("✓ 测试通过")
    
    # 测试用例：深圳龙华区坐标
    print("\n测试2: 深圳龙华区")
    lat, lon = 22.638369, 114.021339  # 龙华区中心坐标
    result = match_location_by_coordinates(lat, lon)
    print(f"坐标: {lat}, {lon}")
    print(f"结果: {result}")
    assert result["province"] == "广东省", f"期望省份: 广东省, 实际: {result['province']}"
    assert result["city"] == "深圳市", f"期望城市: 深圳市, 实际: {result['city']}"
    assert result["district"] == "龙华区", f"期望区: 龙华区, 实际: {result['district']}"
    print("✓ 测试通过")
    
    # 测试用例：广州天河区坐标
    print("\n测试3: 广州天河区")
    lat, lon = 23.135122, 113.351598  # 天河区中心坐标
    result = match_location_by_coordinates(lat, lon)
    print(f"坐标: {lat}, {lon}")
    print(f"结果: {result}")
    assert result["province"] == "广东省", f"期望省份: 广东省, 实际: {result['province']}"
    assert result["city"] == "广州市", f"期望城市: 广州市, 实际: {result['city']}"
    assert result["district"] == "天河区", f"期望区: 天河区, 实际: {result['district']}"
    print("✓ 测试通过")
    
    # 测试用例：用户之前提供的坐标
    print("\n测试4: 用户之前提供的坐标")
    lat, lon = 22.654097, 113.816981  # 用户提供的坐标
    result = match_location_by_coordinates(lat, lon)
    print(f"坐标: {lat}, {lon}")
    print(f"结果: {result}")
    assert result["province"] == "广东省", f"期望省份: 广东省, 实际: {result['province']}"
    assert result["city"] == "深圳市", f"期望城市: 深圳市, 实际: {result['city']}"
    # 这个坐标应该在宝安区或龙华区附近
    assert result["district"] in ["宝安区", "龙华区"], f"期望区: 宝安区或龙华区, 实际: {result['district']}"
    print("✓ 测试通过")
    
    print("\n🎉 所有测试通过！经纬度区一级匹配功能正常工作。")

if __name__ == "__main__":
    test_district_matching()
