import pymysql

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '20031221',
    'database': 'flower_recognition',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def check_users():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 查询用户表
        cursor.execute("SELECT id, username, email, role FROM users")
        print("=== 用户列表 ===")
        for user in cursor.fetchall():
            print(user)
        
        # 查询帖子表
        cursor.execute("SELECT id, user_id, content FROM posts")
        print("\n=== 帖子列表 ===")
        for post in cursor.fetchall():
            print(post)
        
        conn.close()
    except Exception as e:
        print(f"查询失败: {str(e)}")

if __name__ == "__main__":
    check_users()