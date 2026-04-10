import requests
import json

# 登录请求
login_url = 'http://localhost:5000/api/auth/login'
login_data = {
    'username': 'shy',
    'password': '123456'  # 尝试不同的密码
}

print('发送登录请求...')
try:
    response = requests.post(login_url, json=login_data, timeout=10)
    print(f'登录响应状态码: {response.status_code}')
    print(f'登录响应内容: {response.text}')
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            token = data.get('token')
            print(f'登录成功，获取到token: {token}')
            
            # 测试相册API
            albums_url = 'http://localhost:5000/api/albums'
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            print('\n测试相册API...')
            albums_response = requests.get(albums_url, headers=headers, timeout=10)
            print(f'相册API响应状态码: {albums_response.status_code}')
            print(f'相册API响应内容: {albums_response.text}')
        else:
            print('登录失败:', data.get('error'))
    else:
        print('登录请求失败，状态码:', response.status_code)
except Exception as e:
    print(f'请求失败: {e}')
