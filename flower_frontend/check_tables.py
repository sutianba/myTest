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

def check_tables():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 查询所有表
        cursor.execute("SHOW TABLES")
        print("=== 数据库中的表 ===")
        for table in cursor.fetchall():
            print(table)
        
        # 检查 comment_likes 表是否存在
        cursor.execute("SHOW TABLES LIKE 'comment_likes'")
        result = cursor.fetchone()
        if result:
            print("\n=== comment_likes 表存在 ===")
            cursor.execute("DESCRIBE comment_likes")
            for row in cursor.fetchall():
                print(row)
        else:
            print("\n=== comment_likes 表不存在 ===")
        
        conn.close()
    except Exception as e:
        print(f"查询失败: {str(e)}")

if __name__ == "__main__":
    check_tables()