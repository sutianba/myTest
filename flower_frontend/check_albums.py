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

print('=== albums 表 ===')
cursor.execute('SELECT id, name, category, image_count, cover_image FROM albums ORDER BY id DESC')
results = cursor.fetchall()
if results:
    for row in results:
        print(f"ID: {row['id']}, Name: {row['name']}, Category: {row['category']}, Count: {row['image_count']}, Cover: {row['cover_image']}")
else:
    print('无数据')

print('\n=== album_images 表 ===')
cursor.execute('SELECT id, album_id, image_path, image_name FROM album_images ORDER BY id DESC')
results = cursor.fetchall()
if results:
    for row in results:
        print(f"ID: {row['id']}, Album: {row['album_id']}, Path: {row['image_path']}, Name: {row['image_name']}")
else:
    print('无数据')

conn.close()
