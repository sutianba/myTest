#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标签转换脚本：将labelTxt格式转换为YOLOv5格式

YOLOv5期望的标签格式：
每行一个目标：class_id x_center y_center width height
其中所有坐标都是归一化的（0-1范围），并基于图像尺寸进行调整。
"""

import os
import glob
import argparse
import shutil

# 类别名称映射到ID - 添加小写映射以提高匹配率
CLASS_NAMES = {
    'champaka': 0,
    'chitrak': 1,
    'common lanthana': 2,
    'common-lanthana': 2,  # 添加连字符版本
    'daisy': 3,
    'hibiscus': 4,
    'honeysuckle': 5,
    'indian mallow': 6,
    'indian-mallow': 6,    # 添加连字符版本
    'jatropha': 7,
    'lily': 8,
    'malabar melastome': 9,
    'malabar-melastome': 9,  # 添加连字符版本
    'marigold': 10,
    'orchid': 11,
    'rose': 12,
    'shankupushpam': 13,
    'spider lily': 14,
    'spider-lily': 14,      # 添加连字符版本
    'sunflower': 15
}

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='将labelTxt格式转换为YOLOv5格式')
    # 修改默认路径以匹配Windows环境
    parser.add_argument('--dataset_dir', type=str, 
                       default='s:/yolov5-master/myTest/data/flower_dataset.v15i.yolov5-obb',
                       help='数据集根目录')
    parser.add_argument('--subsets', type=str, default='train,val,test',
                       help='需要处理的子集，逗号分隔')
    parser.add_argument('--label_dir', type=str, default='labelTxt',
                       help='原始标签文件夹名称')
    # 注意：YOLOv5硬编码使用'labels'文件夹，不要修改此参数
    parser.add_argument('--output_dir', type=str, default='labels',
                       help='输出标签文件夹名称（YOLOv5要求为labels）')
    return parser.parse_args()

def get_image_dimensions(image_path):
    """获取图像尺寸
    使用PIL库读取实际图像尺寸，确保坐标归一化正确
    """
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            return img.width, img.height
    except Exception as e:
        print(f"警告：无法读取图像 {image_path} 的尺寸，使用默认640x640。错误：{str(e)}")
        return 640, 640

def convert_label_file(label_file, output_file, image_dir):
    """转换单个标签文件
    根据之前查看的标签格式："144 19.00000000000001 49 19.000000000000007 49 117.00000000000001 144 117.00000000000003 rose 0"
    调整解析逻辑以适应多边形格式的标签
    """
    image_filename = os.path.basename(label_file).replace('.txt', '.jpg')
    image_path = os.path.join(image_dir, image_filename)
    
    # 获取图像尺寸
    img_width, img_height = get_image_dimensions(image_path)
    
    with open(label_file, 'r', encoding='utf-8') as f_in:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # 根据实际labelTxt格式解析：多边形格式 x1 y1 x2 y2 x3 y3 x4 y4 class_name confidence
                parts = line.split()
                if len(parts) < 10:  # 至少需要8个坐标值 + 类别名称 + 置信度
                    print(f"警告：标签格式不正确，跳过行: {line} 在文件 {label_file}")
                    continue
                    
                # 提取前8个值作为坐标
                try:
                    coords = list(map(float, parts[:8]))
                    # 提取类别名称（可能是第9个值）
                    class_name = parts[8].lower()  # 转换为小写以匹配CLASS_NAMES
                except ValueError:
                    print(f"警告：坐标转换失败，跳过行: {line} 在文件 {label_file}")
                    continue
                
                # 获取类别ID
                if class_name not in CLASS_NAMES:
                    print(f"警告：未知类别 '{class_name}' 在文件 {label_file}")
                    continue
                    
                class_id = CLASS_NAMES[class_name]
                
                # 从多边形坐标计算边界框（x1,y1,x2,y2）
                # 提取所有x坐标和y坐标
                x_coords = coords[0::2]  # 偶数索引（0,2,4,6）
                y_coords = coords[1::2]  # 奇数索引（1,3,5,7）
                
                # 计算边界框
                x1 = min(x_coords)
                y1 = min(y_coords)
                x2 = max(x_coords)
                y2 = max(y_coords)
                
                # 计算归一化的中心坐标和宽高
                x_center = (x1 + x2) / 2.0 / img_width
                y_center = (y1 + y2) / 2.0 / img_height
                width = (x2 - x1) / img_width
                height = (y2 - y1) / img_height
                
                # 确保值在0-1范围内
                x_center = max(0, min(1, x_center))
                y_center = max(0, min(1, y_center))
                width = max(0, min(1, width))
                height = max(0, min(1, height))
                
                # 写入YOLO格式
                f_out.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

def convert_labels(args):
    """转换所有标签文件"""
    subsets = args.subsets.split(',')
    
    for subset in subsets:
        subset = subset.strip()
        print(f"处理 {subset} 子集...")
        
        # 构建路径
        label_dir = os.path.join(args.dataset_dir, subset, args.label_dir)
        image_dir = os.path.join(args.dataset_dir, subset, 'images')
        output_dir = os.path.join(args.dataset_dir, subset, args.output_dir)
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取所有标签文件
        label_files = glob.glob(os.path.join(label_dir, '*.txt'))
        print(f"找到 {len(label_files)} 个标签文件")
        
        # 转换每个标签文件
        for i, label_file in enumerate(label_files):
            if (i + 1) % 100 == 0 or i == len(label_files) - 1:
                print(f"进度: {i + 1}/{len(label_files)}")
                
            # 构建输出文件名
            base_name = os.path.basename(label_file)
            output_file = os.path.join(output_dir, base_name)
            
            # 转换标签
            convert_label_file(label_file, output_file, image_dir)
    
    print("转换完成！")

if __name__ == '__main__':
    args = parse_arguments()
    convert_labels(args)
    
    # 提示信息
    print("\n注意：")
    print("1. 此脚本是一个基础版本，请根据实际的labelTxt格式调整解析逻辑")
    print("2. 请确保脚本能够正确读取图像尺寸（当前假设为640x640）")
    print("3. YOLOv5硬编码要求标签文件必须放在'labels'文件夹中（与images同级）")
    print("4. 脚本已将输出目录设置为'labels'，确保生成的标签文件位于正确位置")
    print("5. 执行脚本后，请运行: python train.py --img 640 --batch 16 --epochs 300 --data ./data/flower_dataset.v15i.yolov5-obb/data.yaml --weights yolov5s.pt")
