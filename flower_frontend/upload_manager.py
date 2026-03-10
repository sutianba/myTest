#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
安全的图片上传管理模块
包含文件大小限制、类型校验、MIME校验、恶意文件拦截等功能
"""

import os
import secrets
import hashlib
import mimetypes
from PIL import Image
import io
from datetime import datetime
from typing import Tuple, Optional, Dict

# 配置参数
MAX_FILE_SIZE = 5 * 1024 * 1024  # 最大文件大小：5MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/webp'
}

# 安全文件名映射
SECURE_FILENAME_MAP = {
    ' ': '_',
    '<': '',
    '>': '',
    ':': '',
    '"': '',
    '/': '',
    '\\': '',
    '|': '',
    '?': '',
    '*': '',
    '\0': '',
    '\n': '',
    '\r': '',
    '\t': ''
}


def is_safe_filename(filename: str) -> bool:
    """
    检查文件名是否安全
    防止路径遍历攻击
    """
    # 检查是否包含路径遍历字符
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # 检查是否包含危险字符
    for char in SECURE_FILENAME_MAP.keys():
        if char in filename:
            return False
    
    return True


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名（小写）
    """
    return os.path.splitext(filename)[1].lower()


def generate_secure_filename(original_filename: str) -> str:
    """
    生成安全的文件名
    防止路径遍历和文件名覆盖
    """
    # 检查文件名是否安全
    if not is_safe_filename(original_filename):
        raise ValueError("文件名不安全")
    
    # 获取扩展名
    ext = get_file_extension(original_filename)
    
    # 生成安全的文件名：时间戳 + 随机字符串 + 扩展名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_str = secrets.token_hex(8)
    secure_name = f"{timestamp}_{random_str}{ext}"
    
    return secure_name


def check_file_size(file_content: bytes, max_size: int = MAX_FILE_SIZE) -> bool:
    """
    检查文件大小
    """
    return len(file_content) <= max_size


def check_file_extension(filename: str, allowed_extensions: set = ALLOWED_EXTENSIONS) -> bool:
    """
    检查文件扩展名是否在白名单中
    """
    ext = get_file_extension(filename)
    return ext in allowed_extensions


def check_mime_type(file_content: bytes, allowed_mime_types: set = ALLOWED_MIME_TYPES) -> Tuple[bool, Optional[str]]:
    """
    检查MIME类型
    使用多种方法进行校验
    """
    # 方法1：使用mimetypes
    try:
        mime_type, _ = mimetypes.guess_type('dummy' + os.path.splitext('test')[1])
    except:
        mime_type = None
    
    # 方法2：使用PIL检查是否为图片
    try:
        image = Image.open(io.BytesIO(file_content))
        mime_type = f"image/{image.format.lower()}"
        image.close()
    except:
        return False, None
    
    # 方法3：检查文件头（Magic Number）
    if len(file_content) >= 4:
        # JPEG: FF D8 FF
        if file_content[0:3] == b'\xff\xd8\xff':
            mime_type = 'image/jpeg'
        # PNG: 89 50 4E 47
        elif file_content[0:4] == b'\x89PNG':
            mime_type = 'image/png'
        # GIF: 47 49 46 38
        elif file_content[0:3] == b'GIF':
            mime_type = 'image/gif'
        # BMP: 42 4D
        elif file_content[0:2] == b'BM':
            mime_type = 'image/bmp'
    
    return mime_type in allowed_mime_types, mime_type


def check_image_integrity(file_content: bytes) -> Tuple[bool, Optional[str]]:
    """
    检查图片完整性
    防止恶意图片文件
    """
    try:
        # 使用PIL打开图片
        image = Image.open(io.BytesIO(file_content))
        
        # 检查图片尺寸
        width, height = image.size
        if width > 10000 or height > 10000:
            image.close()
            return False, "图片尺寸过大"
        
        # 检查图片像素数量
        if width * height > 100000000:  # 1亿像素
            image.close()
            return False, "图片像素过多"
        
        # 检查图片格式
        if image.format not in ['JPEG', 'PNG', 'GIF', 'BMP', 'WEBP']:
            image.close()
            return False, f"不支持的图片格式: {image.format}"
        
        image.close()
        return True, None
        
    except Exception as e:
        return False, f"图片格式错误: {str(e)}"


def check_for_malicious_content(file_content: bytes) -> Tuple[bool, Optional[str]]:
    """
    检查恶意内容
    防止上传恶意文件
    """
    # 检查是否包含PHP代码
    malicious_patterns = [
        b'<?php',
        b'<?',
        b'<script',
        b'javascript:',
        b'onerror=',
        b'onload=',
        b'eval(',
        b'exec(',
        b'system(',
        b'passthru(',
        b'shell_exec(',
        b'assert(',
        b'base64_decode(',
        b'gzinflate(',
        b'eval(',
    ]
    
    for pattern in malicious_patterns:
        if pattern.lower() in file_content.lower():
            return False, "发现恶意代码"
    
    # 检查文件头
    if len(file_content) >= 4:
        # 检查是否为有效的图片文件头
        valid_headers = [
            b'\xff\xd8\xff',  # JPEG
            b'\x89PNG',       # PNG
            b'GIF',           # GIF
            b'BM',             # BMP
            b'RIFF',          # WebP
        ]
        
        is_valid = False
        for header in valid_headers:
            if file_content.startswith(header):
                is_valid = True
                break
        
        if not is_valid:
            return False, "文件头无效"
    
    return True, None


def compress_image(file_content: bytes, max_size: int = 1024 * 1024) -> Tuple[bytes, bool]:
    """
    压缩图片
    返回压缩后的图片内容和是否需要压缩
    """
    try:
        image = Image.open(io.BytesIO(file_content))
        
        # 如果图片已经很小，不需要压缩
        if len(file_content) <= max_size:
            image.close()
            return file_content, False
        
        # 转换为RGB模式（去除透明通道）
        if image.mode in ['RGBA', 'P']:
            image = image.convert('RGB')
        
        # 压缩图片
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        compressed_content = output.getvalue()
        image.close()
        
        # 如果压缩后仍然很大，进一步压缩
        while len(compressed_content) > max_size and image:
            output = io.BytesIO()
            image = Image.open(io.BytesIO(file_content))
            if image.mode in ['RGBA', 'P']:
                image = image.convert('RGB')
            image.save(output, format='JPEG', quality=70, optimize=True)
            compressed_content = output.getvalue()
            image.close()
        
        return compressed_content, True
        
    except Exception as e:
        print(f"压缩图片失败: {e}")
        return file_content, False


def generate_thumbnail(file_content: bytes, size: Tuple[int, int] = (200, 200)) -> Optional[bytes]:
    """
    生成缩略图
    """
    try:
        image = Image.open(io.BytesIO(file_content))
        
        # 转换为RGB模式
        if image.mode in ['RGBA', 'P']:
            image = image.convert('RGB')
        
        # 生成缩略图
        image.thumbnail(size, Image.LANCZOS)
        
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85)
        thumbnail_content = output.getvalue()
        image.close()
        
        return thumbnail_content
        
    except Exception as e:
        print(f"生成缩略图失败: {e}")
        return None


def calculate_file_hash(file_content: bytes) -> str:
    """
    计算文件哈希值
    用于检测重复文件
    """
    return hashlib.sha256(file_content).hexdigest()


def get_file_info(file_content: bytes) -> Dict:
    """
    获取文件信息
    """
    info = {
        'size': len(file_content),
        'hash': calculate_file_hash(file_content),
        'mime_type': None,
        'is_image': False,
        'dimensions': None
    }
    
    try:
        image = Image.open(io.BytesIO(file_content))
        info['mime_type'] = f"image/{image.format.lower()}"
        info['is_image'] = True
        info['dimensions'] = image.size
        image.close()
    except:
        pass
    
    return info


def validate_upload(file_content: bytes, filename: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    验证上传文件
    返回: (是否有效, 文件信息, 错误信息)
    """
    # 1. 检查文件大小
    if not check_file_size(file_content):
        return False, None, f"文件大小超过限制（最大{MAX_FILE_SIZE // (1024*1024)}MB）"
    
    # 2. 检查文件扩展名
    if not check_file_extension(filename):
        return False, None, f"不支持的文件类型。允许的类型: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # 3. 检查MIME类型
    mime_valid, mime_type = check_mime_type(file_content)
    if not mime_valid:
        return False, None, f"MIME类型验证失败"
    
    # 4. 检查图片完整性
    integrity_valid, integrity_error = check_image_integrity(file_content)
    if not integrity_valid:
        return False, None, integrity_error
    
    # 5. 检查恶意内容
    malicious_valid, malicious_error = check_for_malicious_content(file_content)
    if not malicious_valid:
        return False, None, malicious_error
    
    # 6. 获取文件信息
    file_info = get_file_info(file_content)
    
    return True, file_info, None


def save_upload_file(file_content: bytes, upload_dir: str, original_filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    保存上传文件
    返回: (是否成功, 文件路径, 错误信息)
    """
    try:
        # 生成安全的文件名
        secure_filename = generate_secure_filename(original_filename)
        
        # 确保上传目录存在
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # 保存文件
        filepath = os.path.join(upload_dir, secure_filename)
        
        # 压缩图片
        compressed_content, is_compressed = compress_image(file_content)
        
        # 保存压缩后的文件
        with open(filepath, 'wb') as f:
            f.write(compressed_content)
        
        # 生成缩略图
        thumbnail_content = generate_thumbnail(file_content)
        if thumbnail_content:
            thumbnail_path = filepath + '.thumb.jpg'
            with open(thumbnail_path, 'wb') as f:
                f.write(thumbnail_content)
        
        return True, filepath, None
        
    except Exception as e:
        print(f"保存上传文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None, f"保存文件失败: {str(e)}"


def cleanup_failed_upload(filepath: str):
    """
    清理上传失败的文件
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # 清理可能生成的缩略图
        if os.path.exists(filepath + '.thumb.jpg'):
            os.remove(filepath + '.thumb.jpg')
            
    except Exception as e:
        print(f"清理上传失败的文件失败: {e}")


def get_upload_dir(base_dir: str) -> str:
    """
    获取上传目录
    使用隔离的上传目录
    """
    upload_dir = os.path.join(base_dir, 'uploads')
    
    # 创建上传目录
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    return upload_dir
