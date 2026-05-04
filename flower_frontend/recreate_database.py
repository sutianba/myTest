import pymysql

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '20031221',
    'charset': 'utf8mb4'
}

def recreate_database():
    try:
        # 连接到MySQL服务器（不指定数据库）
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 删除旧数据库
        cursor.execute("DROP DATABASE IF EXISTS flower_recognition")
        print("已删除旧数据库")
        
        # 创建新数据库
        cursor.execute("CREATE DATABASE flower_recognition")
        print("已创建新数据库")
        
        conn.close()
        print("数据库重建完成，请重启应用")
    except Exception as e:
        print(f"重建数据库失败: {str(e)}")

if __name__ == "__main__":
    recreate_database()