#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import os
import torch
import cv2
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

# 默认模型路径
DEFAULT_MODEL_PATH = os.path.join(str(Path(__file__).resolve().parent.parent), 'testflowers.pt')


class FlowerVision:
    """
    花卉识别类 - 提供完整的花卉识别功能接口
    """
    
    def __init__(self, device=None, verbose=False, weights_path=None):
        """
        初始化花卉识别模型，自动加载模型文件
        
        Args:
            device (str, optional): 运行设备，如'cuda'或'cpu'，默认为自动检测
            verbose (bool): 是否打印详细信息，默认为False
            weights_path (str, optional): 模型权重文件路径，默认为None（使用默认模型）
        """
        # 使用提供的权重路径，如果未提供则使用默认路径
        self.weights_path = weights_path if weights_path else DEFAULT_MODEL_PATH
        self.device = torch.device(device) if device else torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.verbose = verbose
        self.model = None  # 模型对象
        self.names = None  # 类别名称字典
        
        # 初始化时自动加载模型
        self.load_model()
    
    def load_model(self, weights_path=None):
        """
        加载花卉识别模型
        
        Args:
            weights_path (str, optional): 模型权重文件路径，如果提供则覆盖初始化时的设置
            
        Returns:
            bool: 加载成功返回True
            
        Raises:
            RuntimeError: 加载模型失败时抛出
            FileNotFoundError: 权重文件不存在时抛出
        """
        # 如果提供了新的权重路径，则使用它，否则使用初始化时设置的路径
        current_weights_path = weights_path if weights_path else self.weights_path
        # 更新实例的权重路径
        self.weights_path = current_weights_path
        
        # 获取绝对路径
        abs_weights_path = os.path.abspath(current_weights_path)
        if not os.path.exists(abs_weights_path):
            raise FileNotFoundError(f"模型权重文件不存在: {abs_weights_path}")
            
        if self.verbose and abs_weights_path == DEFAULT_MODEL_PATH:
            print(f"使用默认模型: {abs_weights_path}")
        elif self.verbose:
            print(f"使用自定义模型: {abs_weights_path}")
            
        weights_path = abs_weights_path
        
        try:
            from models.experimental import attempt_load
            
            if self.verbose:
                print(f"正在加载模型 '{weights_path}' 到设备: {self.device}")
            
            self.model = attempt_load(weights_path, device=self.device)
            
            if hasattr(self.model, 'module'):
                self.names = self.model.module.names
            elif hasattr(self.model, 'names'):
                self.names = self.model.names
            else:
                self.names = {i: f'花卉_{i}' for i in range(10)}
            
            self.weights_path = weights_path
            
            if self.verbose:
                print(f"模型已加载: {weights_path}")
                print(f"花卉类别: {self.names}")
                print(f"运行设备: {self.device}")
                print(f"模型加载成功，支持 {len(self.names)} 种类别")
            
            return True
            
        except FileNotFoundError:
            raise
        except Exception as e:
            if self.verbose:
                print(f"加载模型失败: {str(e)}")
            raise RuntimeError(f"加载模型失败: {str(e)}")
    
    def recognize(self, img_path, conf_thres=0.25, iou_thres=0.45):
        """
        识别图片中的花卉
        
        Args:
            img_path (str): 图片文件路径
            conf_thres (float): 置信度阈值，默认0.25
            iou_thres (float): IoU阈值，默认0.45
            
        Returns:
            tuple: (识别结果列表, 原始图片)
                 识别结果列表中每个元素是包含以下键的字典：
                 - 'flower': 花卉类别名称
                 - 'confidence': 置信度值（0-1之间）
                 - 'bbox': 边界框坐标 [x1, y1, x2, y2]
        """
        if self.model is None:
            raise RuntimeError("请先调用load_model()加载模型")
        
        img_path = os.path.abspath(img_path)
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"图片文件不存在: {img_path}")
        
        try:
            from utils.general import non_max_suppression, scale_boxes
            from utils.augmentations import letterbox
            
            img0 = cv2.imread(img_path)
            if img0 is None:
                raise ValueError(f"无法读取图片: {img_path}")
            
            img = letterbox(img0, new_shape=640)[0]
            img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB
            img = np.ascontiguousarray(img)
            
            img = torch.from_numpy(img).to(self.device)
            img = img.float() / 255.0  # 归一化到0-1范围
            if img.ndimension() == 3:
                img = img.unsqueeze(0)  # 添加批次维度
            
            with torch.no_grad():
                pred = self.model(img)[0]
            
            pred = non_max_suppression(pred, conf_thres=conf_thres, iou_thres=iou_thres)
            
            results = []
            if pred[0] is not None and len(pred[0]) > 0:
                pred[0][:, :4] = scale_boxes(img.shape[2:], pred[0][:, :4], img0.shape).round()
                
                for *xyxy, conf, cls in pred[0]:
                    flower_name = self.names[int(cls)]
                    results.append({
                        'flower': flower_name,
                        'confidence': float(conf),
                        'bbox': [int(x) for x in xyxy]  # 转换为整数坐标
                    })
            
            return results, img0
            
        except Exception as e:
            raise RuntimeError(f"识别过程出错: {str(e)}")

    def visualize_results(self, img, results, thickness=10, font_scale=1.5):
        """
        在图片上可视化识别结果
        
        Args:
            img: 原始图片（BGR格式）
            results: 识别结果列表
            thickness: 边界框线条粗细
            font_scale: 字体大小
            
        Returns:
            可视化后的图片
        """
        # 复制图片以避免修改原始图片
        vis_img = img.copy()
        
        # 为不同类别生成不同颜色
        colors = {}
        for i, result in enumerate(results):
            cls_name = result['flower']
            if cls_name not in colors:
                # 使用类别名的哈希值生成颜色
                color_idx = hash(cls_name) % 10
                colors[cls_name] = [(color_idx * 30) % 255, (color_idx * 70) % 255, (color_idx * 130) % 255]
            
            color = colors[cls_name]
            bbox = result['bbox']
            confidence = result['confidence']
            
            # 绘制边界框
            cv2.rectangle(vis_img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, thickness)
            
            # 绘制类别和置信度
            label = f'{cls_name} {confidence:.2f}'
            (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
            
            # 绘制标签背景
            cv2.rectangle(
                vis_img, 
                (bbox[0], bbox[1] - label_height - 5), 
                (bbox[0] + label_width, bbox[1]), 
                color, 
                -1
            )
            
            # 绘制标签文本
            cv2.putText(
                vis_img, 
                label, 
                (bbox[0], bbox[1] - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                font_scale, 
                (255, 255, 255), 
                1
            )
        
        return vis_img
