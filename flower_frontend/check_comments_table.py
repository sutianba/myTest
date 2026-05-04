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

def check_table():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查 comments 表结构
        cursor.execute("DESCRIBE comments")
        print("=== comments 表结构 ===")
        for row in cursor.fetchall():
            print(row)
        
        conn.close()
    except Exception as e:
        print(f"查询失败: {str(e)}")

if __name__ == "__main__":
    check_table()