#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF信息读取工具

功能：检测指定路径照片的EXIF信息，并以JSON格式打印出来
依赖：piexif库和pillow库（可通过pip install piexif pillow安装）

使用方法：
1. 作为模块导入使用
   from _readEXIF import read_exif
   exif_data = read_exif('photo.jpg')
   print(json.dumps(exif_data, indent=2, ensure_ascii=False))

2. 直接运行使用
   修改代码中的配置区域（第198-204行），设置图片路径和输出格式，然后运行程序：
   python _readEXIF.py
"""

import os
import sys
import json
import piexif
from PIL import Image


def convert_exif_dict(exif_dict):
    """
    将piexif返回的EXIF字典转换为更易读的格式
    
    Args:
        exif_dict (dict): piexif.load()返回的EXIF字典
        
    Returns:
        dict: 转换后的易读格式EXIF字典
    """
    # 标签名称映射表
    tag_names = {
        # 0th IFD组
        piexif.ImageIFD.Make: 'Make',
        piexif.ImageIFD.Model: 'Model',
        piexif.ImageIFD.Software: 'Software',
        piexif.ImageIFD.DateTime: 'DateTime',
        piexif.ImageIFD.Artist: 'Artist',
        piexif.ImageIFD.Copyright: 'Copyright',
        piexif.ImageIFD.Orientation: 'Orientation',
        
        # Exif IFD组
        piexif.ExifIFD.DateTimeOriginal: 'DateTimeOriginal',
        piexif.ExifIFD.DateTimeDigitized: 'DateTimeDigitized',
        piexif.ExifIFD.ExposureTime: 'ExposureTime',
        piexif.ExifIFD.FNumber: 'FNumber',
        piexif.ExifIFD.ISOSpeedRatings: 'ISOSpeedRatings',
        piexif.ExifIFD.FocalLength: 'FocalLength',
        piexif.ExifIFD.ExposureProgram: 'ExposureProgram',
        piexif.ExifIFD.MeteringMode: 'MeteringMode',
        piexif.ExifIFD.Flash: 'Flash',
        piexif.ExifIFD.FocalLengthIn35mmFilm: 'FocalLengthIn35mmFilm',
        piexif.ExifIFD.ExposureBiasValue: 'ExposureBiasValue',
        piexif.ExifIFD.WhiteBalance: 'WhiteBalance',
        piexif.ExifIFD.LensMake: 'LensMake',
        piexif.ExifIFD.LensModel: 'LensModel',
        
        # GPS IFD组
        piexif.GPSIFD.GPSLatitudeRef: 'GPSLatitudeRef',
        piexif.GPSIFD.GPSLatitude: 'GPSLatitude',
        piexif.GPSIFD.GPSLongitudeRef: 'GPSLongitudeRef',
        piexif.GPSIFD.GPSLongitude: 'GPSLongitude',
        piexif.GPSIFD.GPSAltitudeRef: 'GPSAltitudeRef',
        piexif.GPSIFD.GPSAltitude: 'GPSAltitude',
        piexif.GPSIFD.GPSTimeStamp: 'GPSTimeStamp',
        piexif.GPSIFD.GPSDateStamp: 'GPSDateStamp',
    }
    
    result = {}
    
    # 处理0th IFD组
    if '0th' in exif_dict and exif_dict['0th']:
        result['0th'] = {}
        for tag_id, value in exif_dict['0th'].items():
            tag_name = tag_names.get(tag_id, f'Tag_{tag_id}')
            # 解码字节类型的值
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8', errors='replace')
                except UnicodeDecodeError:
                    try:
                        value = value.decode('gbk', errors='replace')
                    except UnicodeDecodeError:
                        value = str(value)
            result['0th'][tag_name] = value
    
    # 处理Exif IFD组
    if 'Exif' in exif_dict and exif_dict['Exif']:
        result['Exif'] = {}
        for tag_id, value in exif_dict['Exif'].items():
            tag_name = tag_names.get(tag_id, f'Tag_{tag_id}')
            # 解码字节类型的值
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8', errors='replace')
                except UnicodeDecodeError:
                    try:
                        value = value.decode('gbk', errors='replace')
                    except UnicodeDecodeError:
                        value = str(value)
            # 特殊处理分数类型
            elif isinstance(value, tuple) and len(value) == 2:
                try:
                    # 尝试转换为浮点数
                    value = value[0] / value[1]
                except (ZeroDivisionError, TypeError):
                    pass
            result['Exif'][tag_name] = value
    
    # 处理GPS IFD组
    if 'GPS' in exif_dict and exif_dict['GPS']:
        result['GPS'] = {}
        for tag_id, value in exif_dict['GPS'].items():
            tag_name = tag_names.get(tag_id, f'Tag_{tag_id}')
            # 解码字节类型的值
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8', errors='replace')
                except UnicodeDecodeError:
                    value = str(value)
            # 处理GPS坐标（分数元组转换为度分秒格式）
            elif tag_name in ['GPSLatitude', 'GPSLongitude'] and isinstance(value, tuple):
                try:
                    degrees = value[0][0] / value[0][1]
                    minutes = value[1][0] / value[1][1]
                    seconds = value[2][0] / value[2][1]
                    value = f"{degrees:.6f}° {minutes:.6f}' {seconds:.6f}\""
                except (IndexError, ZeroDivisionError, TypeError):
                    pass
            # 处理GPS高度
            elif tag_name == 'GPSAltitude' and isinstance(value, tuple):
                try:
                    value = value[0] / value[1]
                except (ZeroDivisionError, TypeError):
                    pass
            result['GPS'][tag_name] = value
    
    # 处理1st IFD组（通常包含缩略图信息）
    if '1st' in exif_dict and exif_dict['1st']:
        result['1st'] = {}
        for tag_id, value in exif_dict['1st'].items():
            tag_name = tag_names.get(tag_id, f'Tag_{tag_id}')
            # 解码字节类型的值
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8', errors='replace')
                except UnicodeDecodeError:
                    value = str(value)
            result['1st'][tag_name] = value
    
    return result


def read_exif(image_path):
    """
    读取照片的EXIF信息
    
    Args:
        image_path (str): 照片文件路径
        
    Returns:
        dict: 包含EXIF信息的字典，如果没有EXIF信息则返回空字典
    """
    if not os.path.exists(image_path):
        print(f"错误：文件 {image_path} 不存在", file=sys.stderr)
        return {}
    
    try:
        # 打开图片
        img = Image.open(image_path)
        
        # 检查是否有EXIF信息
        if 'exif' not in img.info:
            return {}
        
        # 读取EXIF信息
        exif_dict = piexif.load(img.info['exif'])
        
        # 转换为易读格式
        readable_exif = convert_exif_dict(exif_dict)
        
        return readable_exif
        
    except Exception as e:
        print(f"错误：读取EXIF信息失败 - {str(e)}", file=sys.stderr)
        return {}


def main():
    """主函数 - 直接在代码中配置参数"""
    # ====================== 配置区域 ======================
    # 请在这里修改图片路径
    image_path = r"S:\BOSS_Project\myTest\TOOL\Only_reference\test.jpg"  # 替换为您的照片路径
    
    # 是否使用带缩进的格式化输出
    pretty_print = True  # True: 格式化输出, False: 紧凑输出
    # ====================== 配置区域结束 ======================
    
    # 读取EXIF信息
    exif_data = read_exif(image_path)
    
    # 输出JSON格式
    if pretty_print:
        print(json.dumps(exif_data, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(exif_data, ensure_ascii=False))


if __name__ == '__main__':
    main()