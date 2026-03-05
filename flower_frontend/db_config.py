#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""MySQL数据库配置"""

import os

# 数据库配置
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'flower_recognition')

# SQL文件路径
SCHEMA_SQL = 'flower_recognition.sql'

def get_db_connection():
    """获取MySQL数据库连接"""
    import pymysql
    
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

def init_mysql_db():
    """初始化MySQL数据库"""
    import pymysql
    
    try:
        print("[调试] 开始执行init_mysql_db函数")
        print("正在尝试连接到MySQL数据库...")
        
        # 先连接到mysql系统数据库
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()
        
        # 检查数据库是否存在
        cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s", (DB_NAME,))
        result = cursor.fetchone()
        
        if not result:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"数据库 {DB_NAME} 创建成功")
        
        cursor.close()
        conn.close()
        
        # 连接到指定数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("成功连接到MySQL数据库")
        
        # 执行SQL文件初始化
        if os.path.exists(SCHEMA_SQL):
            with open(SCHEMA_SQL, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        # 忽略已存在表的错误
                        if "already exists" not in str(e):
                            print(f"执行SQL语句时出错: {str(e)}")
            
            conn.commit()
            conn.close()
            print(f"数据库已从 {SCHEMA_SQL} 初始化完成")
        else:
            print(f"SQL文件不存在: {SCHEMA_SQL}")
            
    except Exception as e:
        print(f"数据库初始化失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        print("请检查MySQL数据库配置")
