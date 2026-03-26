#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
检查角色和权限配置
"""
import sys
sys.path.insert(0, '.')

from db import db_manager

def check_roles_and_permissions():
    """检查角色和权限配置"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        print("=" * 60)
        print("角色表 (roles)")
        print("=" * 60)
        cursor.execute("SELECT * FROM roles")
        roles = cursor.fetchall()
        for role in roles:
            print(f"ID: {role['id']}, 名称: {role['name']}, 描述: {role['description']}")
        
        print("\n" + "=" * 60)
        print("权限表 (permissions)")
        print("=" * 60)
        cursor.execute("SELECT * FROM permissions")
        permissions = cursor.fetchall()
        for perm in permissions:
            print(f"ID: {perm['id']}, 名称: {perm['name']}, 描述: {perm['description']}")
        
        print("\n" + "=" * 60)
        print("角色权限关联 (role_permissions)")
        print("=" * 60)
        cursor.execute('''
            SELECT r.name as role_name, p.name as perm_name 
            FROM role_permissions rp
            JOIN roles r ON rp.role_id = r.id
            JOIN permissions p ON rp.permission_id = p.id
            ORDER BY r.name
        ''')
        role_perms = cursor.fetchall()
        current_role = None
        for rp in role_perms:
            if rp['role_name'] != current_role:
                current_role = rp['role_name']
                print(f"\n【{current_role}】")
            print(f"  - {rp['perm_name']}")
        
        print("\n" + "=" * 60)
        print("用户角色 (user_roles)")
        print("=" * 60)
        cursor.execute('''
            SELECT u.username, u.role, r.name as role_name
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            ORDER BY u.id DESC
            LIMIT 10
        ''')
        user_roles = cursor.fetchall()
        for ur in user_roles:
            print(f"用户: {ur['username']}, 表role: {ur['role']}, 关联role: {ur['role_name']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == '__main__':
    check_roles_and_permissions()
