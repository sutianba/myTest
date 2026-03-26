#!/usr/bin/env python3
import pymysql
import time

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='20031221',
    database='flower_recognition',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
cursor = conn.cursor()

print('=== 修复 rose相册 ===\n')

# 获取所有 rose 识别结果
cursor.execute('''
    SELECT id, user_id, image_path, result, confidence, created_at 
    FROM recognition_results 
    WHERE result = 'rose'
    ORDER BY created_at
''')
rose_images = cursor.fetchall()

if rose_images:
    print(f"找到 {len(rose_images)} 张 rose 图片")
    
    # 创建 rose相册
    user_id = rose_images[0]['user_id']
    cursor.execute(
        'INSERT INTO albums (user_id, name, category, cover_image, description, image_count, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
        (user_id, 'rose相册', 'rose', None, 'rose分类相册', 0)
    )
    album_id = cursor.lastrowid
    print(f"创建 rose相册 ID: {album_id}")
    
    # 添加图片
    first_image_path = None
    for img in rose_images:
        image_description = f"rose - 识别置信度：{img['confidence']:.2f}"
        now = int(time.time())
        cursor.execute(
            'INSERT INTO album_images (album_id, user_id, image_path, image_name, image_description, recognition_result_id, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (album_id, img['user_id'], img['image_path'], img['image_path'].split('/')[-1], image_description, img['id'], now)
        )
        if first_image_path is None:
            first_image_path = img['image_path']
    
    # 设置封面
    if first_image_path:
        cursor.execute(
            'UPDATE albums SET cover_image = %s, image_count = %s WHERE id = %s',
            (first_image_path, len(rose_images), album_id)
        )
        print(f"设置封面: {first_image_path}")
    
    conn.commit()
    print(f"\nrose相册修复完成！共 {len(rose_images)} 张图片")
else:
    print("没有找到 rose 图片")

conn.close()
