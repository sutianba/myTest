#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

# 创建测试图片目录
uploads_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'recognition')
os.makedirs(uploads_dir, exist_ok=True)

# 创建一张简单的测试图片
img = Image.new('RGB', (400, 300), color='lightblue')
draw = ImageDraw.Draw(img)

# 添加文字
try:
    font = ImageFont.truetype("arial.ttf", 30)
except:
    font = ImageFont.load_default()

draw.text((100, 130), "Test Flower", fill='black', font=font)

# 保存图片
test_files = [
    'recognition_20_1774455779.jpg',
    'recognition_20_1774455775.jpg',
    'recognition_20_1774450115.jpg',
    'recognition_20_1774450046.jpg',
    'recognition_20_1774415156.jpg'
]

for filename in test_files:
    filepath = os.path.join(uploads_dir, filename)
    img.save(filepath)
    print(f'创建测试图片: {filepath}')

print('\n测试图片创建完成！')
