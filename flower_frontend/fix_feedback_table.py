#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
修复 user_feedback 表结构，添加意见反馈所需字段
"""
import sys
sys.path.insert(0, '.')

from db import db_manager

def fix_feedback_table():
    """修改 user_feedback 表，添加意见反馈所需字段"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 检查现有字段
        cursor.execute("DESCRIBE user_feedback")
        existing_columns = [col['Field'] for col in cursor.fetchall()]
        
        print("现有字段:", existing_columns)
        
        # 需要添加的字段
        columns_to_add = [
            ('title', 'VARCHAR(100)', 'NULL'),
            ('content', 'TEXT', 'NULL'),
            ('feedback_type', 'VARCHAR(50)', 'NULL'),
            ('status', 'VARCHAR(20)', "DEFAULT 'pending'"),
            ('response', 'TEXT', 'NULL'),
            ('responded_at', 'INT', 'NULL'),
        ]
        
        for col_name, col_type, default in columns_to_add:
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE user_feedback ADD COLUMN {col_name} {col_type} {default}")
                    print(f"✅ 添加字段: {col_name}")
                except Exception as e:
                    print(f"⚠️ 添加字段 {col_name} 失败: {str(e)}")
            else:
                print(f"ℹ️ 字段已存在: {col_name}")
        
        # 修改 created_at 字段类型为 INT（如果不是的话）
        cursor.execute("DESCRIBE user_feedback")
        columns_info = {col['Field']: col for col in cursor.fetchall()}
        
        if 'created_at' in columns_info:
            col_type = columns_info['created_at']['Type']
            if 'timestamp' in col_type.lower():
                try:
                    # 添加新的 INT 类型字段，然后迁移数据
                    cursor.execute("ALTER TABLE user_feedback ADD COLUMN created_at_int INT NULL")
                    cursor.execute("UPDATE user_feedback SET created_at_int = UNIX_TIMESTAMP(created_at) WHERE created_at IS NOT NULL")
                    cursor.execute("ALTER TABLE user_feedback DROP COLUMN created_at")
                    cursor.execute("ALTER TABLE user_feedback CHANGE created_at_int created_at INT NULL")
                    print("✅ 修改 created_at 字段类型为 INT")
                except Exception as e:
                    print(f"⚠️ 修改 created_at 字段失败: {str(e)}")
        
        # 添加 updated_at 字段
        if 'updated_at' not in existing_columns:
            try:
                cursor.execute("ALTER TABLE user_feedback ADD COLUMN updated_at INT NULL")
                print("✅ 添加字段: updated_at")
            except Exception as e:
                print(f"⚠️ 添加字段 updated_at 失败: {str(e)}")
        
        conn.commit()
        print("\n✅ 表结构更新完成")
        
        # 再次检查表结构
        print("\n更新后的表结构:")
        print("=" * 60)
        cursor.execute("DESCRIBE user_feedback")
        columns = cursor.fetchall()
        print(f"{'字段名':<20} {'类型':<20} {'允许空':<10} {'默认值'}")
        print("=" * 60)
        for col in columns:
            print(f"{col['Field']:<20} {col['Type']:<20} {col['Null']:<10} {col['Default']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == '__main__':
    fix_feedback_table()
