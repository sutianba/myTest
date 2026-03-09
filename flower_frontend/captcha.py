#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""图形验证码模块"""

import random
import string
import io
import base64
from PIL import Image, ImageDraw, ImageFont, ImageFilter


class CaptchaGenerator:
    """验证码生成器"""
    
    def __init__(self):
        # 验证码字符集（去除容易混淆的字符）
        self.chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'
        self.font_paths = [
            '/System/Library/Fonts/PingFang.ttc',  # macOS
            '/System/Library/Fonts/Helvetica.ttc',  # macOS
            '/Library/Fonts/Arial Unicode.ttf',  # macOS
            'C:/Windows/Fonts/msyh.ttc',  # Windows
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
        ]
        self.font_size = 36
        self.image_width = 160
        self.image_height = 60
        self.code_length = 4
        
    def get_font(self):
        """获取字体"""
        for font_path in self.font_paths:
            try:
                return ImageFont.truetype(font_path, self.font_size)
            except:
                continue
        # 如果找不到字体，使用默认字体
        return ImageFont.load_default()
    
    def generate_captcha(self):
        """生成验证码图片和文本"""
        # 生成随机验证码
        captcha_text = ''.join(random.choices(self.chars, k=self.code_length))
        
        # 创建图片
        image = Image.new('RGB', (self.image_width, self.image_height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # 获取字体
        font = self.get_font()
        
        # 绘制验证码文字
        for i, char in enumerate(captcha_text):
            x = 20 + i * 30 + random.randint(-5, 5)
            y = random.randint(5, 15)
            
            # 随机颜色
            color = (
                random.randint(0, 100),
                random.randint(0, 100),
                random.randint(0, 100)
            )
            
            # 随机旋转角度
            angle = random.randint(-20, 20)
            
            # 创建文字图片
            char_image = Image.new('RGBA', (30, 40), (255, 255, 255, 0))
            char_draw = ImageDraw.Draw(char_image)
            char_draw.text((0, 0), char, font=font, fill=color)
            char_image = char_image.rotate(angle, expand=True)
            
            # 粘贴到主图片
            image.paste(char_image, (x, y), char_image)
        
        # 添加干扰线
        for _ in range(random.randint(3, 5)):
            x1 = random.randint(0, self.image_width)
            y1 = random.randint(0, self.image_height)
            x2 = random.randint(0, self.image_width)
            y2 = random.randint(0, self.image_height)
            
            draw.line(
                [(x1, y1), (x2, y2)],
                fill=(
                    random.randint(0, 150),
                    random.randint(0, 150),
                    random.randint(0, 150)
                ),
                width=random.randint(1, 2)
            )
        
        # 添加干扰点
        for _ in range(random.randint(50, 100)):
            draw.point(
                (random.randint(0, self.image_width), random.randint(0, self.image_height)),
                fill=(
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255)
                )
            )
        
        # 添加背景噪点
        for x in range(self.image_width):
            for y in range(self.image_height):
                if random.random() > 0.95:
                    draw.point((x, y), fill=(
                        random.randint(0, 255),
                        random.randint(0, 255),
                        random.randint(0, 255)
                    ))
        
        # 模糊处理
        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        return captcha_text, image
    
    def generate_captcha_base64(self):
        """生成Base64编码的验证码图片"""
        captcha_text, image = self.generate_captcha()
        
        # 转换为Base64
        buffered = io.BytesIO()
        image.save(buffered, format='PNG')
        base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return captcha_text, base64_str


# 全局验证码生成器
captcha_generator = CaptchaGenerator()

# 验证码存储（内存缓存）
captcha_storage = {}


def generate_captcha():
    """生成验证码"""
    captcha_text, base64_str = captcha_generator.generate_captcha_base64()
    
    # 生成唯一ID
    captcha_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    # 存储验证码（5分钟有效）
    captcha_storage[captcha_id] = {
        'text': captcha_text,
        'created_at': __import__('time').time(),
        'expires_at': __import__('time').time() + 300,
        'used': False
    }
    
    return captcha_id, base64_str


def verify_captcha(captcha_id, captcha_text):
    """验证验证码"""
    if not captcha_id or captcha_id not in captcha_storage:
        return False, '验证码无效'
    
    captcha_data = captcha_storage[captcha_id]
    
    # 检查是否过期
    if __import__('time').time() > captcha_data['expires_at']:
        del captcha_storage[captcha_id]
        return False, '验证码已过期'
    
    # 检查是否已使用
    if captcha_data['used']:
        return False, '验证码已使用'
    
    # 检查验证码
    if captcha_text.upper() != captcha_data['text'].upper():
        return False, '验证码错误'
    
    # 标记为已使用
    captcha_data['used'] = True
    
    return True, '验证成功'


def clear_captcha(captcha_id):
    """清除验证码"""
    if captcha_id in captcha_storage:
        del captcha_storage[captcha_id]
