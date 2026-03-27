#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
修复管理员用户的角色关联
"""
import sys
sys.path.insert(0, '.')

from db import db_manager

def fix_admin_role_links():
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 获取所有在users表中是admin/super_admin但没有user_roles关联的用户
        cursor.execute('''
            SELECT u.id, u.username, u.role
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            WHERE u.role IN ('admin', 'super_admin') AND ur.user_id IS NULL
        ''')
        users_without_link = cursor.fetchall()
        
        print("=" * 60)
        print("修复没有角色关联的管理员用户")
        print("=" * 60)
        
        for user in users_without_link:
            user_id = user['id']
            username = user['username']
            user_role = user['role']
            
            # 获取对应角色的ID
            cursor.execute("SELECT id FROM roles WHERE name = %s", (user_role,))
            role = cursor.fetchone()
            
            if role:
                role_id = role['id']
                # 添加user_roles关联
                cursor.execute(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                    (user_id, role_id)
                )
                print(f"✅ 为用户 {username} (ID: {user_id}) 添加 {user_role} 角色关联")
            else:
                print(f"❌ 未找到角色 {user_role}")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("修复完成")
        print("=" * 60)
        
        # 验证修复结果
        cursor.execute('''
            SELECT u.username, u.role, r.name as linked_role
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            WHERE u.role IN ('admin', 'super_admin')
        ''')
        results = cursor.fetchall()
        
        print("\n验证结果：")
        for r in results:
            print(f"  用户: {r['username']}, users表: {r['role']}, 关联: {r['linked_role']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == '__main__':
    fix_admin_role_links()
