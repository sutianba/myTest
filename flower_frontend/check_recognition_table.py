import pymysql

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '20031221',
    'database': 'flower_recognition',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def check_recognition_table():
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查 recognition_results 表结构
        cursor.execute("DESCRIBE recognition_results")
        columns = cursor.fetchall()
        
        print("recognition_results 表结构:")
        print("-" * 60)
        for col in columns:
            print(f"  {col['Field']}: {col['Type']} (Null: {col['Null']}, Default: {col['Default']})")
        
        conn.close()
    except Exception as e:
        import traceback
        print(f"错误: {e}")
        traceback.print_exc()
        if conn:
            conn.close()

if __name__ == "__main__":
    check_recognition_table()
