#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
测试MySQL数据库连接
"""

import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_config import init_mysql_db, get_db_connection

def test_mysql_connection():
    """测试MySQL数据库连接"""
    print("=" * 60)
    print("开始测试MySQL数据库连接")
    print("=" * 60)
    
    try:
        # 初始化数据库
        print("\n[步骤1] 初始化数据库...")
        init_mysql_db()
        print("数据库初始化成功")
        
        # 获取数据库连接
        print("\n[步骤2] 获取数据库连接...")
        conn = get_db_connection()
        print("数据库连接成功")
        
        # 测试查询
        print("\n[步骤3] 测试查询...")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        print(f"users表中的记录数: {result['count']}")
        
        # 查询所有用户
        cursor.execute("SELECT id, username, role FROM users")
        users = cursor.fetchall()
        print(f"\n用户列表:")
        for user in users:
            print(f"  ID: {user['id']}, 用户名: {user['username']}, 角色: {user['role']}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("MySQL数据库测试成功！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n数据库测试失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mysql_connection()
    sys.exit(0 if success else 1)