import pymysql
import time

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '20031221',
    'database': 'flower_recognition',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def test_like():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查 likes 表结构
        cursor.execute("DESCRIBE likes")
        print("=== likes 表结构 ===")
        for row in cursor.fetchall():
            print(row)
        
        # 测试插入数据
        post_id = 1
        user_id = 1
        now = int(time.time())
        print(f"\n=== 测试插入数据 ===")
        print(f"post_id={post_id}, user_id={user_id}, created_at={now}, type={type(now)}")
        
        try:
            cursor.execute('''
            INSERT INTO likes (post_id, user_id, created_at)
            VALUES (%s, %s, %s)
            ''', (post_id, user_id, now))
            conn.commit()
            print("插入成功！")
        except Exception as e:
            conn.rollback()
            print(f"插入失败: {str(e)}")
        
        conn.close()
    except Exception as e:
        print(f"连接数据库失败: {str(e)}")

if __name__ == "__main__":
    test_like()