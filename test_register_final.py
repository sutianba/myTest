#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
测试注册功能
"""

import json
import requests

# 测试注册接口
url = "http://localhost:5000/api/register"
headers = {
    "Content-Type": "application/json"
}

# 生成一个唯一的用户名和邮箱
test_id = 999999
data = {
    "username": f"testuser_{test_id}",
    "email": f"testuser_{test_id}@example.com",
    "password": "123456"
}

print(f"测试注册用户: {data['username']}")
print(f"邮箱: {data['email']}")

try:
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
except Exception as e:
    print(f"错误: {e}")
