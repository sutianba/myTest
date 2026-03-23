import pymysql

# 连接数据库
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='20031221',
    database='flower_recognition',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

cursor = conn.cursor()

# 检查users表结构
print('Users table structure:')
cursor.execute('DESCRIBE users')
for row in cursor.fetchall():
    print(row)

# 检查roles表结构
print('\nRoles table structure:')
cursor.execute('DESCRIBE roles')
for row in cursor.fetchall():
    print(row)

# 检查user_roles表结构
print('\nUser_roles table structure:')
cursor.execute('DESCRIBE user_roles')
for row in cursor.fetchall():
    print(row)

conn.close()
