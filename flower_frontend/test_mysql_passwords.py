import pymysql

# 尝试不同的密码组合
test_passwords = ['', 'password', 'root', '123456', '12345678']

def test_mysql_passwords():
    print("测试不同的MySQL密码组合...")
    
    for password in test_passwords:
        try:
            # 尝试连接到MySQL服务器
            connection = pymysql.connect(host='localhost', user='root', password=password)
            print(f"✓ 成功连接到MySQL服务器，密码: '{password}'")
            connection.close()
            
            # 尝试连接到flower_recognition数据库
            try:
                connection = pymysql.connect(
                    host='localhost',
                    user='root',
                    password=password,
                    db='flower_recognition',
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
                print(f"✓ 成功连接到flower_recognition数据库，密码: '{password}'")
                connection.close()
                return password
            except Exception as e:
                print(f"✗ 无法连接到flower_recognition数据库，密码: '{password}' - 错误: {str(e)}")
                
        except Exception as e:
            print(f"✗ 无法连接到MySQL服务器，密码: '{password}' - 错误: {str(e)}")
    
    print("\n所有测试的密码都无法连接到MySQL服务器。")
    return None

if __name__ == "__main__":
    test_mysql_passwords()