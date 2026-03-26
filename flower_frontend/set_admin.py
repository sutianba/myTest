#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
将指定用户设置为管理员
"""
import sys
sys.path.insert(0, '.')

from db import db_manager, get_user_by_username, update_user_role

def set_user_as_admin(username):
    """将指定用户设置为管理员"""
    try:
        # 查找用户
        user = get_user_by_username(username)
        if not user:
            print(f"用户 '{username}' 不存在")
            return False
        
        user_id = user['id']
        current_role = user.get('role', 'user')
        
        print(f"找到用户: {username} (ID: {user_id})")
        print(f"当前角色: {current_role}")
        
        # 更新 users 表的 role 字段
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 更新 users 表的 role 字段
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (user_id,)
            )
            
            # 2. 更新 user_roles 表
            # 先删除现有的角色关联
            cursor.execute(
                "DELETE FROM user_roles WHERE user_id = %s",
                (user_id,)
            )
            
            # 获取 admin 角色的 ID
            cursor.execute(
                "SELECT id FROM roles WHERE name = 'admin'"
            )
            role_record = cursor.fetchone()
            
            if role_record:
                role_id = role_record['id']
                # 插入新的角色关联
                cursor.execute(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                    (user_id, role_id)
                )
                print(f"已更新 user_roles 表，角色ID: {role_id}")
            else:
                print("警告: 未找到 'admin' 角色")
            
            conn.commit()
            print(f"✅ 用户 '{username}' 已成功设置为管理员")
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 更新失败: {str(e)}")
            return False
        finally:
            conn.close()
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

if __name__ == '__main__':
    # 设置用户名为 sxf 的用户为管理员
    username = "sxf"
    print(f"正在将用户 '{username}' 设置为管理员...")
    print("-" * 50)
    set_user_as_admin(username)
