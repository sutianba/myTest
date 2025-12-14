#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
独立测试经纬度匹配函数（不需要加载整个应用）
"""

# 复制必要的数据库和函数
guangxi_guangdong_cities = {
    "guangxi": {
        "province_name": "广西壮族自治区",
        "cities": {
            "南宁市": {"lat_min": 22.7, "lat_max": 23.3, "lon_min": 108.1, "lon_max": 108.5, "districts": {}},
            "柳州市": {"lat_min": 23.6, "lat_max": 24.4, "lon_min": 108.9, "lon_max": 109.7, "districts": {}},
            "桂林市": {"lat_min": 24.7, "lat_max": 25.5, "lon_min": 110.1, "lon_max": 110.7, "districts": {}},
            "梧州市": {"lat_min": 22.8, "lat_max": 23.6, "lon_min": 111.1, "lon_max": 111.7, "districts": {}},
            "北海市": {"lat_min": 20.8, "lat_max": 21.6, "lon_min": 108.8, "lon_max": 109.6, "districts": {}},
            "防城港市": {"lat_min": 21.3, "lat_max": 22.1, "lon_min": 107.5, "lon_max": 108.5, "districts": {}},
            "钦州市": {"lat_min": 21.7, "lat_max": 22.7, "lon_min": 108.4, "lon_max": 109.2, "districts": {}},
            "贵港市": {"lat_min": 22.8, "lat_max": 23.8, "lon_min": 109.2, "lon_max": 109.8, "districts": {}},
            "玉林市": {"lat_min": 22.1, "lat_max": 23.1, "lon_min": 109.8, "lon_max": 110.6, "districts": {}},
            "百色市": {"lat_min": 23.5, "lat_max": 24.5, "lon_min": 106.2, "lon_max": 107.0, "districts": {}},
            "贺州市": {"lat_min": 23.7, "lat_max": 24.5, "lon_min": 111.1, "lon_max": 112.0, "districts": {}},
            "河池市": {"lat_min": 23.9, "lat_max": 25.1, "lon_min": 107.6, "lon_max": 108.6, "districts": {}},
            "来宾市": {"lat_min": 23.3, "lat_max": 24.1, "lon_min": 108.6, "lon_max": 109.4, "districts": {}},
            "崇左市": {"lat_min": 22.1, "lat_max": 23.1, "lon_min": 107.1, "lon_max": 108.2, "districts": {}}
        }
    },
    "guangdong": {
        "province_name": "广东省",
        "cities": {
            "广州市": {
                "lat_min": 22.7, "lat_max": 23.3, "lon_min": 113.1, "lon_max": 113.6,
                "districts": {
                    "越秀区": {"lat_min": 23.12, "lat_max": 23.16, "lon_min": 113.24, "lon_max": 113.30},
                    "天河区": {"lat_min": 23.11, "lat_max": 23.24, "lon_min": 113.32, "lon_max": 113.40},
                    "海珠区": {"lat_min": 23.05, "lat_max": 23.15, "lon_min": 113.22, "lon_max": 113.32},
                    "荔湾区": {"lat_min": 23.06, "lat_max": 23.15, "lon_min": 113.16, "lon_max": 113.26},
                    "白云区": {"lat_min": 23.10, "lat_max": 23.30, "lon_min": 113.10, "lon_max": 113.30},
                    "黄埔区": {"lat_min": 23.05, "lat_max": 23.25, "lon_min": 113.35, "lon_max": 113.55},
                    "番禺区": {"lat_min": 22.80, "lat_max": 23.00, "lon_min": 113.20, "lon_max": 113.50},
                    "花都区": {"lat_min": 23.20, "lat_max": 23.40, "lon_min": 112.90, "lon_max": 113.20},
                    "南沙区": {"lat_min": 22.60, "lat_max": 22.80, "lon_min": 113.30, "lon_max": 113.60},
                    "从化区": {"lat_min": 23.40, "lat_max": 23.70, "lon_min": 113.30, "lon_max": 114.00},
                    "增城区": {"lat_min": 23.10, "lat_max": 23.50, "lon_min": 113.50, "lon_max": 114.00}
                }
            },
            "深圳市": {
                "lat_min": 22.3, "lat_max": 22.8, "lon_min": 113.7, "lon_max": 114.6,
                "districts": {
                    "罗湖区": {"lat_min": 22.53, "lat_max": 22.57, "lon_min": 114.04, "lon_max": 114.12},
                    "福田区": {"lat_min": 22.51, "lat_max": 22.57, "lon_min": 113.93, "lon_max": 114.04},
                    "南山区": {"lat_min": 22.42, "lat_max": 22.55, "lon_min": 113.87, "lon_max": 114.00},
                    "宝安区": {"lat_min": 22.44, "lat_max": 22.70, "lon_min": 113.72, "lon_max": 114.00},
                    "龙岗区": {"lat_min": 22.53, "lat_max": 22.80, "lon_min": 114.08, "lon_max": 114.30},
                    "盐田区": {"lat_min": 22.57, "lat_max": 22.68, "lon_min": 114.22, "lon_max": 114.32},
                    "龙华区": {"lat_min": 22.54, "lat_max": 22.70, "lon_min": 113.90, "lon_max": 114.08},
                    "坪山区": {"lat_min": 22.65, "lat_max": 22.80, "lon_min": 114.15, "lon_max": 114.40},
                    "光明区": {"lat_min": 22.70, "lat_max": 22.80, "lon_min": 113.90, "lon_max": 114.05},
                    "大鹏新区": {"lat_min": 22.40, "lat_max": 22.60, "lon_min": 114.20, "lon_max": 114.60}
                }
            },
            "珠海市": {"lat_min": 21.8, "lat_max": 22.4, "lon_min": 113.2, "lon_max": 113.7, "districts": {}},
            "汕头市": {"lat_min": 23.1, "lat_max": 23.5, "lon_min": 116.4, "lon_max": 117.2, "districts": {}},
            "佛山市": {"lat_min": 22.9, "lat_max": 23.3, "lon_min": 112.9, "lon_max": 113.3, "districts": {}},
            "韶关市": {"lat_min": 24.5, "lat_max": 25.4, "lon_min": 113.4, "lon_max": 114.3, "districts": {}},
            "湛江市": {"lat_min": 20.8, "lat_max": 21.5, "lon_min": 110.2, "lon_max": 110.9, "districts": {}},
            "肇庆市": {"lat_min": 23.1, "lat_max": 23.8, "lon_min": 112.2, "lon_max": 112.8, "districts": {}},
            "江门市": {"lat_min": 22.3, "lat_max": 22.8, "lon_min": 112.4, "lon_max": 113.0, "districts": {}},
            "茂名市": {"lat_min": 21.3, "lat_max": 21.8, "lon_min": 110.7, "lon_max": 111.3, "districts": {}},
            "惠州市": {"lat_min": 22.8, "lat_max": 23.5, "lon_min": 114.3, "lon_max": 114.9, "districts": {}},
            "梅州市": {"lat_min": 24.0, "lat_max": 24.4, "lon_min": 116.0, "lon_max": 116.4, "districts": {}},
            "汕尾市": {"lat_min": 22.7, "lat_max": 23.1, "lon_min": 115.2, "lon_max": 116.0, "districts": {}},
            "河源市": {"lat_min": 23.6, "lat_max": 24.3, "lon_min": 114.4, "lon_max": 115.2, "districts": {}},
            "阳江市": {"lat_min": 21.7, "lat_max": 22.3, "lon_min": 111.4, "lon_max": 112.0, "districts": {}},
            "清远市": {"lat_min": 23.4, "lat_max": 24.2, "lon_min": 112.9, "lon_max": 113.5, "districts": {}},
            "东莞市": {"lat_min": 22.8, "lat_max": 23.1, "lon_min": 113.6, "lon_max": 114.1, "districts": {}},
            "中山市": {"lat_min": 22.4, "lat_max": 22.7, "lon_min": 113.1, "lon_max": 113.5, "districts": {}},
            "潮州市": {"lat_min": 23.4, "lat_max": 23.7, "lon_min": 116.3, "lon_max": 116.7, "districts": {}},
            "揭阳市": {"lat_min": 22.9, "lat_max": 23.5, "lon_min": 115.8, "lon_max": 116.4, "districts": {}},
            "云浮市": {"lat_min": 22.7, "lat_max": 23.2, "lon_min": 111.9, "lon_max": 112.4, "districts": {}}
        }
    }
}

def match_location_by_coordinates(lat, lon):
    """
    根据经纬度匹配广西或广东的城市和区
    使用简单的矩形范围匹配
    """
    # 检查是否在广东范围内
    for city_name, city_info in guangxi_guangdong_cities["guangdong"]["cities"].items():
        if city_info["lat_min"] <= lat <= city_info["lat_max"] and city_info["lon_min"] <= lon <= city_info["lon_max"]:
            # 进一步检查是否在该城市的某个区内
            for district_name, district_coords in city_info["districts"].items():
                if district_coords["lat_min"] <= lat <= district_coords["lat_max"] and district_coords["lon_min"] <= lon <= district_coords["lon_max"]:
                    return {
                        "province": guangxi_guangdong_cities["guangdong"]["province_name"],
                        "city": city_name,
                        "district": district_name
                    }
            # 如果没有匹配到区，返回城市信息
            return {
                "province": guangxi_guangdong_cities["guangdong"]["province_name"],
                "city": city_name,
                "district": "未知区"
            }
    
    # 检查是否在广西范围内
    for city_name, city_info in guangxi_guangdong_cities["guangxi"]["cities"].items():
        if city_info["lat_min"] <= lat <= city_info["lat_max"] and city_info["lon_min"] <= lon <= city_info["lon_max"]:
            # 进一步检查是否在该城市的某个区内
            for district_name, district_coords in city_info["districts"].items():
                if district_coords["lat_min"] <= lat <= district_coords["lat_max"] and district_coords["lon_min"] <= lon <= district_coords["lon_max"]:
                    return {
                        "province": guangxi_guangdong_cities["guangxi"]["province_name"],
                        "city": city_name,
                        "district": district_name
                    }
            # 如果没有匹配到区，返回城市信息
            return {
                "province": guangxi_guangdong_cities["guangxi"]["province_name"],
                "city": city_name,
                "district": "未知区"
            }
    
    # 默认返回未知
    return {
        "province": "未知省份",
        "city": "未知城市",
        "district": "未知区"
    }

# 测试区一级匹配
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
