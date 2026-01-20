#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import sqlite3
import json

# 连接到数据库
def add_topic_support():
    try:
        conn = sqlite3.connect('flower_recognition.db')
        cursor = conn.cursor()
        
        print("=" * 50)
        print("添加话题支持功能")
        print("=" * 50)
        
        # 1. 为posts表添加topics字段
        print("\n1. 为posts表添加topics字段...")
        try:
            cursor.execute('ALTER TABLE posts ADD COLUMN topics TEXT')
            print("✓ 成功为posts表添加topics字段")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ posts表已存在topics字段")
            else:
                raise
        
        # 2. 创建topics表来存储所有话题和统计信息
        print("\n2. 创建topics表...")
        try:
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                display_name VARCHAR(100) NOT NULL,
                post_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            print("✓ 成功创建topics表")
        except Exception as e:
            print(f"创建topics表失败: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 3. 更新posts表中的现有记录，将topics字段设置为默认值(空数组)
        print("\n3. 更新现有posts记录的topics字段...")
        try:
            cursor.execute('UPDATE posts SET topics = ? WHERE topics IS NULL', (json.dumps([]),))
            print("✓ 成功更新现有posts记录")
        except Exception as e:
            print(f"更新posts记录失败: {e}")
            import traceback
            traceback.print_exc()
            return
        
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 50)
        print("话题功能数据库结构更新完成！")
        print("=" * 50)
        
        # 查看更新后的表结构
        view_updated_tables()
        
    except Exception as e:
        print(f"更新数据库失败: {e}")
        import traceback
        traceback.print_exc()

# 查看更新后的表结构
def view_updated_tables():
    try:
        conn = sqlite3.connect('flower_recognition.db')
        cursor = conn.cursor()
        
        print("\n更新后的表结构:")
        print("=" * 50)
        
        # 查看posts表结构
        print("\nposts表结构:")
        print("-" * 50)
        cursor.execute('PRAGMA table_info(posts)')
        posts_columns = cursor.fetchall()
        for col in posts_columns:
            print(f"  {col[1]:20} {col[2]:15}")
        
        # 查看topics表结构
        print("\ntopics表结构:")
        print("-" * 50)
        cursor.execute('PRAGMA table_info(topics)')
        topics_columns = cursor.fetchall()
        for col in topics_columns:
            print(f"  {col[1]:20} {col[2]:15}")
        
        conn.close()
        
    except Exception as e:
        print(f"查看表结构失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_topic_support()