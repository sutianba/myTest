#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import sqlite3

def add_role_column():
    """为users表添加role列"""
    try:
        conn = sqlite3.connect('flower_recognition.db')
        cursor = conn.cursor()
        
        print("检查users表结构...")
        cursor.execute('PRAGMA table_info(users)')
        columns = cursor.fetchall()
        
        print("\n当前users表结构:")
        for col in columns:
            print(f"  {col[1]:20} {col[2]:15}")
        
        # 检查是否已有role列
        has_role = any(col[1] == 'role' for col in columns)
        
        if has_role:
            print("\n✓ users表已有role列，无需修改")
        else:
            print("\n正在添加role列...")
            cursor.execute('ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT "user"')
            conn.commit()
            print("✓ 成功添加role列")
            
            # 为现有用户设置默认role
            cursor.execute('UPDATE users SET role = "user" WHERE role IS NULL')
            conn.commit()
            print("✓ 已为现有用户设置默认role")
        
        # 显示更新后的表结构
        print("\n更新后的users表结构:")
        cursor.execute('PRAGMA table_info(users)')
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]:20} {col[2]:15}")
        
        conn.close()
        print("\n" + "=" * 50)
        print("数据库更新完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"更新数据库失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    add_role_column()