import requests

# 测试登录API
def test_login():
    url = 'http://localhost:5000/api/login'
    headers = {'Content-Type': 'application/json'}
    data = {'username': 'admin', 'password': 'password123'}
    
    response = requests.post(url, json=data, headers=headers)
    print(f"登录API响应: {response.status_code}")
    print(f"响应内容: {response.json()}")

# 测试检查登录状态API
def test_check_login():
    url = 'http://localhost:5000/api/check_login'
    
    response = requests.get(url)
    print(f"检查登录状态API响应: {response.status_code}")
    print(f"响应内容: {response.json()}")

if __name__ == "__main__":
    print("测试登录API:")
    test_login()
    print("\n测试检查登录状态API:")
    test_check_login()