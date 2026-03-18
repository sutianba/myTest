#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""检查SQLite数据库表结构"""

import sqlite3

# 数据库文件路径
DB_PATH = 'flower_recognition.db'

def check_database_structure():
    """检查数据库表结构"""
    try:
        # 连接到数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("=== 数据库表结构检查 ===")
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n数据库中的表: {len(tables)}")
        for table in tables:
            table_name = table[0]
            print(f"\n--- 表: {table_name} ---")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("列信息:")
            for column in columns:
                print(f"  {column[1]} ({column[2]}) - {'NOT NULL' if column[3] else ''} {'PRIMARY KEY' if column[5] else ''}")
        
        # 检查用户表数据
        print("\n=== 用户表数据 ===")
        cursor.execute("SELECT * FROM users LIMIT 5;")
        users = cursor.fetchall()
        print(f"用户数量: {len(users)}")
        for user in users:
            print(f"  ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}, 验证状态: {user[4]}")
        
        # 检查识别结果表数据
        print("\n=== 识别结果表数据 ===")
        cursor.execute("SELECT * FROM recognition_results LIMIT 5;")
        results = cursor.fetchall()
        print(f"识别结果数量: {len(results)}")
        for result in results:
            print(f"  ID: {result[0]}, 用户ID: {result[1]}, 结果: {result[3]}, 置信度: {result[4]}")
        
        conn.close()
        print("\n=== 检查完成 ===")
        
    except Exception as e:
        print(f"检查数据库时出错: {e}")

if __name__ == '__main__':
    check_database_structure()
