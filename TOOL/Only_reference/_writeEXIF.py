#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF信息写入工具

功能：为指定路径的照片写入自定义EXIF信息
依赖：piexif库（可通过pip install piexif安装）

使用方法：
1. 作为模块导入使用
   from _writeEXIF import write_exif
   write_exif('photo.jpg', {'Make': 'Canon', 'Model': 'EOS R5', 'DateTimeOriginal': '2023:10:01 14:30:00'})

2. 直接运行使用
   修改代码中的配置区域（第103-117行），设置图片路径和要写入的EXIF信息，然后运行程序：
   python _writeEXIF.py
"""

import os
import sys
import piexif
from PIL import Image


def write_exif(image_path, exif_data):
    """
    为照片写入EXIF信息
    
    Args:
        image_path (str): 照片文件路径
        exif_data (dict): 要写入的EXIF信息字典，格式为{标签名: 值}
        
    Returns:
        bool: 写入成功返回True，失败返回False
    """
    if not os.path.exists(image_path):
        print(f"错误：文件 {image_path} 不存在")
        return False
    
    try:
        # 打开图片
        img = Image.open(image_path)
        
        # 获取现有EXIF数据，如果没有则创建空字典
        try:
            exif_dict = piexif.load(img.info['exif'])
        except (KeyError, TypeError):
            exif_dict = {'0th': {}, 'Exif': {}, 'GPS': {}, '1st': {}, 'thumbnail': None}
        
        # EXIF标签映射表（常用标签）
        exif_tags = {
            # 0th IFD组
            'Make': piexif.ImageIFD.Make,
            'Model': piexif.ImageIFD.Model,
            'Software': piexif.ImageIFD.Software,
            'DateTime': piexif.ImageIFD.DateTime,
            'Artist': piexif.ImageIFD.Artist,
            'Copyright': piexif.ImageIFD.Copyright,
            
            # Exif IFD组
            'DateTimeOriginal': piexif.ExifIFD.DateTimeOriginal,
            'DateTimeDigitized': piexif.ExifIFD.DateTimeDigitized,
            'ExposureTime': piexif.ExifIFD.ExposureTime,
            'FNumber': piexif.ExifIFD.FNumber,
            'ISOSpeedRatings': piexif.ExifIFD.ISOSpeedRatings,
            'FocalLength': piexif.ExifIFD.FocalLength,
            'ExposureProgram': piexif.ExifIFD.ExposureProgram,
            'MeteringMode': piexif.ExifIFD.MeteringMode,
            'Flash': piexif.ExifIFD.Flash,
            'FocalLengthIn35mmFilm': piexif.ExifIFD.FocalLengthIn35mmFilm,
        }
        
        # 处理用户输入的EXIF数据
        for tag_name, tag_value in exif_data.items():
            if tag_name in exif_tags:
                tag_id = exif_tags[tag_name]
                
                # 将字符串转换为字节类型（EXIF标准要求）
                if isinstance(tag_value, str):
                    tag_value = tag_value.encode('utf-8')
                
                # 根据标签类型设置合适的组
                if tag_id in piexif.ImageIFD.__dict__.values():
                    exif_dict['0th'][tag_id] = tag_value
                elif tag_id in piexif.ExifIFD.__dict__.values():
                    exif_dict['Exif'][tag_id] = tag_value
                elif tag_id in piexif.GPSIFD.__dict__.values():
                    exif_dict['GPS'][tag_id] = tag_value
            else:
                print(f"警告：未知的EXIF标签 '{tag_name}'，将被忽略")
        
        # 转换为EXIF字节
        exif_bytes = piexif.dump(exif_dict)
        
        # 保存图片，保留原始格式
        img.save(image_path, exif=exif_bytes)
        print(f"成功为 {image_path} 写入EXIF信息")
        return True
        
    except Exception as e:
        print(f"错误：写入EXIF信息失败 - {str(e)}")
        return False


def main():
    """主函数 - 直接在代码中配置参数"""
    # ====================== 配置区域 ======================
    # 请在这里修改图片路径
    image_path = r"S:\BOSS_Project\myTest\TOOL\Only_reference\test.jpg"  # 替换为您的照片路径
    
    # 请在这里修改要写入的EXIF信息
    exif_data = {
        'Make': 'Canon',           # 相机制造商
        'Model': 'EOS R5',         # 相机型号
        'Software': 'Adobe Photoshop CC 2023',  # 使用的软件
        'DateTimeOriginal': '2023:10:01 14:30:00',  # 原始拍摄日期时间
        'Artist': '张三',          # 作者
        'Copyright': '© 2023 张三'  # 版权信息
        # 可以根据需要添加更多EXIF标签
    }
    # ====================== 配置区域结束 ======================
    
    if not exif_data:
        print("错误：请至少指定一个EXIF标签和值")
        return
    
    write_exif(image_path, exif_data)


if __name__ == '__main__':
    main()