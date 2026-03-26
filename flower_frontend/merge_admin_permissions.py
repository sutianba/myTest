#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
合并超级管理员和管理员的权限
让admin也拥有super_admin的所有权限
"""
import sys
sys.path.insert(0, '.')

from db import db_manager

def merge_admin_permissions():
    """合并超级管理员和管理员的权限"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 1. 获取 super_admin 的所有权限
        cursor.execute("SELECT id FROM roles WHERE name = 'super_admin'")
        super_admin = cursor.fetchone()
        
        if not super_admin:
            print("❌ 未找到 super_admin 角色")
            return
        
        super_admin_id = super_admin['id']
        
        # 2. 获取 admin 角色ID
        cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
        admin = cursor.fetchone()
        
        if not admin:
            print("❌ 未找到 admin 角色")
            return
        
        admin_id = admin['id']
        
        # 3. 获取 super_admin 的所有权限ID
        cursor.execute("SELECT permission_id FROM role_permissions WHERE role_id = %s", (super_admin_id,))
        super_admin_perms = [row['permission_id'] for row in cursor.fetchall()]
        
        print(f"超级管理员有 {len(super_admin_perms)} 个权限")
        
        # 4. 获取 admin 已有的权限ID
        cursor.execute("SELECT permission_id FROM role_permissions WHERE role_id = %s", (admin_id,))
        admin_perms = [row['permission_id'] for row in cursor.fetchall()]
        
        print(f"管理员已有 {len(admin_perms)} 个权限")
        
        # 5. 找出 admin 缺少的权限
        missing_perms = set(super_admin_perms) - set(admin_perms)
        
        print(f"需要添加 {len(missing_perms)} 个权限到管理员角色")
        
        # 6. 为 admin 添加缺少的权限
        for perm_id in missing_perms:
            try:
                cursor.execute(
                    "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)",
                    (admin_id, perm_id)
                )
                print(f"  ✅ 添加权限ID: {perm_id}")
            except Exception as e:
                print(f"  ℹ️ 权限已存在: {perm_id}")
        
        conn.commit()
        
        # 7. 验证权限合并结果
        print("\n" + "=" * 60)
        print("权限合并完成，验证结果：")
        print("=" * 60)
        
        cursor.execute('''
            SELECT p.name, p.description 
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = %s
            ORDER BY p.name
        ''', (admin_id,))
        permissions = cursor.fetchall()
        
        print(f"\n管理员(admin)现在拥有 {len(permissions)} 个权限：")
        for perm in permissions:
            print(f"  - {perm['name']}: {perm['description']}")
        
        conn.close()
        print("\n✅ 权限合并完成！管理员和超级管理员现在拥有相同的权限")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == '__main__':
    merge_admin_permissions()
