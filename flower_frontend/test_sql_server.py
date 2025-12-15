#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
SQL Server连接测试脚本
用于测试与SQL Server数据库的连接和基本操作
"""

import pyodbc
import traceback

def test_sql_server_connection():
    """测试SQL Server数据库连接"""
    print("开始测试SQL Server数据库连接...")
    
    # SQL Server连接配置
    SERVER = 'localhost'
    DATABASE = 'flower_recognition'
    USERNAME = 'sa'
    PASSWORD = 'Password123'
    
    try:
        # 尝试连接到SQL Server
        connection_string = f"DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"
        print(f"连接字符串: {connection_string}")
        
        connection = pyodbc.connect(connection_string)
        print("✓ 成功连接到SQL Server数据库")
        
        # 测试创建表
        cursor = connection.cursor()
        print("\n尝试创建users表...")
        
        cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
        CREATE TABLE users (
            id INT PRIMARY KEY IDENTITY(1,1),
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE()
        )
        ''')
        
        connection.commit()
        print("✓ 表创建成功或已存在")
        
        # 测试插入数据
        print("\n尝试插入测试数据...")
        test_username = 'test_user'
        test_password = 'test_pass'
        
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (test_username, test_password))
        connection.commit()
        print("✓ 数据插入成功")
        
        # 测试查询数据
        print("\n尝试查询数据...")
        cursor.execute("SELECT * FROM users WHERE username = ?", (test_username,))
        
        # 将结果转换为字典
        columns = [column[0] for column in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        if rows:
            print(f"✓ 查询成功，结果: {rows}")
        else:
            print("✗ 查询结果为空")
        
        # 测试删除数据
        print("\n尝试删除测试数据...")
        cursor.execute("DELETE FROM users WHERE username = ?", (test_username,))
        connection.commit()
        print("✓ 数据删除成功")
        
        # 关闭连接
        cursor.close()
        connection.close()
        print("\n✓ 连接已关闭，测试完成")
        
        return True
        
    except Exception as e:
        print(f"\n✗ 连接或操作失败: {type(e).__name__}: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_sql_server_connection()
