import requests

# 测试点赞 API
def test_like_api():
    url = "http://127.0.0.1:5000/api/posts/1/like"
    
    # 先获取 token（需要登录）
    login_url = "http://127.0.0.1:5000/api/auth/login"
    login_data = {
        "username": "shy",
        "password": "123456"
    }
    
    try:
        # 登录
        login_response = requests.post(login_url, json=login_data)
        print(f"登录响应: {login_response.status_code}")
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get('token')
            print(f"获取到 token: {token[:20]}...")
            
            # 测试点赞
            headers = {
                'Authorization': f'Bearer {token}'
            }
            like_response = requests.post(url, headers=headers)
            print(f"点赞响应状态码: {like_response.status_code}")
            print(f"点赞响应内容: {like_response.text}")
        else:
            print(f"登录失败: {login_response.text}")
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == "__main__":
    test_like_api()