import pymysql

# 测试不同的密码组合
test_passwords = ['', 'password', 'root', '123456', '12345678']

def test_mysql_connection(password):
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password=password,
            connect_timeout=5
        )
        connection.close()
        return True
    except pymysql.err.OperationalError as e:
        return False
    except Exception as e:
        return False

print("测试MySQL root用户密码...")
for password in test_passwords:
    result = test_mysql_connection(password)
    password_display = "空密码" if password == '' else password
    print(f"密码 '{password_display}': {'✓ 成功' if result else '✗ 失败'}")
