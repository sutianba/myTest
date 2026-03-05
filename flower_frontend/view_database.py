#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""查看数据库结构和内容"""

import os

# 检查是否使用MySQL
USE_MYSQL = os.environ.get('USE_MYSQL', 'false').lower() == 'true'

if USE_MYSQL:
    try:
        import pymysql
    except ImportError:
        print("错误: 请安装PyMySQL: pip install pymysql")
        exit(1)
    
    # MySQL数据库配置
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'flower_recognition')
    
    print("=" * 50)
    print("MySQL数据库配置")
    print("=" * 50)
    print(f"  主机: {DB_HOST}")
    print(f"  端口: {DB_PORT}")
    print(f"  用户: {DB_USER}")
    print(f"  密码: {'*' * len(DB_PASSWORD) if DB_PASSWORD else '(无)'}")
    print(f"  数据库: {DB_NAME}")
    print("=" * 50)
    
    try:
        # 连接到MySQL数据库
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()
        
        # 查询所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("\n数据库中的表:")
        print("-" * 50)
        for table in tables:
            table_name = list(table.values())[0]
            print(f"  - {table_name}")
        
        # 查看每个表的结构和数据
        for table in tables:
            table_name = list(table.values())[0]
            print(f"\n{'=' * 50}")
            print(f"表名: {table_name}")
            print(f"{'=' * 50}")
            
            # 查看表结构
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            print("\n表结构:")
            print("-" * 50)
            for col in columns:
                print(f"  {col['Field']:25} {col['Type']:20} {'NULL' if col['Null'] == 'YES' else 'NOT NULL'}")
            
            # 查看表数据
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            print(f"\n数据行数: {len(rows)}")
            if rows:
                print("\n数据内容:")
                print("-" * 50)
                for i, row in enumerate(rows, 1):
                    print(f"  行 {i}: {row}")
            else:
                print("\n  (空表)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n错误: 连接MySQL数据库失败 - {str(e)}")
        print("请检查MySQL是否运行以及数据库配置是否正确")
else:
    import sqlite3
    
    # SQLite数据库配置
    DATABASE_PATH = 'flower_recognition.db'
    
    print("=" * 50)
    print("SQLite数据库配置")
    print("=" * 50)
    print(f"  数据库文件: {DATABASE_PATH}")
    print("=" * 50)
    
    if not os.path.exists(DATABASE_PATH):
        print(f"\n错误: 数据库文件不存在 - {DATABASE_PATH}")
        exit(1)
    
    try:
        # 连接到SQLite数据库
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询所有表
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = cursor.fetchall()
        
        print("\n数据库中的表:")
        print("-" * 50)
        for table in tables:
            print(f"  - {table[0]}")
        
        # 查看每个表的结构和数据
        for table in tables:
            table_name = table[0]
            print(f"\n{'=' * 50}")
            print(f"表名: {table_name}")
            print(f"{'=' * 50}")
            
            # 查看表结构
            cursor.execute(f'PRAGMA table_info({table_name})')
            columns = cursor.fetchall()
            print("\n表结构:")
            print("-" * 50)
            for col in columns:
                print(f"  {col[1]:20} {col[2]:15} {'NULL' if col[3] == 1 else 'NOT NULL'}")
            
            # 查看表数据
            cursor.execute(f'SELECT * FROM {table_name}')
            rows = cursor.fetchall()
            print(f"\n数据行数: {len(rows)}")
            if rows:
                print("\n数据内容:")
                print("-" * 50)
                for i, row in enumerate(rows, 1):
                    # 获取行数据的字典表示
                    row_dict = {}
                    for j, col in enumerate(columns):
                        row_dict[col[1]] = row[j]
                    print(f"  行 {i}: {row_dict}")
            else:
                print("\n  (空表)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n错误: 连接SQLite数据库失败 - {str(e)}")

print("\n" + "=" * 50)
print("数据库查询完成")
print("=" * 50)
