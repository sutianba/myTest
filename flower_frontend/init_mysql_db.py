#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""MySQL数据库初始化脚本"""

import pymysql
import time
import os

# 基准目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def init_mysql_database():
    """初始化MySQL数据库"""
    
    # MySQL数据库配置
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '20031221',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    try:
        # 连接MySQL服务器（不指定数据库）
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 创建数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS flower_recognition CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute("USE flower_recognition")
        
        # 读取并执行SQL文件
        sql_file_path = os.path.join(BASE_DIR, 'database.sql')
        if os.path.exists(sql_file_path):
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句并执行
            sql_statements = sql_content.split(';')
            for statement in sql_statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                        print(f"执行SQL: {statement[:50]}...")
                    except Exception as e:
                        print(f"执行SQL失败: {statement[:50]}...")
                        print(f"错误: {e}")
        else:
            print(f"SQL文件不存在: {sql_file_path}")
            return False
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("MySQL数据库初始化完成！")
        return True
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接"""
    
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '20031221',
        'database': 'flower_recognition',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 测试查询
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("数据库中的表:")
        for table in tables:
            print(f"  - {table['Tables_in_flower_recognition']}")
        
        # 测试用户表结构
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        print("\n用户表结构:")
        for column in columns:
            print(f"  - {column['Field']}: {column['Type']}")
        
        cursor.close()
        conn.close()
        
        print("\n数据库连接测试成功！")
        return True
        
    except Exception as e:
        print(f"数据库连接测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始初始化MySQL数据库...")
    
    # 初始化数据库
    if init_mysql_database():
        print("\n数据库初始化成功，开始测试连接...")
        
        # 测试连接
        if test_database_connection():
            print("\n数据库初始化完成！")
        else:
            print("\n数据库连接测试失败！")
    else:
        print("\n数据库初始化失败！")