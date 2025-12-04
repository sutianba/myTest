#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import os
import torch
import cv2
import numpy as np
from pathlib import Path
import pathlib
import platform
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QTextEdit, QLabel, QMessageBox, QSplitter,
    QFrame, QSizePolicy, QDoubleSpinBox, QGroupBox, QGridLayout, QComboBox
)
from PyQt5.QtGui import QPixmap, QFont, QTextOption, QImage
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal

# 添加当前目录的父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入EXIF信息读取类
from tool.exif_test import ExifReader

# Windows系统下的路径兼容性处理
if platform.system() == 'Windows':
    _original_pure_posix_path = pathlib.PurePosixPath
    _original_posix_path = pathlib.PosixPath
    pathlib.PurePosixPath = pathlib.PureWindowsPath
    pathlib.PosixPath = pathlib.WindowsPath

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).resolve().parent.parent))


# 导入花卉识别AI模块的核心功能
class FlowerVisionAI:
    """
    花卉识别AI类 - 提供完整的花卉识别功能接口
    """
    
    def __init__(self, weights_path=None, device=None, verbose=False):
        """
        初始化花卉识别模型
        
        Args:
            weights_path (str, optional): 模型权重文件路径，不提供则不自动加载
            device (str, optional): 运行设备，如'cuda'或'cpu'，默认为自动检测
            verbose (bool): 是否打印详细信息，默认为False
        """
        self.weights_path = weights_path
        self.device = torch.device(device) if device else torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.verbose = verbose
        self.model = None  # 模型对象
        self.names = None  # 类别名称字典
    
    def load_model(self, weights_path=None):
        """
        加载花卉识别模型
        
        Args:
            weights_path (str, optional): 模型权重文件路径，默认为初始化时的路径
            
        Returns:
            bool: 加载成功返回True
            
        Raises:
            RuntimeError: 加载模型失败时抛出
            FileNotFoundError: 权重文件不存在时抛出
        """
        if weights_path is None:
            weights_path = self.weights_path
        
        weights_path = os.path.abspath(weights_path)
        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"模型权重文件不存在: {weights_path}")
        
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

    def visualize_results(self, img, results, thickness=2, font_scale=0.5):
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
            detector: FlowerVisionAI实例
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
            self.reader.process_image(self.file_path)
            # 发送完成信号
            self.finished.emit()
        except Exception as e:
            # 发送错误信号
            self.error.emit(str(e))


class FlowerVisionGUI(QMainWindow):
    """
    花卉识别GUI主窗口类
    """
    
    def __init__(self):
        """初始化花卉识别GUI"""
        super().__init__()
        self.init_ui()
        self.flower_detector = FlowerVisionAI(verbose=True)
        self.exif_reader = ExifReader()
        self.setup_console_redirect()   # 重定向标准输出到文本框
        self.recognition_thread = None  # 初始化识别线程为None
        self.model_load_thread = None   # 初始化模型加载线程为None
        self.exif_thread = None         # 初始化EXIF处理线程为None
        self.current_image_path = None  # 当前处理的图片路径
        self.current_image = None       # 当前处理的图片数据
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle('花卉识别AI系统')
        self.setGeometry(100, 100, 1000, 700)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建顶部按钮和参数设置区域
        top_layout = QVBoxLayout()
        
        # 创建按钮行
        buttons_layout = QHBoxLayout()
        
        # 创建选择模型按钮
        self.select_model_button = QPushButton('选择模型文件')
        self.select_model_button.setMinimumHeight(35)
        self.select_model_button.clicked.connect(self.select_model)
        
        # 创建选择图片按钮
        self.select_image_button = QPushButton('选择图片文件')
        self.select_image_button.setMinimumHeight(35)
        self.select_image_button.clicked.connect(self.select_image)
        self.select_image_button.setEnabled(False)  # 初始禁用，等待模型加载
        
        # 创建识别按钮
        self.recognize_button = QPushButton('开始识别')
        self.recognize_button.setMinimumHeight(35)
        self.recognize_button.clicked.connect(self.start_recognition)
        self.recognize_button.setEnabled(False)  # 初始禁用，等待模型和图片都准备好
        
        # 创建清空按钮
        self.clear_button = QPushButton('清空')
        self.clear_button.setMinimumHeight(35)
        self.clear_button.clicked.connect(self.clear_all)
        
        # 添加按钮到按钮布局
        buttons_layout.addWidget(self.select_model_button)
        buttons_layout.addWidget(self.select_image_button)
        buttons_layout.addWidget(self.recognize_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addStretch()
        
        # 创建参数设置组
        params_group = QGroupBox("识别参数设置")
        params_layout = QGridLayout()
        
        # 设备选择
        device_label = QLabel("运行设备:")
        self.device_combo = QComboBox()
        # 检测可用设备
        self.device_combo.addItem("CPU")
        if torch.cuda.is_available():
            self.device_combo.addItem("CUDA (GPU)")
        
        # 置信度阈值
        conf_label = QLabel("置信度阈值:")
        self.conf_spin = QDoubleSpinBox()
        self.conf_spin.setRange(0.1, 1.0)
        self.conf_spin.setValue(0.25)
        self.conf_spin.setSingleStep(0.05)
        
        # IoU阈值
        iou_label = QLabel("IoU阈值:")
        self.iou_spin = QDoubleSpinBox()
        self.iou_spin.setRange(0.1, 1.0)
        self.iou_spin.setValue(0.45)
        self.iou_spin.setSingleStep(0.05)
        
        # 添加参数控件到布局
        params_layout.addWidget(device_label, 0, 0)
        params_layout.addWidget(self.device_combo, 0, 1)
        params_layout.addWidget(conf_label, 0, 2)
        params_layout.addWidget(self.conf_spin, 0, 3)
        params_layout.addWidget(iou_label, 0, 4)
        params_layout.addWidget(self.iou_spin, 0, 5)
        params_layout.setColumnStretch(6, 1)  # 添加伸缩项
        
        # 设置参数组布局
        params_group.setLayout(params_layout)
        
        # 添加按钮行和参数组到顶部布局
        top_layout.addLayout(buttons_layout)
        top_layout.addWidget(params_group)
        
        # 添加顶部布局到主布局
        main_layout.addLayout(top_layout)
        
        # 创建分割器，用于分割图片预览和识别结果
        splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧图片预览区域
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        
        self.image_label = QLabel('图片预览')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFrameStyle(QLabel.Panel | QLabel.Sunken)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        left_layout.addWidget(self.image_label)
        
        # 创建右侧区域
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        
        # 创建垂直分割器，用于分割EXIF信息和识别结果
        right_splitter = QSplitter(Qt.Vertical)
        
        # 创建EXIF信息显示区域
        exif_frame = QFrame()
        exif_layout = QVBoxLayout(exif_frame)
        
        # 创建EXIF信息标题
        exif_label = QLabel('EXIF信息')
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        exif_label.setFont(font)
        
        # 创建文本编辑框用于显示EXIF信息
        self.exif_text = QTextEdit()
        self.exif_text.setReadOnly(True)
        self.exif_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.exif_text.setWordWrapMode(QTextOption.WordWrap)
        
        # 添加到EXIF布局
        exif_layout.addWidget(exif_label)
        exif_layout.addWidget(self.exif_text)
        
        # 创建识别结果显示区域
        results_frame = QFrame()
        results_layout = QVBoxLayout(results_frame)
        
        # 创建识别结果标题
        results_label = QLabel('识别结果')
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        results_label.setFont(font)
        
        # 创建文本编辑框用于显示识别结果
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.results_text.setWordWrapMode(QTextOption.WordWrap)
        
        # 添加加载状态指示器
        self.loading_label = QLabel('处理中...')
        self.loading_label.setVisible(False)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet('color: #0066cc; font-style: italic;')
        
        # 添加到识别结果布局
        results_layout.addWidget(results_label)
        results_layout.addWidget(self.loading_label)
        results_layout.addWidget(self.results_text)
        
        # 添加EXIF和识别结果框架到右侧分割器
        right_splitter.addWidget(exif_frame)
        right_splitter.addWidget(results_frame)
        
        # 设置右侧分割器的初始大小比例
        right_splitter.setSizes([300, 400])
        
        # 添加右侧分割器到右侧布局
        right_layout.addWidget(right_splitter)
        
        # 添加左右框架到分割器
        splitter.addWidget(left_frame)
        splitter.addWidget(right_frame)
        
        # 设置分割器的初始大小比例
        splitter.setSizes([500, 500])
        
        # 添加分割器到主布局
        main_layout.addWidget(splitter, 1)
    
    def setup_console_redirect(self):
        """重定向控制台输出到文本编辑框"""
        # 保存原始的stdout
        self.original_stdout = sys.stdout
        
        # 使用信号槽机制来安全地在主线程中更新UI
        from PyQt5.QtCore import pyqtSignal, QObject
        
        class ConsoleSignals(QObject):
            exif_text = pyqtSignal(str)
            results_text = pyqtSignal(str)
        
        self.console_signals = ConsoleSignals()
        self.console_signals.exif_text.connect(self.add_text_to_exif)
        self.console_signals.results_text.connect(self.add_text_to_results)
        
        # 创建一个自定义的输出流类，用于EXIF信息
        class ExifConsoleRedirect:
            def __init__(self, signals):
                self.signals = signals
            
            def write(self, text):
                # 发送信号到主线程更新UI
                self.signals.exif_text.emit(text)
            
            def flush(self):
                pass
        
        # 创建一个自定义的输出流类，用于识别结果
        class ResultsConsoleRedirect:
            def __init__(self, signals):
                self.signals = signals
            
            def write(self, text):
                # 发送信号到主线程更新UI
                self.signals.results_text.emit(text)
            
            def flush(self):
                pass
        
        # 初始重定向到EXIF文本编辑框
        self.exif_redirect = ExifConsoleRedirect(self.console_signals)
        self.results_redirect = ResultsConsoleRedirect(self.console_signals)
        sys.stdout = self.exif_redirect
        
    def add_text_to_exif(self, text):
        """在主线程中添加文本到EXIF文本框"""
        self.exif_text.insertPlainText(text)
        self.exif_text.moveCursor(self.exif_text.textCursor().End)
    
    def add_text_to_results(self, text):
        """在主线程中添加文本到结果文本框"""
        self.results_text.insertPlainText(text)
        self.results_text.moveCursor(self.results_text.textCursor().End)
        
    def redirect_to_results(self):
        """重定向输出到识别结果文本框"""
        sys.stdout = self.results_redirect
        
    def redirect_to_exif(self):
        """重定向输出到EXIF信息文本框"""
        sys.stdout = self.exif_redirect
    
    def select_model(self):
        """选择模型文件并加载"""
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            '选择模型文件', 
            '', 
            '模型文件 (*.pt)'
        )
        
        if file_path:
            # 检查是否有正在运行的线程，如果有则停止
            if self.model_load_thread and self.model_load_thread.isRunning():
                self.model_load_thread.terminate()
                self.model_load_thread.wait()
            
            # 清空之前的内容
            self.results_text.clear()
            
            # 显示加载状态
            self.loading_label.setVisible(True)
            self.select_model_button.setEnabled(False)
            
            # 更新设备设置
            device = 'cuda:0' if self.device_combo.currentText() == 'CUDA (GPU)' else 'cpu'
            self.flower_detector.device = torch.device(device)
            
            # 重定向输出到结果文本框，确保模型加载信息输出到识别结果区域
            self.redirect_to_results()
            
            # 创建并启动模型加载线程
            self.model_load_thread = ModelLoadThread(self.flower_detector, file_path)
            self.model_load_thread.finished.connect(self.on_model_loaded)
            self.model_load_thread.error.connect(self.on_process_error)
            self.model_load_thread.progress.connect(self.update_progress)
            self.model_load_thread.start()
    
    def on_model_loaded(self, success):
        """模型加载完成后的回调"""
        # 隐藏加载状态
        self.loading_label.setVisible(False)
        self.select_model_button.setEnabled(True)
        
        # 重定向输出到结果文本框
        self.redirect_to_results()
        
        if success:
            print(f"✅ 模型加载成功！")
            print(f"支持 {len(self.flower_detector.names)} 种花卉类别")
            self.select_image_button.setEnabled(True)
            
            # 如果已有图片，可以启用识别按钮
            if self.current_image_path:
                self.recognize_button.setEnabled(True)
        else:
            QMessageBox.critical(self, '错误', '模型加载失败')
    
    def select_image(self):
        """选择图片文件并显示预览和EXIF信息"""
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            '选择图片文件', 
            '', 
            '图片文件 (*.jpg *.jpeg *.png *.tiff *.bmp)'
        )
        
        if file_path:
            self.current_image_path = file_path
            # 显示图片预览
            self.display_image_preview(file_path)
            
            # 启用识别按钮
            if self.flower_detector.model is not None:
                self.recognize_button.setEnabled(True)
            
            # 清空之前的EXIF内容
            self.exif_text.clear()
            
            # 显示加载状态
            self.loading_label.setVisible(True)
            self.select_image_button.setEnabled(False)
            
            # 重定向输出到EXIF文本框
            self.redirect_to_exif()
            
            # 创建并启动EXIF处理线程
            if self.exif_thread and self.exif_thread.isRunning():
                self.exif_thread.terminate()
                self.exif_thread.wait()
            
            self.exif_thread = ExifProcessThread(self.exif_reader, file_path)
            self.exif_thread.finished.connect(self.on_exif_process_finished)
            self.exif_thread.error.connect(self.on_exif_process_error)
            self.exif_thread.start()
    
    def on_exif_process_finished(self):
        """EXIF处理完成后的回调"""
        # 隐藏加载状态
        self.loading_label.setVisible(False)
        self.select_image_button.setEnabled(True)
        
        # 输出已选择图片信息到EXIF文本框
        print(f"\n已选择图片: {os.path.basename(self.current_image_path)}")
    
    def on_exif_process_error(self, error_message):
        """EXIF处理错误时的回调
        
        Args:
            error_message: 错误信息
        """
        # 隐藏加载状态
        self.loading_label.setVisible(False)
        self.select_image_button.setEnabled(True)
        
        # 显示错误信息
        print(f"处理EXIF信息时出错: {error_message}")
    
    def start_recognition(self):
        """开始识别图片中的花卉"""
        if not self.current_image_path or not self.flower_detector.model:
            QMessageBox.warning(self, '警告', '请先选择模型和图片')
            return
        
        # 检查是否有正在运行的线程，如果有则停止
        if self.recognition_thread and self.recognition_thread.isRunning():
            self.recognition_thread.terminate()
            self.recognition_thread.wait()
        
        # 清空之前的识别结果内容
        self.results_text.clear()
        
        # 显示加载状态
        self.loading_label.setVisible(True)
        self.recognize_button.setEnabled(False)
        
        # 获取参数
        conf_thres = self.conf_spin.value()
        iou_thres = self.iou_spin.value()
        
        # 重定向输出到结果文本框
        self.redirect_to_results()
        
        # 创建并启动识别线程
        self.recognition_thread = RecognitionThread(
            self.flower_detector, 
            self.current_image_path, 
            conf_thres, 
            iou_thres
        )
        self.recognition_thread.finished.connect(self.on_recognition_finished)
        self.recognition_thread.error.connect(self.on_process_error)
        self.recognition_thread.progress.connect(self.update_progress)
        self.recognition_thread.start()
    
    def update_progress(self, message):
        """更新进度信息"""
        self.loading_label.setText(message)
    
    def on_recognition_finished(self, results, img):
        """识别完成后的回调"""
        # 隐藏加载状态
        self.loading_label.setVisible(False)
        self.recognize_button.setEnabled(True)
        
        # 保存当前图片
        self.current_image = img
        
        # 显示识别结果
        if results:
            print(f"✅ 识别成功！检测到 {len(results)} 个花卉实例:")
            # 按置信度降序排序结果
            results_sorted = sorted(results, key=lambda x: x['confidence'], reverse=True)
            
            for i, result in enumerate(results_sorted, 1):
                flower_name = result['flower']
                confidence = result['confidence']
                bbox = result['bbox']
                
                # 格式化输出
                print(f"  {i}. [{confidence:.2%}] {flower_name}")
                print(f"     位置: x1={bbox[0]}, y1={bbox[1]}, x2={bbox[2]}, y2={bbox[3]}")
                print(f"     尺寸: {bbox[2]-bbox[0]}×{bbox[3]-bbox[1]}")
            
            # 可视化结果并显示
            vis_img = self.flower_detector.visualize_results(img, results)
            self.display_image_with_results(vis_img)
        else:
            print(f"⚠️  未检测到任何花卉")
            # 显示原始图片
            self.display_image_preview(self.current_image_path)
    
    def on_process_error(self, error_message):
        """处理错误时的回调
        
        Args:
            error_message: 错误信息
        """
        # 隐藏加载状态
        self.loading_label.setVisible(False)
        self.select_model_button.setEnabled(True)
        self.recognize_button.setEnabled(True)
        
        # 显示错误信息
        print(f"❌ 错误: {error_message}")
        QMessageBox.critical(self, '错误', f'处理时出错: {error_message}')
    
    def display_image_preview(self, file_path):
        """显示图片预览"""
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            # 缩放图片以适应标签大小
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText('无法加载图片')
            QMessageBox.warning(self, '警告', '无法显示图片预览')
    
    def display_image_with_results(self, cv_img):
        """显示带有识别结果的图片
        
        Args:
            cv_img: OpenCV格式的图片（BGR）
        """
        # 转换OpenCV图片到Qt格式
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # 创建QPixmap并显示
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
    
    def clear_all(self):
        """清空所有内容"""
        # 检查是否有正在运行的线程，如果有则停止
        if self.recognition_thread and self.recognition_thread.isRunning():
            self.recognition_thread.terminate()
            self.recognition_thread.wait()
        
        if self.model_load_thread and self.model_load_thread.isRunning():
            self.model_load_thread.terminate()
            self.model_load_thread.wait()
        
        if self.exif_thread and self.exif_thread.isRunning():
            self.exif_thread.terminate()
            self.exif_thread.wait()
        
        # 清空文本框和图片
        self.results_text.clear()
        self.exif_text.clear()
        self.image_label.clear()
        self.image_label.setText('图片预览')
        
        # 重置状态
        self.loading_label.setVisible(False)
        self.select_model_button.setEnabled(True)
        self.select_image_button.setEnabled(self.flower_detector.model is not None)
        self.recognize_button.setEnabled(False)
        self.current_image_path = None
        self.current_image = None
    
    def resizeEvent(self, event):
        """窗口大小改变时重新调整图片预览大小"""
        if self.image_label.pixmap() is not None:
            scaled_pixmap = self.image_label.pixmap().scaled(
                self.image_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        super().resizeEvent(event)
    
    def closeEvent(self, event):
        """关闭窗口时恢复原始的stdout并停止线程"""
        # 检查是否有正在运行的线程，如果有则停止
        if self.recognition_thread and self.recognition_thread.isRunning():
            self.recognition_thread.terminate()
            self.recognition_thread.wait()
        
        if self.model_load_thread and self.model_load_thread.isRunning():
            self.model_load_thread.terminate()
            self.model_load_thread.wait()
        
        if self.exif_thread and self.exif_thread.isRunning():
            self.exif_thread.terminate()
            self.exif_thread.wait()
        
        sys.stdout = self.original_stdout
        event.accept()


def main():
    """主函数"""
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建并显示主窗口
    window = FlowerVisionGUI()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
