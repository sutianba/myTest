import requests
import json
import time
import base64
import os

# 测试性能的图片路径
TEST_IMAGE_PATH = "test_flower.jpg"  # 请确保有测试图片

# API地址
API_URL = "http://127.0.0.1:5000/api/detect"

# 读取测试图片并转换为base64
with open(TEST_IMAGE_PATH, "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")
    image_data = f"data:image/jpeg;base64,{image_data}"

# 测试单张图片处理时间
def test_single_image():
    print("=== 测试单张图片处理时间 ===")
    start_time = time.time()
    
    data = {"image": image_data}
    response = requests.post(API_URL, json=data)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"请求成功: {result['success']}")
        print(f"识别结果: {result.get('results', {}).get('detections', [])}")
    else:
        print(f"请求失败: {response.status_code}")
    
    print(f"单张图片处理时间: {processing_time:.2f}秒")
    print("=" * 50)
    return processing_time

# 测试多张图片处理时间
def test_multiple_images(image_count=3):
    print(f"=== 测试{image_count}张图片处理时间 ===")
    start_time = time.time()
    
    data = {"images": [image_data] * image_count}
    response = requests.post(API_URL, json=data)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"请求成功: {result['success']}")
        print(f"处理图片数量: {len(result.get('all_results', []))}")
        for i, img_result in enumerate(result.get('all_results', [])):
            detections = img_result.get('results', {}).get('detections', [])
            print(f"第{i+1}张图片识别结果: {detections}")
    else:
        print(f"请求失败: {response.status_code}")
    
    print(f"{image_count}张图片总处理时间: {processing_time:.2f}秒")
    print(f"平均每张图片处理时间: {processing_time/image_count:.2f}秒")
    print("=" * 50)
    return processing_time

# 主函数
if __name__ == "__main__":
    # 确保有测试图片
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"测试图片不存在: {TEST_IMAGE_PATH}")
        print("请将测试图片命名为test_flower.jpg并放在当前目录下")
        exit(1)
    
    print("开始测试优化后的花卉识别性能...")
    print("=" * 50)
    
    # 测试单张图片
    single_time = test_single_image()
    
    # 测试多张图片
    multiple_time = test_multiple_images(3)
    multiple_time_5 = test_multiple_images(5)
    
    print("性能测试完成！")
    print(f"单张图片处理时间: {single_time:.2f}秒")
    print(f"3张图片总处理时间: {multiple_time:.2f}秒")
    print(f"5张图片总处理时间: {multiple_time_5:.2f}秒")
    print("优化总结:")
    print("1. 已禁用Nominatim网络请求，减少网络延迟")
    print("2. 优化了图片处理流程，避免重复加载和处理")
    print("3. 实现了线程池异步处理，提高多图片处理效率")
