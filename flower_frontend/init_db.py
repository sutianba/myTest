import pymysql

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '20031221',
    'database': 'flower_recognition',
    'charset': 'utf8mb4'
}

# 连接MySQL服务器（不指定数据库）
conn = pymysql.connect(
    host=DB_CONFIG['host'],
    user=DB_CONFIG['user'],
    password=DB_CONFIG['password'],
    charset='utf8mb4'
)
cursor = conn.cursor()

# 删除现有数据库
cursor.execute(f"DROP DATABASE IF EXISTS {DB_CONFIG['database']}")
print(f"数据库 {DB_CONFIG['database']} 已删除")

# 创建新数据库
cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
print(f"数据库 {DB_CONFIG['database']} 已创建")

conn.commit()
conn.close()
print('数据库重新初始化完成')
