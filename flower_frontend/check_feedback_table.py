#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
检查 feedback 表结构
"""
import sys
sys.path.insert(0, '.')

from db import db_manager

def check_feedback_table():
    """检查 user_feedback 表结构"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 获取表结构
        cursor.execute("DESCRIBE user_feedback")
        columns = cursor.fetchall()
        
        print("user_feedback 表结构:")
        print("=" * 60)
        print(f"{'字段名':<20} {'类型':<20} {'允许空':<10} {'默认值'}")
        print("=" * 60)
        
        for col in columns:
            print(f"{col['Field']:<20} {col['Type']:<20} {col['Null']:<10} {col['Default']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == '__main__':
    check_feedback_table()
