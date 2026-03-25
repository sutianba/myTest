"""
测试识别保存流程
模拟图片上传和识别，测试 recognition_results 和 album_images 表的写入
"""

import requests
import base64
import json

# 测试图片路径
TEST_IMAGE_PATH = "test_flower.jpg"

# 服务地址
BASE_URL = "http://127.0.0.1:5000"

# 登录信息
LOGIN_DATA = {
    "username": "test",
    "password": "123456"
}

def login():
    """登录获取token"""
    print("=== 登录测试账号 ===")
    response = requests.post(f"{BASE_URL}/api/auth/login", json=LOGIN_DATA)
    data = response.json()
    print(f"登录响应: {data}")
    if data.get('success'):
        return data.get('token')
    else:
        print("登录失败")
        return None

def load_image_as_base64(image_path):
    """加载图片并转换为base64"""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_data}"
    except Exception as e:
        print(f"加载图片失败: {e}")
        return None

def test_recognition(token):
    """测试识别和保存流程"""
    print("\n=== 测试识别和保存流程 ===")
    
    # 加载测试图片
    image_base64 = load_image_as_base64(TEST_IMAGE_PATH)
    if not image_base64:
        print("请确保 test_flower.jpg 文件存在")
        return
    
    # 构建请求数据
    data = {
        "image": image_base64,
        "save_to_album": True
    }
    
    # 设置请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # 发送识别请求
    print("发送识别请求...")
    response = requests.post(f"{BASE_URL}/api/detect", json=data, headers=headers)
    
    # 打印响应
    print(f"响应状态码: {response.status_code}")
    response_data = response.json()
    print(f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
    
    # 检查是否成功
    if response_data.get('success'):
        print("\n=== 识别成功 ===")
        # 检查是否保存到相册
        if 'saved_to_album' in response_data.get('results', {}):
            print("✓ 已保存到相册")
            print(f"  相册ID: {response_data['results']['saved_to_album']['album_id']}")
            print(f"  相册名称: {response_data['results']['saved_to_album']['album_name']}")
        else:
            print("✗ 未保存到相册")
    else:
        print("\n=== 识别失败 ===")
        print(f"错误信息: {response_data.get('error')}")

def check_database():
    """检查数据库中的记录"""
    print("\n=== 检查数据库记录 ===")
    
    # 检查 recognition_results 表
    print("\n1. 检查 recognition_results 表:")
    import subprocess
    result = subprocess.run(
        ["mysql", "-u", "root", "-p20031221", "-e", "USE flower_recognition; SELECT id,user_id,image_path FROM recognition_results ORDER BY id DESC LIMIT 3;"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(f"错误: {result.stderr}")
    
    # 检查 album_images 表
    print("\n2. 检查 album_images 表:")
    result = subprocess.run(
        ["mysql", "-u", "root", "-p20031221", "-e", "USE flower_recognition; SELECT id,album_id,image_path,recognition_result_id FROM album_images ORDER BY id DESC LIMIT 3;"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(f"错误: {result.stderr}")

if __name__ == "__main__":
    # 登录获取token
    token = login()
    if token:
        # 测试识别和保存流程
        test_recognition(token)
        # 检查数据库记录
        check_database()
