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

print('=== 修复 rose相册 封面 ===\n')

# 获取 rose相册 的第一张真实图片
cursor.execute('''
    SELECT id, image_path 
    FROM album_images 
    WHERE album_id = 6 AND image_path NOT LIKE '%test_flower%'
    ORDER BY created_at 
    LIMIT 1
''')
first_image = cursor.fetchone()

if first_image:
    print(f"第一张真实图片: {first_image['image_path']}")
    
    # 更新封面
    cursor.execute(
        'UPDATE albums SET cover_image = %s WHERE id = 6',
        (first_image['image_path'],)
    )
    conn.commit()
    print("封面已更新！")
else:
    print("没有找到真实图片")

# 删除 test_flower.jpg 记录
cursor.execute("DELETE FROM album_images WHERE image_path LIKE '%test_flower%'")
conn.commit()
print(f"删除测试图片记录: {cursor.rowcount} 条")

# 更新图片计数
cursor.execute(
    'UPDATE albums SET image_count = (SELECT COUNT(*) FROM album_images WHERE album_id = 6) WHERE id = 6'
)
conn.commit()

cursor.execute('SELECT image_count, cover_image FROM albums WHERE id = 6')
album = cursor.fetchone()
print(f"\n最终状态: image_count={album['image_count']}, cover_image={album['cover_image']}")

conn.close()
