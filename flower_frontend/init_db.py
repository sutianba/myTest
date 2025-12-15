#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import pymysql
import hashlib

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',  # 尝试使用常见密码
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def init_database():
    try:
        # 连接到MySQL服务器
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 创建数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS flower_recognition CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("数据库创建成功")
        
        # 选择数据库
        cursor.execute("USE flower_recognition")
        
        # 创建用户表
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(64) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)
        print("用户表创建成功")
        
        # 插入初始测试用户
        users = [
            ("admin", "password123"),
            ("test", "test123")
        ]
        
        for username, password in users:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            # 检查用户是否已存在
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()
            
            if not existing_user:
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                    (username, hashed_password)
                )
                print(f"用户 {username} 创建成功")
            else:
                print(f"用户 {username} 已存在")
        
        # 提交更改
        connection.commit()
        
    except pymysql.err.OperationalError as e:
        if e.args[0] == 1045:  # Access denied
            print("数据库连接失败: 用户名或密码错误")
            print("请检查MySQL配置，尤其是root用户的密码")
        elif e.args[0] == 2003:  # Can't connect to server
            print("数据库连接失败: 无法连接到MySQL服务器")
            print("请确保MySQL服务已启动")
        else:
            print(f"数据库连接失败: {e}")
    except Exception as e:
        print(f"初始化数据库时发生错误: {e}")
    finally:
        # 关闭连接
        if 'connection' in locals():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    init_database()
