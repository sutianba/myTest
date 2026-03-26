#!/usr/bin/env python3
import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='20031221',
    database='flower_recognition',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
cursor = conn.cursor()

print('=== recognition_results 表（真实识别记录）===')
cursor.execute('SELECT id, user_id, image_path, result, confidence, created_at FROM recognition_results ORDER BY id DESC LIMIT 10')
results = cursor.fetchall()

if results:
    for row in results:
        print(f"ID: {row['id']}, User: {row['user_id']}, Result: {row['result']}, Confidence: {row['confidence']}")
        print(f"  Path: {row['image_path']}")
        print(f"  Created: {row['created_at']}")
        print('---')
else:
    print('无数据')

conn.close()
