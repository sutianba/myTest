import pymysql
import sys

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '20031221',
    'database': 'flower_recognition',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def check_albums_table():
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查 albums 表结构
        cursor.execute("DESCRIBE albums")
        columns = cursor.fetchall()
        
        print("albums 表结构:")
        print("-" * 60)
        for col in columns:
            print(f"  {col['Field']}: {col['Type']} (Null: {col['Null']}, Default: {col['Default']})")
        
        print("\n" + "=" * 60)
        
        # 检查是否有触发器
        cursor.execute("SHOW TRIGGERS LIKE 'albums'")
        triggers = cursor.fetchall()
        
        print("\nalbums 表触发器:")
        print("-" * 60)
        if triggers:
            for trig in triggers:
                print(f"  {trig['Trigger']}: {trig['Event']} {trig['Timing']} -> {trig['Statement'][:50]}...")
        else:
            print("  无触发器")
        
        conn.close()
    except Exception as e:
        import traceback
        print(f"错误: {e}")
        traceback.print_exc()
        if conn:
            conn.close()
        sys.exit(1)

if __name__ == "__main__":
    check_albums_table()
