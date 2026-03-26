#!/usr/bin/env python3
import pymysql
import time
from datetime import datetime

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='20031221',
    database='flower_recognition',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
cursor = conn.cursor()

print('=== 同步真实识别记录到相册 ===\n')

# 获取所有识别结果
cursor.execute('''
    SELECT id, user_id, image_path, result, confidence, created_at 
    FROM recognition_results 
    ORDER BY result, created_at
''')
recognitions = cursor.fetchall()

# 按花卉类型分组
flower_groups = {}
for rec in recognitions:
    flower_name = rec['result']
    if flower_name not in flower_groups:
        flower_groups[flower_name] = []
    flower_groups[flower_name].append(rec)

print(f"发现花卉类型: {list(flower_groups.keys())}\n")

# 为每种花卉创建/获取相册并添加图片
for flower_name, images in flower_groups.items():
    print(f"处理 {flower_name} ({len(images)} 张图片)...")
    
    # 查找或创建相册
    album_name = f"{flower_name}相册"
    cursor.execute(
        'SELECT id, cover_image FROM albums WHERE name = %s AND user_id = %s',
        (album_name, images[0]['user_id'])
    )
    album = cursor.fetchone()
    
    if album:
        album_id = album['id']
        print(f"  找到现有相册 ID: {album_id}")
    else:
        # 创建新相册 - 使用 CURRENT_TIMESTAMP
        cursor.execute(
            'INSERT INTO albums (user_id, name, category, cover_image, description, image_count, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
            (images[0]['user_id'], album_name, flower_name, None, f'{flower_name}分类相册', 0)
        )
        album_id = cursor.lastrowid
        print(f"  创建新相册 ID: {album_id}")
    
    # 添加图片到相册（跳过已存在的）
    added_count = 0
    first_image_path = None
    for img in images:
        # 检查是否已存在
        cursor.execute(
            'SELECT id FROM album_images WHERE album_id = %s AND image_path = %s',
            (album_id, img['image_path'])
        )
        if cursor.fetchone():
            continue
        
        # 添加图片 - 使用当前时间戳 (INT)
        image_description = f"{flower_name} - 识别置信度：{img['confidence']:.2f}"
        now = int(time.time())
        cursor.execute(
            'INSERT INTO album_images (album_id, user_id, image_path, image_name, image_description, recognition_result_id, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (album_id, img['user_id'], img['image_path'], img['image_path'].split('/')[-1], image_description, img['id'], now)
        )
        added_count += 1
        
        # 记录第一张图片路径
        if first_image_path is None:
            first_image_path = img['image_path']
    
    # 如果有新增图片且相册没有封面，设置封面
    if added_count > 0 and first_image_path:
        cursor.execute(
            'SELECT cover_image FROM albums WHERE id = %s',
            (album_id,)
        )
        current_cover = cursor.fetchone()
        if not current_cover or not current_cover['cover_image']:
            cursor.execute(
                'UPDATE albums SET cover_image = %s WHERE id = %s',
                (first_image_path, album_id)
            )
            print(f"  设置封面: {first_image_path}")
    
    # 更新图片计数
    cursor.execute(
        'UPDATE albums SET image_count = (SELECT COUNT(*) FROM album_images WHERE album_id = %s) WHERE id = %s',
        (album_id, album_id)
    )
    
    print(f"  新增 {added_count} 张图片\n")

# 删除测试图相关的记录
print('清理测试数据...')
cursor.execute("DELETE FROM album_images WHERE image_path LIKE '%test_flower%'")
cursor.execute("UPDATE albums SET cover_image = NULL, image_count = 0 WHERE cover_image LIKE '%test_flower%'")

cursor.execute("DELETE FROM albums WHERE image_count = 0 AND cover_image IS NULL")

cursor.execute("DELETE FROM albums WHERE name = 'rose相册' AND id = 2")

conn.commit()
conn.close()

print('\n同步完成！')
