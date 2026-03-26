#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
列出所有用户
"""
import sys
sys.path.insert(0, '.')

from db import db_manager

def list_all_users():
    """列出所有用户"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, email, role, created_at FROM users")
        users = cursor.fetchall()
        
        print("=" * 80)
        print(f"{'ID':<5} {'用户名':<20} {'邮箱':<30} {'角色':<10} {'创建时间'}")
        print("=" * 80)
        
        for user in users:
            created_at = user['created_at']
            if isinstance(created_at, int):
                from datetime import datetime
                created_at = datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{user['id']:<5} {user['username']:<20} {str(user['email']):<30} {user['role']:<10} {created_at}")
        
        print("=" * 80)
        print(f"共 {len(users)} 个用户")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == '__main__':
    list_all_users()
