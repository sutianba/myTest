#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
调试经纬度匹配问题
"""

# 直接定义城市数据库用于调试
import sys
print(f"Python版本: {sys.version}")

guangxi_guangdong_cities = {
    "guangxi": {
        "province_name": "广西壮族自治区",
        "cities": {
            "南宁市": {"lat_min": 22.7, "lat_max": 23.3, "lon_min": 108.1, "lon_max": 108.5}
        }
    },
    "guangdong": {
        "province_name": "广东省",
        "cities": {
            "深圳市": {"lat_min": 22.3, "lat_max": 22.8, "lon_min": 113.7, "lon_max": 114.6}
        }
    }
}

def match_location_by_coordinates(lat, lon):
    print(f"\n调用匹配函数: lat={lat} (类型: {type(lat)}), lon={lon} (类型: {type(lon)})")
    
    # 检查是否在广东范围内
    print("检查广东省城市:")
    for city_name, coords in guangxi_guangdong_cities["guangdong"]["cities"].items():
        print(f"  城市: {city_name}")
        print(f"  范围: lat[{coords['lat_min']}, {coords['lat_max']}], lon[{coords['lon_min']}, {coords['lon_max']}]")
        print(f"  纬度检查: {coords['lat_min']} <= {lat} <= {coords['lat_max']} => {coords['lat_min'] <= lat <= coords['lat_max']}")
        print(f"  经度检查: {coords['lon_min']} <= {lon} <= {coords['lon_max']} => {coords['lon_min'] <= lon <= coords['lon_max']}")
        
        if coords["lat_min"] <= lat <= coords["lat_max"] and coords["lon_min"] <= lon <= coords["lon_max"]:
            result = {
                "province": guangxi_guangdong_cities["guangdong"]["province_name"],
                "city": city_name,
                "district": "未知区"
            }
            print(f"  匹配成功: {result}")
            return result
    
    # 检查是否在广西范围内
    print("检查广西壮族自治区城市:")
    for city_name, coords in guangxi_guangdong_cities["guangxi"]["cities"].items():
        print(f"  城市: {city_name}")
        print(f"  范围: lat[{coords['lat_min']}, {coords['lat_max']}], lon[{coords['lon_min']}, {coords['lon_max']}]")
        print(f"  纬度检查: {coords['lat_min']} <= {lat} <= {coords['lat_max']} => {coords['lat_min'] <= lat <= coords['lat_max']}")
        print(f"  经度检查: {coords['lon_min']} <= {lon} <= {coords['lon_max']} => {coords['lon_min'] <= lon <= coords['lon_max']}")
        
        if coords["lat_min"] <= lat <= coords["lat_max"] and coords["lon_min"] <= lon <= coords["lon_max"]:
            result = {
                "province": guangxi_guangdong_cities["guangxi"]["province_name"],
                "city": city_name,
                "district": "未知区"
            }
            print(f"  匹配成功: {result}")
            return result
    
    # 默认返回未知
    result = {
        "province": "未知省份",
        "city": "未知城市",
        "district": "未知区"
    }
    print(f"  匹配失败: {result}")
    return result

# 测试用户提供的坐标
print("=== 测试用户提供的坐标 22.654097, 113.816981 ===")
# 先尝试浮点数
print("\n1. 使用浮点数:")
result = match_location_by_coordinates(22.654097, 113.816981)
print(f"最终结果: {result}")

# 再尝试字符串
print("\n2. 使用字符串:")
try:
    result = match_location_by_coordinates("22.654097", "113.816981")
    print(f"最终结果: {result}")
except Exception as e:
    print(f"错误: {e}")
