"""
测试数据库写入流程
直接测试 save_recognition_result 和 add_image_to_album 函数
"""

import sys
import os

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import save_recognition_result, add_image_to_album, create_album, get_user_albums

def test_database_flow():
    """测试数据库写入流程"""
    print("=== 测试数据库写入流程 ===")
    
    try:
        # 测试用户 ID
        user_id = 20
        
        # 1. 测试 save_recognition_result
        print("\n1. 测试 save_recognition_result:")
        image_path = "/static/uploads/recognition/test_flower.jpg"
        result = "rose"
        confidence = 0.85
        
        # 保存识别结果
        result_id = save_recognition_result(
            user_id, 
            image_path, 
            result, 
            confidence,
            shoot_time="2024-01-01 12:00:00",
            shoot_year=2024,
            shoot_month=1,
            shoot_season="冬季",
            latitude=39.9042,
            longitude=116.4074,
            location_text="北京市",
            region_label="华北地区",
            final_category="rose"
        )
        
        print(f"   保存识别结果成功，result_id: {result_id}")
        
        # 2. 测试创建相册
        print("\n2. 测试创建相册:")
        album_name = f"{result}相册"
        category = result
        
        # 检查是否已有相册
        albums = get_user_albums(user_id, result)
        if albums:
            album = albums[0]
            album_id = album['id']
            print(f"   使用现有相册，album_id: {album_id}")
        else:
            # 创建新相册
            album_id = create_album(user_id, album_name, category)
            print(f"   创建新相册成功，album_id: {album_id}")
        
        # 3. 测试 add_image_to_album
        print("\n3. 测试 add_image_to_album:")
        image_name = "test_flower.jpg"
        image_description = f"{result} - 识别置信度：{confidence:.2f}"
        
        # 添加图片到相册
        image_id = add_image_to_album(
            album_id, 
            user_id, 
            image_path, 
            result, 
            confidence, 
            result_id
        )
        
        if image_id:
            print(f"   添加图片到相册成功，image_id: {image_id}")
        else:
            print("   图片已存在于相册中，跳过重复插入")
        
        # 4. 检查数据库记录
        print("\n4. 检查数据库记录:")
        import subprocess
        
        # 检查 recognition_results 表
        print("   a. 检查 recognition_results 表:")
        result = subprocess.run(
            ["mysql", "-u", "root", "-p20031221", "-e", "USE flower_recognition; SELECT id,user_id,image_path,result,confidence FROM recognition_results ORDER BY id DESC LIMIT 3;"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        
        # 检查 album_images 表
        print("   b. 检查 album_images 表:")
        result = subprocess.run(
            ["mysql", "-u", "root", "-p20031221", "-e", "USE flower_recognition; SELECT id,album_id,image_path,recognition_result_id FROM album_images ORDER BY id DESC LIMIT 3;"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_flow()
