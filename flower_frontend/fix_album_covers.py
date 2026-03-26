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

# 获取所有相册
cursor.execute('SELECT id, name, cover_image FROM albums')
albums = cursor.fetchall()

for album in albums:
    album_id = album['id']
    
    # 获取相册的第一张图片
    cursor.execute(
        'SELECT image_path FROM album_images WHERE album_id = %s ORDER BY created_at DESC LIMIT 1',
        (album_id,)
    )
    first_image = cursor.fetchone()
    
    if first_image:
        image_path = first_image['image_path']
        # 更新相册封面
        cursor.execute(
            'UPDATE albums SET cover_image = %s WHERE id = %s',
            (image_path, album_id)
        )
        print(f"更新相册 '{album['name']}' (ID: {album_id}) 封面为: {image_path}")
    else:
        print(f"相册 '{album['name']}' (ID: {album_id}) 没有图片，跳过")

# 更新 image_count
cursor.execute('''
    UPDATE albums a 
    SET image_count = (
        SELECT COUNT(*) FROM album_images ai 
        WHERE ai.album_id = a.id AND ai.deleted_at IS NULL
    )
''')
print("\n更新所有相册的 image_count")

conn.commit()
conn.close()
print("\n修复完成！")
