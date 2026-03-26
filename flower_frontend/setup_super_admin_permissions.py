#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
为超级管理员添加专属权限
"""
import sys
sys.path.insert(0, '.')

from db import db_manager

def setup_super_admin_permissions():
    """设置超级管理员专属权限"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 1. 添加超级管理员专属权限
        super_admin_permissions = [
            ('manage_admins', '管理管理员账户'),
            ('view_operations', '查看操作记录'),
            ('system_settings', '系统设置'),
            ('super_admin_only', '超级管理员专属')
        ]
        
        print("添加超级管理员专属权限...")
        for perm_name, perm_desc in super_admin_permissions:
            try:
                cursor.execute(
                    "INSERT INTO permissions (name, description) VALUES (%s, %s)",
                    (perm_name, perm_desc)
                )
                print(f"  ✅ 添加权限: {perm_name}")
            except Exception as e:
                # 权限可能已存在
                print(f"  ℹ️ 权限已存在: {perm_name}")
        
        conn.commit()
        
        # 2. 获取 super_admin 角色ID
        cursor.execute("SELECT id FROM roles WHERE name = 'super_admin'")
        super_admin_role = cursor.fetchone()
        
        if not super_admin_role:
            print("❌ 未找到 super_admin 角色")
            return
        
        super_admin_id = super_admin_role['id']
        
        # 3. 将专属权限分配给 super_admin
        print("\n分配权限给超级管理员...")
        for perm_name, _ in super_admin_permissions:
            cursor.execute("SELECT id FROM permissions WHERE name = %s", (perm_name,))
            perm = cursor.fetchone()
            
            if perm:
                perm_id = perm['id']
                try:
                    cursor.execute(
                        "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)",
                        (super_admin_id, perm_id)
                    )
                    print(f"  ✅ 分配权限: {perm_name}")
                except Exception as e:
                    print(f"  ℹ️ 权限已分配: {perm_name}")
        
        conn.commit()
        
        # 4. 验证权限分配
        print("\n" + "=" * 60)
        print("超级管理员当前权限:")
        print("=" * 60)
        cursor.execute('''
            SELECT p.name, p.description 
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = %s
            ORDER BY p.name
        ''', (super_admin_id,))
        permissions = cursor.fetchall()
        for perm in permissions:
            print(f"  - {perm['name']}: {perm['description']}")
        
        conn.close()
        print("\n✅ 超级管理员权限设置完成")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == '__main__':
    setup_super_admin_permissions()
