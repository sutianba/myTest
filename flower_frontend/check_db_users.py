import sqlite3
import os

# 获取数据库文件路径
db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flower_recognition.db')

# 连接到SQLite数据库
conn = sqlite3.connect(db_file)
conn.row_factory = sqlite3.Row  # 使结果可以像字典一样访问
cursor = conn.cursor()

# 查询所有用户
cursor.execute('SELECT * FROM users')
users = cursor.fetchall()

# 打印用户信息
print('数据库中的用户:')
if users:
    for user in users:
        print(f'  ID: {user["id"]}, 用户名: {user["username"]}, 密码哈希: {user["password_hash"]}')
else:
    print('  没有用户')

# 关闭连接
conn.close()
