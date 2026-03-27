#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
检查管理员是否有manage_admins权限
"""
import sys
sys.path.insert(0, '.')

from db import db_manager

def check_permission():
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 检查admin是否有manage_admins权限
        cursor.execute('''
            SELECT r.name as role_name, p.name as perm_name 
            FROM role_permissions rp
            JOIN roles r ON rp.role_id = r.id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE r.name = 'admin' AND p.name = 'manage_admins'
        ''')
        result = cursor.fetchone()
        
        if result:
            print(f"✅ 管理员角色有 manage_admins 权限")
        else:
            print(f"❌ 管理员角色没有 manage_admins 权限")
            
            # 查找manage_admins权限ID
            cursor.execute("SELECT id FROM permissions WHERE name = 'manage_admins'")
            perm = cursor.fetchone()
            
            if perm:
                perm_id = perm['id']
                # 查找admin角色ID
                cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
                role = cursor.fetchone()
                
                if role:
                    role_id = role['id']
                    # 添加权限
                    cursor.execute(
                        "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)",
                        (role_id, perm_id)
                    )
                    conn.commit()
                    print(f"✅ 已为管理员添加 manage_admins 权限")
            else:
                print("❌ 未找到 manage_admins 权限")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == '__main__':
    check_permission()
