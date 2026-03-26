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

print('=== rose相册 查询结果 ===')
cursor.execute("SELECT id, name, image_count, cover_image FROM albums WHERE name = 'rose相册'")
results = cursor.fetchall()
if results:
    for row in results:
        print(f"ID: {row['id']}")
        print(f"Name: {row['name']}")
        print(f"Image Count: {row['image_count']}")
        print(f"Cover Image: {row['cover_image']}")
        print('---')
else:
    print('无数据')

conn.close()
