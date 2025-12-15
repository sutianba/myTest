import pymysql
import pymysql.cursors

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',  # MySQL密码，与app.py保持一致
    'db': 'flower_recognition',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def test_db_connection():
    print("测试数据库连接...")
    try:
        # 测试连接到MySQL服务器
        connection = pymysql.connect(host=DB_CONFIG['host'], user=DB_CONFIG['user'], password=DB_CONFIG['password'])
        print("✓ 成功连接到MySQL服务器")
        connection.close()
        
        # 测试连接到flower_recognition数据库
        connection = pymysql.connect(**DB_CONFIG)
        print("✓ 成功连接到flower_recognition数据库")
        
        # 测试是否存在users表
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES LIKE 'users'")
        result = cursor.fetchone()
        
        if result:
            print("✓ users表存在")
            
            # 查看users表结构
            cursor.execute("DESCRIBE users")
            table_info = cursor.fetchall()
            print("\nusers表结构:")
            for column in table_info:
                print(f"  {column['Field']}: {column['Type']}")
                
            # 测试插入一条测试记录
            print("\n测试插入一条测试记录...")
            try:
                test_username = "testuser"
                test_password = "testpass123"
                
                # 先检查是否存在
                cursor.execute("SELECT * FROM users WHERE username = %s", (test_username,))
                existing = cursor.fetchone()
                
                if existing:
                    print(f"✗ 测试用户 '{test_username}' 已存在，跳过插入")
                else:
                    cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, SHA2(%s, 256))", (test_username, test_password))
                    connection.commit()
                    print("✓ 成功插入测试记录")
                    
                    # 查询插入的记录
                    cursor.execute("SELECT * FROM users WHERE username = %s", (test_username,))
                    inserted = cursor.fetchone()
                    if inserted:
                        print(f"✓ 成功查询到插入的记录: {inserted['username']}")
            except Exception as e:
                print(f"✗ 插入测试记录失败: {str(e)}")
                connection.rollback()
        else:
            print("✗ users表不存在")
            
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"✗ 数据库连接失败: {str(e)}")

if __name__ == "__main__":
    test_db_connection()