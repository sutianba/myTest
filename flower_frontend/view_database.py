#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import sqlite3

# 连接到数据库
conn = sqlite3.connect('flower_recognition.db')
cursor = conn.cursor()

# 查询所有表
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()

print("=" * 50)
print("数据库文件位置: flower_recognition.db")
print("=" * 50)
print("\n数据库中的表:")
print("-" * 50)
for table in tables:
    print(f"  - {table[0]}")

# 查看每个表的结构和数据
for table in tables:
    table_name = table[0]
    print(f"\n{'=' * 50}")
    print(f"表名: {table_name}")
    print(f"{'=' * 50}")
    
    # 查看表结构
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = cursor.fetchall()
    print("\n表结构:")
    print("-" * 50)
    for col in columns:
        print(f"  {col[1]:20} {col[2]:15}")
    
    # 查看表数据
    cursor.execute(f'SELECT * FROM {table_name}')
    rows = cursor.fetchall()
    print(f"\n数据行数: {len(rows)}")
    if rows:
        print("\n数据内容:")
        print("-" * 50)
        for i, row in enumerate(rows, 1):
            print(f"  行 {i}: {row}")
    else:
        print("\n  (空表)")

conn.close()
print("\n" + "=" * 50)
print("数据库查询完成")
print("=" * 50)