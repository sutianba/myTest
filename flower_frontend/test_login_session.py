import requests

# 创建会话对象以保持cookie
session = requests.Session()

# 测试登录API
def test_login():
    url = 'http://localhost:5000/api/login'
    headers = {'Content-Type': 'application/json'}
    data = {'username': 'admin', 'password': 'password123'}
    
    response = session.post(url, json=data, headers=headers)
    print(f"登录API响应: {response.status_code}")
    print(f"响应内容: {response.json()}")
    return response.json()

# 测试检查登录状态API（使用同一个会话）
def test_check_login():
    url = 'http://localhost:5000/api/check_login'
    
    response = session.get(url)
    print(f"检查登录状态API响应: {response.status_code}")
    print(f"响应内容: {response.json()}")
    return response.json()

# 测试登出API
def test_logout():
    url = 'http://localhost:5000/api/logout'
    
    response = session.post(url)
    print(f"登出API响应: {response.status_code}")
    print(f"响应内容: {response.json()}")
    return response.json()

if __name__ == "__main__":
    print("测试登录API:")
    login_result = test_login()
    
    if login_result.get('success'):
        print("\n登录成功，测试检查登录状态API:")
        check_login_result = test_check_login()
        
        print("\n测试登出API:")
        logout_result = test_logout()
        
        print("\n登出后测试检查登录状态API:")
        check_login_result_after_logout = test_check_login()