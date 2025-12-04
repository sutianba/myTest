#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
from PyQt5.QtCore import QThread, pyqtSignal


class RecognitionThread(QThread):
    """
    花卉识别处理线程类，用于在后台处理图片识别
    """
    # 信号定义
    finished = pyqtSignal(list, object)  # 处理完成信号，传递识别结果和原始图片
    error = pyqtSignal(str)  # 错误信号
    progress = pyqtSignal(str)  # 进度信号
    
    def __init__(self, detector, file_path, conf_thres=0.25, iou_thres=0.45):
        """初始化处理线程
        
        Args:
            detector: FlowerVision实例
            file_path: 要处理的图片文件路径
            conf_thres: 置信度阈值
            iou_thres: IoU阈值
        """
        super().__init__()
        self.detector = detector
        self.file_path = file_path
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
    
    def run(self):
        """线程运行方法，在后台进行花卉识别"""
        try:
            self.progress.emit("正在进行花卉识别...")
            # 执行识别
            results, img = self.detector.recognize(self.file_path, self.conf_thres, self.iou_thres)
            # 发送完成信号
            self.finished.emit(results, img)
        except Exception as e:
            # 发送错误信号
            self.error.emit(str(e))


class ModelLoadThread(QThread):
    """
    模型加载线程类，用于在后台加载模型
    """
    # 信号定义
    finished = pyqtSignal(bool)  # 加载完成信号
    error = pyqtSignal(str)  # 错误信号
    progress = pyqtSignal(str)  # 进度信号
    
    def __init__(self, detector, weights_path):
        """初始化模型加载线程
        
        Args:
            detector: FlowerVisionAI实例
            weights_path: 模型权重文件路径
        """
        super().__init__()
        self.detector = detector
        self.weights_path = weights_path
    
    def run(self):
        """线程运行方法，在后台加载模型"""
        try:
            self.progress.emit(f"正在加载模型: {os.path.basename(self.weights_path)}...")
            # 加载模型
            success = self.detector.load_model(self.weights_path)
            # 发送完成信号
            self.finished.emit(success)
        except Exception as e:
            # 发送错误信号
            self.error.emit(str(e))


class ExifProcessThread(QThread):
    """
    EXIF处理线程类，用于在后台处理图片EXIF信息提取
    """
    # 信号定义
    finished = pyqtSignal()  # 处理完成信号
    error = pyqtSignal(str)  # 错误信号
    
    def __init__(self, reader, file_path):
        """初始化处理线程
        
        Args:
            reader: ExifReader实例
            file_path: 要处理的图片文件路径
        """
        super().__init__()
        self.reader = reader
        self.file_path = file_path
    
    def run(self):
        """线程运行方法，在后台处理EXIF信息"""
        try:
            # 处理图片EXIF信息
            print(f"正在处理文件: {self.file_path}")
            success = self.reader.process_image(self.file_path)
            if success:
                # 发送完成信号
                self.finished.emit()
            else:
                # 发送错误信号
                self.error.emit(f"无法加载图片的EXIF数据: {self.file_path}")
        except Exception as e:
            # 发送错误信号
            self.error.emit(str(e))


class AddressLookupThread(QThread):
    """
    地址查询线程类，用于在后台通过坐标获取地址信息
    """
    # 信号定义
    finished = pyqtSignal(dict)  # 处理完成信号，传递地址信息（字典类型）
    error = pyqtSignal(str)  # 错误信号
    progress = pyqtSignal(str)  # 进度信号
    
    def __init__(self, geo_service, latitude, longitude):
        """初始化地址查询线程
        
        Args:
            geo_service: 地理服务实例，包含get_address_from_coordinates方法
            latitude: 纬度
            longitude: 经度
        """
        super().__init__()
        self.geo_service = geo_service
        self.latitude = latitude
        self.longitude = longitude
    
    def run(self):
        """线程运行方法，在后台执行地址查询"""
        try:
            self.progress.emit("正在获取地址信息...")
            # 执行地址查询
            address = self.geo_service.get_address_from_coordinates(self.latitude, self.longitude)
            # 保持原始返回格式（应该是字典），只处理None的情况
            if address is None:
                # 返回空字典而不是字符串，以便format_address方法正常处理
                address = {}
            # 发送完成信号
            self.finished.emit(address)
        except Exception as e:
            # 发送错误信号
            self.error.emit(str(e))
