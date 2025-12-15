import requests
import json

# 测试注册功能
def test_register():
    print("开始测试注册功能...")
    
    # 测试1：正常注册新用户
    print("\n1. 测试正常注册新用户...")
    register_url = "http://127.0.0.1:5000/api/register"
    
    # 测试数据：新用户
    new_user = {
        "username": "newtestuser",
        "password": "test1234"
    }
    
    try:
        response = requests.post(register_url, json=new_user)
        result = response.json()
        print(f"注册响应: {result}")
        
        if result["success"]:
            print("✓ 注册成功！")
            
            # 测试2：使用新注册的用户登录
            print("\n2. 测试使用新注册的用户登录...")
            login_url = "http://127.0.0.1:5000/api/login"
            
            login_data = {
                "username": "newtestuser",
                "password": "test1234"
            }
            
            login_response = requests.post(login_url, json=login_data)
            login_result = login_response.json()
            print(f"登录响应: {login_result}")
            
            if login_result["success"]:
                print("✓ 登录成功！注册和登录功能正常工作。")
            else:
                print(f"✗ 登录失败: {login_result.get('error')}")
        else:
            print(f"✗ 注册失败: {result.get('error')}")
            
    except Exception as e:
        print(f"✗ 注册请求失败: {str(e)}")
    
    # 测试3：测试注册已存在的用户名
    print("\n3. 测试注册已存在的用户名...")
    
    existing_user = {
        "username": "newtestuser",
        "password": "test12345"
    }
    
    try:
        response = requests.post(register_url, json=existing_user)
        result = response.json()
        print(f"注册响应: {result}")
        
        if not result["success"] and result["error"] == "用户名已存在":
            print("✓ 正确拒绝了已存在的用户名注册")
        else:
            print("✗ 未能正确处理已存在的用户名")
    except Exception as e:
        print(f"✗ 注册请求失败: {str(e)}")
    
    # 测试4：测试密码长度不足
    print("\n4. 测试密码长度不足...")
    
    short_password_user = {
        "username": "shortpassuser",
        "password": "123"
    }
    
    try:
        response = requests.post(register_url, json=short_password_user)
        result = response.json()
        print(f"注册响应: {result}")
        
        if not result["success"] and "密码长度" in result["error"]:
            print("✓ 正确拒绝了短密码")
        else:
            print("✗ 未能正确处理短密码")
    except Exception as e:
        print(f"✗ 注册请求失败: {str(e)}")
    
    print("\n注册功能测试完成！")

if __name__ == "__main__":
    # 先重新启动服务器
    import subprocess
    import time
    
    print("正在启动Flask服务器...")
    server_process = subprocess.Popen(["python", "app.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # 等待服务器启动
    time.sleep(3)
    
    # 运行测试
    test_register()
    
    # 关闭服务器
    print("\n正在关闭Flask服务器...")
    server_process.terminate()