import pymysql

# 测试数据库连接
try:
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='20031221',
        database='flower_recognition',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    print('数据库连接成功')
    conn.close()
except Exception as e:
    print(f'数据库连接失败: {str(e)}')

# 测试Flask导入
try:
    from flask import Flask
    print('Flask导入成功')
except Exception as e:
    print(f'Flask导入失败: {str(e)}')