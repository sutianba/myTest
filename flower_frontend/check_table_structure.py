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

print('=== album_images 表结构 ===')
cursor.execute('DESCRIBE album_images')
results = cursor.fetchall()
for row in results:
    print(f"{row['Field']}: {row['Type']}")

conn.close()
