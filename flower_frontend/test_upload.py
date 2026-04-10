import requests
import base64
import os

# 登录获取token
def login():
    login_url = 'http://localhost:5000/api/auth/login'
    login_data = {
        'username': 'shy',
        'password': '123456'
    }
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            return data.get('token')
    return None

# 上传图片
def upload_image(token):
    upload_url = 'http://localhost:5000/api/detect'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 使用一个测试图片
    test_image_path = 'test_image.jpg'
    if not os.path.exists(test_image_path):
        # 创建一个简单的测试图片
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_image_path)
    
    # 读取图片并转换为base64
    with open(test_image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # 构建请求数据
    data = {
        'image': f'data:image/jpeg;base64,{image_data}',
        'save_to_album': True
    }
    
    print('上传图片...')
    response = requests.post(upload_url, json=data, headers=headers)
    print(f'上传响应状态码: {response.status_code}')
    print(f'上传响应内容: {response.text}')
    
    return response

# 测试相册API
def test_albums(token):
    albums_url = 'http://localhost:5000/api/albums'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print('\n测试相册API...')
    response = requests.get(albums_url, headers=headers)
    print(f'相册API响应状态码: {response.status_code}')
    print(f'相册API响应内容: {response.text}')

if __name__ == '__main__':
    token = login()
    if token:
        print(f'登录成功，token: {token}')
        upload_image(token)
        test_albums(token)
    else:
        print('登录失败')
