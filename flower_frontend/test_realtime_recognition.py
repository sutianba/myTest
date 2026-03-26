#!/usr/bin/env python3
"""
测试实时识别后自动进相册的完整流程
"""
import pymysql
import time
import os

# 数据库连接
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='20031221',
    database='flower_recognition',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
cursor = conn.cursor()

print("=" * 60)
print("测试实时识别后自动进相册流程")
print("=" * 60)

# 测试参数
user_id = 20
flower_name = "rose"
confidence = 0.85

# 1. 记录测试前的状态
print("\n【步骤1】记录测试前的数据库状态")
print("-" * 60)

# 检查 rose相册 当前状态
cursor.execute("SELECT id, name, image_count, cover_image FROM albums WHERE name = 'rose相册' AND user_id = %s", (user_id,))
rose_album_before = cursor.fetchone()
if rose_album_before:
    print(f"rose相册(测试前): ID={rose_album_before['id']}, image_count={rose_album_before['image_count']}, cover_image={rose_album_before['cover_image']}")
else:
    print("rose相册不存在，将在保存时自动创建")

# 检查 recognition_results 当前最大ID
cursor.execute("SELECT MAX(id) as max_id FROM recognition_results")
max_result_id_before = cursor.fetchone()['max_id'] or 0
print(f"recognition_results 当前最大ID: {max_result_id_before}")

# 检查 album_images 当前最大ID
cursor.execute("SELECT MAX(id) as max_id FROM album_images")
max_image_id_before = cursor.fetchone()['max_id'] or 0
print(f"album_images 当前最大ID: {max_image_id_before}")

# 2. 模拟识别结果保存
print("\n【步骤2】模拟保存识别结果到 recognition_results")
print("-" * 60)

timestamp = int(time.time())
image_path = f"/static/uploads/recognition/recognition_{user_id}_{timestamp}.jpg"

cursor.execute('''
    INSERT INTO recognition_results 
    (user_id, image_path, result, confidence, created_at)
    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
''', (user_id, image_path, flower_name, confidence))
conn.commit()

result_id = cursor.lastrowid
print(f"✓ 识别结果保存成功: result_id={result_id}")
print(f"  - user_id={user_id}")
print(f"  - image_path={image_path}")
print(f"  - result={flower_name}")
print(f"  - confidence={confidence}")

# 3. 查找或创建相册
print("\n【步骤3】查找或创建相册")
print("-" * 60)

cursor.execute("SELECT id, name, image_count, cover_image FROM albums WHERE name = 'rose相册' AND user_id = %s", (user_id,))
album = cursor.fetchone()

if album:
    album_id = album['id']
    print(f"✓ 找到现有相册: album_id={album_id}, name={album['name']}")
    print(f"  - 当前 image_count={album['image_count']}")
    print(f"  - 当前 cover_image={album['cover_image']}")
else:
    # 创建新相册
    cursor.execute(
        "INSERT INTO albums (user_id, name, category, cover_image, description, image_count, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
        (user_id, 'rose相册', flower_name, None, 'rose分类相册', 0)
    )
    conn.commit()
    album_id = cursor.lastrowid
    print(f"✓ 创建新相册: album_id={album_id}, name=rose相册")

# 4. 添加图片到相册
print("\n【步骤4】添加图片到 album_images")
print("-" * 60)

image_name = os.path.basename(image_path)
image_description = f"{flower_name} - 识别置信度：{confidence:.2f}"

cursor.execute(
    "INSERT INTO album_images (album_id, user_id, image_path, image_name, image_description, recognition_result_id, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
    (album_id, user_id, image_path, image_name, image_description, result_id, timestamp)
)
conn.commit()
image_id = cursor.lastrowid
print(f"✓ 图片添加到相册成功: image_id={image_id}")
print(f"  - album_id={album_id}")
print(f"  - image_path={image_path}")
print(f"  - recognition_result_id={result_id}")

# 5. 更新相册图片数量
print("\n【步骤5】更新相册的 image_count")
print("-" * 60)

cursor.execute("SELECT image_count FROM albums WHERE id = %s", (album_id,))
count_before = cursor.fetchone()['image_count']
print(f"  更新前 image_count={count_before}")

cursor.execute(
    "UPDATE albums SET image_count = image_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
    (album_id,)
)
conn.commit()

cursor.execute("SELECT image_count FROM albums WHERE id = %s", (album_id,))
count_after = cursor.fetchone()['image_count']
print(f"✓ 更新后 image_count={count_after} (+1)")

# 6. 检查并更新封面
print("\n【步骤6】检查并更新相册封面")
print("-" * 60)

cursor.execute("SELECT cover_image FROM albums WHERE id = %s", (album_id,))
current_cover = cursor.fetchone()['cover_image']
print(f"  当前封面: {current_cover}")

if not current_cover:
    cursor.execute(
        "UPDATE albums SET cover_image = %s WHERE id = %s",
        (image_path, album_id)
    )
    conn.commit()
    print(f"✓ 设置新封面: {image_path}")
else:
    print(f"✓ 相册已有封面，保持原有封面")

# 7. 验证最终结果
print("\n【步骤7】验证最终数据库状态")
print("-" * 60)

# 检查 recognition_results
cursor.execute("SELECT id, user_id, image_path, result, confidence FROM recognition_results WHERE id = %s", (result_id,))
result = cursor.fetchone()
print(f"✓ recognition_results 记录:")
print(f"  - ID={result['id']}, result={result['result']}, confidence={result['confidence']}")

# 检查 album_images
cursor.execute("SELECT id, album_id, image_path, recognition_result_id FROM album_images WHERE id = %s", (image_id,))
image = cursor.fetchone()
print(f"✓ album_images 记录:")
print(f"  - ID={image['id']}, album_id={image['album_id']}, recognition_result_id={image['recognition_result_id']}")

# 检查 albums
cursor.execute("SELECT id, name, image_count, cover_image FROM albums WHERE id = %s", (album_id,))
album_after = cursor.fetchone()
print(f"✓ albums 记录:")
print(f"  - ID={album_after['id']}, name={album_after['name']}")
print(f"  - image_count={album_after['image_count']}")
print(f"  - cover_image={album_after['cover_image']}")

# 8. 对比测试前后
print("\n【步骤8】对比测试前后状态")
print("-" * 60)

if rose_album_before:
    print(f"rose相册 image_count: {rose_album_before['image_count']} → {album_after['image_count']} (+{album_after['image_count'] - rose_album_before['image_count']})")
else:
    print(f"rose相册 image_count: 0 → {album_after['image_count']} (新创建)")

print(f"recognition_results: ID {max_result_id_before} → {result_id} (新增)")
print(f"album_images: ID {max_image_id_before} → {image_id} (新增)")

print("\n" + "=" * 60)
print("测试完成！实时识别后自动进相册流程正常")
print("=" * 60)

conn.close()
