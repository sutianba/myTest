#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
检查管理员用户权限
"""
import sys
sys.path.insert(0, '.')

from db import db_manager

def check_admin_permissions():
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 获取所有管理员用户
        cursor.execute("SELECT id, username, email, role FROM users WHERE role IN ('admin', 'super_admin')")
        admins = cursor.fetchall()
        
        print("=" * 60)
        print("检查管理员用户权限")
        print("=" * 60)
        
        for admin in admins:
            user_id = admin['id']
            username = admin['username']
            email = admin['email']
            user_role = admin['role']
            
            print(f"\n用户: {username} (ID: {user_id}, 邮箱: {email})")
            print(f"  users表role字段: {user_role}")
            
            # 检查user_roles关联
            cursor.execute('''
                SELECT r.name, r.id
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = %s
            ''', (user_id,))
            linked_roles = cursor.fetchall()
            
            if linked_roles:
                for linked in linked_roles:
                    role_name = linked['name']
                    role_id = linked['id']
                    print(f"  user_roles关联: {role_name} (ID: {role_id})")
                    
                    # 检查该角色的权限
                    cursor.execute('''
                        SELECT p.name, p.description
                        FROM permissions p
                        JOIN role_permissions rp ON p.id = rp.permission_id
                        WHERE rp.role_id = %s AND p.name = 'manage_admins'
                    ''', (role_id,))
                    perm = cursor.fetchone()
                    
                    if perm:
                        print(f"    ✅ 有 manage_admins 权限")
                    else:
                        print(f"    ❌ 没有 manage_admins 权限")
            else:
                print(f"  ❌ 没有user_roles关联")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_admin_permissions()
