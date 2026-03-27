#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
检查用户角色关联
"""
import sys
sys.path.insert(0, '.')

from db import db_manager

def check_user_role():
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 获取所有管理员用户
        cursor.execute("SELECT id, username, role FROM users WHERE role IN ('admin', 'super_admin')")
        admins = cursor.fetchall()
        
        print("=" * 60)
        print("检查管理员用户的角色关联")
        print("=" * 60)
        
        for admin in admins:
            user_id = admin['id']
            username = admin['username']
            user_role = admin['role']
            
            # 检查user_roles表中的关联
            cursor.execute('''
                SELECT r.name 
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = %s
            ''', (user_id,))
            linked_roles = cursor.fetchall()
            
            print(f"\n用户: {username} (ID: {user_id})")
            print(f"  users表role字段: {user_role}")
            print(f"  user_roles表关联: {[r['name'] for r in linked_roles]}")
            
            # 检查是否有manage_admins权限
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = %s AND p.name = 'manage_admins'
            ''', (user_id,))
            result = cursor.fetchone()
            has_perm = result['count'] > 0 if result else False
            print(f"  是否有manage_admins权限: {'是' if has_perm else '否'}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == '__main__':
    check_user_role()
