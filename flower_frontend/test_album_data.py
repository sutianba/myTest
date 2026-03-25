"""
测试相册数据验证脚本
验证相册创建、图片保存、数据关联等功能
"""

import sqlite3
import os

# 数据库路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'flower_recognition.db')

def test_album_data():
    """测试相册数据"""
    print("=" * 60)
    print("相册数据验证")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. 检查相册数据
        print("\n1. 检查相册数据...")
        cursor.execute("SELECT * FROM albums ORDER BY created_at DESC")
        albums = cursor.fetchall()
        
        if albums:
            print(f"   找到 {len(albums)} 个相册:")
            for album in albums:
                print(f"   - {album['name']} (ID: {album['id']})")
                print(f"     分类: {album['category']}, 图片数: {album['image_count']}")
        else:
            print("   暂无相册数据")
        
        # 2. 检查相册图片数据
        print("\n2. 检查相册图片数据...")
        cursor.execute("SELECT * FROM album_images ORDER BY created_at DESC")
        images = cursor.fetchall()
        
        if images:
            print(f"   找到 {len(images)} 张图片:")
            for img in images[:3]:  # 只显示前3张
                print(f"   - {img['image_name']} (ID: {img['id']})")
                print(f"     相册ID: {img['album_id']}, 路径: {img['image_path']}")
                print(f"     描述: {img['image_description']}")
            if len(images) > 3:
                print(f"   ... 还有 {len(images) - 3} 张图片")
        else:
            print("   暂无相册图片数据")
        
        # 3. 检查识别结果数据
        print("\n3. 检查识别结果数据...")
        cursor.execute("SELECT * FROM recognition_results ORDER BY created_at DESC")
        results = cursor.fetchall()
        
        if results:
            print(f"   找到 {len(results)} 条识别结果:")
            for result in results[:3]:  # 只显示前3条
                print(f"   - ID: {result['id']}, 结果: {result['result']}")
                print(f"     置信度: {result['confidence']}, 路径: {result['image_path']}")
            if len(results) > 3:
                print(f"   ... 还有 {len(results) - 3} 条结果")
        else:
            print("   暂无识别结果数据")
        
        # 4. 检查图片文件是否存在
        print("\n4. 检查图片文件是否存在...")
        cursor.execute("SELECT image_path FROM album_images")
        image_paths = cursor.fetchall()
        
        for img_path in image_paths[:3]:  # 只检查前3张
            full_path = os.path.join(BASE_DIR, img_path['image_path'].lstrip('/'))
            if os.path.exists(full_path):
                print(f"   ✓ 图片存在: {img_path['image_path']}")
            else:
                print(f"   ✗ 图片不存在: {img_path['image_path']}")
        if len(image_paths) > 3:
            print(f"   ... 还有 {len(image_paths) - 3} 张图片")
        
        print("\n" + "=" * 60)
        print("数据验证完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n验证过程中发生错误：{e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    test_album_data()
