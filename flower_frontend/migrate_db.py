"""
数据库迁移脚本
用于更新现有的 SQLite 数据库，添加 recognition_results 表缺失的字段
"""

import sqlite3
import os

# 数据库路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'flower_recognition.db')

def migrate_database():
    """迁移数据库，添加缺失的字段"""
    print(f"正在迁移数据库：{DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查 recognition_results 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recognition_results'")
        if not cursor.fetchone():
            print("recognition_results 表不存在，跳过迁移")
            return
        
        # 获取现有列
        cursor.execute("PRAGMA table_info(recognition_results)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print(f"现有列：{existing_columns}")
        
        # 需要添加的列
        columns_to_add = [
            ('shoot_time', 'TEXT'),
            ('shoot_year', 'INTEGER'),
            ('shoot_month', 'INTEGER'),
            ('shoot_season', 'TEXT'),
            ('latitude', 'REAL'),
            ('longitude', 'REAL'),
            ('location_text', 'TEXT'),
            ('region_label', 'TEXT'),
            ('final_category', 'TEXT'),
            ('deleted_at', 'INTEGER')
        ]
        
        # 添加缺失的列
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                print(f"添加列：{column_name} {column_type}")
                cursor.execute(f"ALTER TABLE recognition_results ADD COLUMN {column_name} {column_type}")
            else:
                print(f"列已存在：{column_name}")
        
        conn.commit()
        print("数据库迁移完成！")
        
    except Exception as e:
        print(f"迁移失败：{e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
