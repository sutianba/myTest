#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

# 创建测试图片目录
uploads_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'recognition')
os.makedirs(uploads_dir, exist_ok=True)

# 创建一张简单的测试图片
img = Image.new('RGB', (400, 300), color='pink')
draw = ImageDraw.Draw(img)

# 添加文字
try:
    font = ImageFont.truetype("arial.ttf", 30)
except:
    font = ImageFont.load_default()

draw.text((120, 130), "Rose Flower", fill='darkred', font=font)

# 保存图片
filepath = os.path.join(uploads_dir, 'test_flower.jpg')
img.save(filepath)
print(f'创建测试图片: {filepath}')

print('\n测试图片创建完成！')
