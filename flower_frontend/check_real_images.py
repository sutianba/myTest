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

print('=== 所有相册及其图片 ===')
cursor.execute('SELECT id, name, cover_image FROM albums ORDER BY id')
albums = cursor.fetchall()

for album in albums:
    album_id = album['id']
    print(f"\n相册: {album['name']} (ID: {album_id})")
    print(f"当前封面: {album['cover_image']}")
    
    # 获取该相册的所有图片
    cursor.execute(
        'SELECT id, image_path, image_name, created_at FROM album_images WHERE album_id = %s ORDER BY created_at',
        (album_id,)
    )
    images = cursor.fetchall()
    
    if images:
        print(f"图片数量: {len(images)}")
        for img in images:
            print(f"  - ID: {img['id']}, Path: {img['image_path']}, Name: {img['image_name']}")
    else:
        print("  无图片")

conn.close()
