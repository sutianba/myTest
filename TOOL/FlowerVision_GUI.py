#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import os
import platform
from pathlib import Path
import pathlib
import cv2
import warnings

# 抑制PyQt5和sip相关的所有弃用警告
warnings.filterwarnings("ignore", category=DeprecationWarning, module="PyQt5")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*sipPyTypeDict.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*sip extension module.*")

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QTextEdit, QLabel, QMessageBox, QSplitter,
    QFrame, QSizePolicy, QDoubleSpinBox, QGroupBox, QGridLayout, QComboBox,
    QScrollArea, QListWidget, QListWidgetItem, QDialog
)
from PyQt5.QtGui import QPixmap, QFont, QTextOption, QImage
from PyQt5.QtCore import Qt, QEvent, pyqtSignal, QThread

# 添加当前目录的父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入外部模块（所有类都从外部导入）
from tool.flower_vision import FlowerVision
from tool.flower_vision_threads import RecognitionThread, ExifProcessThread, AddressLookupThread
from tool.exif_test import ExifReader
from tool.Flower_Album import FlowerAlbum, resize_image, ClassificationAlbumDialog, ClassificationAlbum

# Windows系统下的路径兼容性处理
if platform.system() == 'Windows':
    _original_pure_posix_path = pathlib.PurePosixPath
    _original_posix_path = pathlib.PosixPath
    pathlib.PurePosixPath = pathlib.PureWindowsPath
    pathlib.PosixPath = pathlib.WindowsPath

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).resolve().parent.parent))


class FlowerVisionGUI(QMainWindow):
    """
    花卉识别GUI主窗口类
    """
    
    def __init__(self):
        """初始化花卉识别GUI"""
        super().__init__()
        self.init_ui()  # 先初始化UI，确保loading_label已经创建
        try:
            self.flower_detector = FlowerVision(verbose=True)
            self.exif_reader = ExifReader()
            self.setup_console_redirect()   # 重定向标准输出到文本框
            
            # 初始化线程和状态变量
            self.recognition_thread = None  # 初始化识别线程为None
            self.exif_thread = None         # 初始化EXIF处理线程为None
            self.address_thread = None      # 初始化地址查询线程为None
            self.batch_thread = None        # 初始化批量识别线程为None
            
            # 初始化图片相关变量
            self.image_paths = []  # 存储多个图片路径
            self.current_image_index = -1  # 当前处理的图片索引
            self.current_image_path = None  # 当前处理的图片路径
            self.current_image = None       # 当前处理的图片数据
            self.zoom_factor = 1.0          # 缩放因子
            self.original_pixmap = None     # 原始pixmap
            self.current_location_info = None  # 初始化当前位置信息
            self.processed_images = {}  # 存储已处理图片的信息
            
            # 确保loading_label已存在再访问
            if hasattr(self, 'loading_label'):
                self.loading_label.setVisible(False)
        except Exception as e:
            QMessageBox.critical(self, '初始化错误', f'加载默认模型失败: {str(e)}')
            self.close()
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle('花卉识别AI系统')
        self.setGeometry(100, 100, 1000, 700)
        
        # 设置全局样式表
        self.setStyleSheet("""
            /* 主窗口样式 */
            QMainWindow {
                background-color: #e6f3ff;
            }
            
            /* 按钮样式 */
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 15px;
                font-weight: 500;
                border: none;
                margin: 4px;
            }
            
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6ba4f4, stop:1 #4a90e2);
                border: 2px solid #3a7bc8;
                font-size: 14px;
                font-weight: 500;
            }
            
            QPushButton:pressed {
                background-color: #3a7bc8;
            }
            
            QPushButton:disabled {
                background-color: #a9c6e8;
                color: #d0d0d0;
            }
            
            /* 分组框样式 */
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid #b3d1e6;
                border-radius: 10px;
                margin-top: 10px;
                padding: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                background-color: #4a90e2;
                color: white;
                padding: 3px 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            
            /* 框架样式 */
            QFrame {
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid #b3d1e6;
                border-radius: 10px;
            }
            
            /* 滚动区域样式 */
            QScrollArea {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #b3d1e6;
                border-radius: 10px;
                margin: 5px;
            }
            
            /* 文本编辑框样式 */
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #b3d1e6;
                border-radius: 8px;
                padding: 8px;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                font-size: 13px;
            }
            
            /* 标签样式 */
            QLabel {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
            }
            
            /* 双精度旋转框样式 */
            QDoubleSpinBox {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #b3d1e6;
                border-radius: 6px;
                padding: 4px 8px;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
            }
            
            QDoubleSpinBox:hover {
                border-color: #4a90e2;
            }
            
            /* 分割器样式 */
            QSplitter::handle:horizontal {
                background-color: #b3d1e6;
                width: 6px;
                border-radius: 3px;
                margin: 5px 0;
            }
            
            QSplitter::handle:horizontal:hover {
                background-color: #4a90e2;
            }
            
            QSplitter::handle:vertical {
                background-color: #b3d1e6;
                height: 6px;
                border-radius: 3px;
                margin: 0 5px;
            }
            
            QSplitter::handle:vertical:hover {
                background-color: #4a90e2;
            }
            
            /* 毛玻璃效果（Windows系统支持） */
            QWidget#centralwidget {
                background-color: #e6f3ff;
                background-image: url('');
            }
        """)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建顶部按钮和参数设置区域
        top_layout = QVBoxLayout()
        
        # 创建按钮行
        buttons_layout = QHBoxLayout()
        
        # 创建选择图片按钮
        self.select_image_button = QPushButton('选择图片文件')
        self.select_image_button.setMinimumHeight(35)
        self.select_image_button.clicked.connect(self.select_image)
        # 模型自动加载，所以可以直接启用选择图片按钮
        self.select_image_button.setEnabled(True)
        
        # 创建选择文件夹按钮
        self.select_folder_button = QPushButton('选择图片文件夹')
        self.select_folder_button.setMinimumHeight(35)
        self.select_folder_button.clicked.connect(self.select_folder)
        self.select_folder_button.setEnabled(True)
        
        # 创建模型信息标签
        self.model_info_label = QLabel('使用默认模型: testflowers.pt')
        self.model_info_label.setAlignment(Qt.AlignCenter)
        self.model_info_label.setStyleSheet('color: #336699; font-weight: bold; padding: 8px; background-color: rgba(255, 255, 255, 0.8); border-radius: 8px;')
        
        # 创建识别按钮
        self.recognize_button = QPushButton('开始识别')
        self.recognize_button.setMinimumHeight(35)
        self.recognize_button.clicked.connect(self.start_recognition)
        self.recognize_button.setEnabled(False)  # 初始禁用，等待模型和图片都准备好
        
        # 创建分类按钮
        self.classify_button = QPushButton('分类')
        self.classify_button.setMinimumHeight(35)
        self.classify_button.clicked.connect(self.open_classification_album)
        self.classify_button.setEnabled(False)
        
        # 创建重置按钮
        self.reset_button = QPushButton('重置')
        self.reset_button.setMinimumHeight(35)
        self.reset_button.clicked.connect(self.reset_all)
        
        # 添加按钮和标签到布局
        buttons_layout.addWidget(self.model_info_label)
        buttons_layout.addWidget(self.select_image_button)
        buttons_layout.addWidget(self.select_folder_button)
        buttons_layout.addWidget(self.recognize_button)
        
        # 创建一键识别按钮
        self.batch_recognize_button = QPushButton('一键识别所有图片')
        self.batch_recognize_button.setMinimumHeight(35)
        self.batch_recognize_button.clicked.connect(self.batch_recognize_all)
        self.batch_recognize_button.setEnabled(False)
        buttons_layout.addWidget(self.batch_recognize_button)
        
        buttons_layout.addWidget(self.classify_button)
        buttons_layout.addWidget(self.reset_button)
        
        # 创建参数设置布局
        params_group = QGroupBox('识别参数设置')
        params_layout = QGridLayout(params_group)
        
        # 创建置信度阈值滑块
        params_layout.addWidget(QLabel('置信度阈值:'), 0, 0)
        self.conf_spin = QDoubleSpinBox()
        self.conf_spin.setMinimum(0.01)
        self.conf_spin.setMaximum(1.0)
        self.conf_spin.setValue(0.25)
        self.conf_spin.setSingleStep(0.01)
        self.conf_spin.setSuffix(' (推荐: 0.25-0.5)')
        params_layout.addWidget(self.conf_spin, 0, 1)
        
        # 创建IoU阈值滑块
        params_layout.addWidget(QLabel('IoU阈值:'), 1, 0)
        self.iou_spin = QDoubleSpinBox()
        self.iou_spin.setMinimum(0.01)
        self.iou_spin.setMaximum(1.0)
        self.iou_spin.setValue(0.45)
        self.iou_spin.setSingleStep(0.01)
        self.iou_spin.setSuffix(' (推荐: 0.4-0.6)')
        params_layout.addWidget(self.iou_spin, 1, 1)
        
        # 添加按钮布局和参数设置到顶部布局
        top_layout.addLayout(buttons_layout)
        top_layout.addWidget(params_group)
        
        # 添加顶部布局到主布局
        main_layout.addLayout(top_layout)
        
        # 创建分割器，用于水平分割左右两个部分
        splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧图片显示框架
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.Panel)
        left_frame.setFrameShadow(QFrame.Raised)
        left_layout = QVBoxLayout(left_frame)
        
        # 创建滚动区域用于显示图片
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet('background-color: rgba(255, 255, 255, 0.9); border: 1px solid #b3d1e6; border-radius: 10px; margin: 5px;')
        self.scroll_area.setMinimumHeight(400)
        
        # 创建图片显示标签
        self.image_label = QLabel('请选择图片')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet('background-color: rgba(255, 255, 255, 0.9); border-radius: 8px; padding: 10px;')
        self.image_label.setMouseTracking(True)
        self.image_label.installEventFilter(self)
        
        # 将标签放入滚动区域
        self.scroll_area.setWidget(self.image_label)
        
        # 将滚动区域添加到布局
        left_layout.addWidget(self.scroll_area)
        
        # 创建图片切换按钮
        navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton('上一张')
        self.prev_button.setMinimumHeight(30)
        self.prev_button.clicked.connect(self.prev_image)
        self.prev_button.setEnabled(False)
        
        self.next_button = QPushButton('下一张')
        self.next_button.setMinimumHeight(30)
        self.next_button.clicked.connect(self.next_image)
        self.next_button.setEnabled(False)
        
        navigation_layout.addWidget(self.prev_button)
        navigation_layout.addWidget(self.next_button)
        left_layout.addLayout(navigation_layout)
        
        # 创建图片信息标签
        self.image_info = QLabel('')
        self.image_info.setAlignment(Qt.AlignCenter)
        self.image_info.setStyleSheet('color: #336699; font-size: 12px; padding: 5px; background-color: rgba(255, 255, 255, 0.7); border-radius: 6px;')
        left_layout.addWidget(self.image_info)
        
        # 创建右侧框架，用于放置EXIF信息和识别结果
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.Panel)
        right_frame.setFrameShadow(QFrame.Raised)
        right_layout = QVBoxLayout(right_frame)
        
        # 创建右侧分割器，用于垂直分割EXIF信息和识别结果
        right_splitter = QSplitter(Qt.Vertical)
        
        # 创建EXIF信息框架
        exif_frame = QFrame()
        exif_frame.setFrameShape(QFrame.Panel)
        exif_frame.setFrameShadow(QFrame.Raised)
        exif_layout = QVBoxLayout(exif_frame)
        
        # 添加EXIF信息标题
        exif_label = QLabel('图片EXIF信息')
        exif_label.setStyleSheet('font-weight: bold; padding: 5px; color: #336699; background-color: rgba(255, 255, 255, 0.7); border-radius: 6px;')
        exif_layout.addWidget(exif_label)
        
        # 创建EXIF信息文本框
        self.exif_text = QTextEdit()
        self.exif_text.setReadOnly(True)
        self.exif_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.exif_text.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        exif_layout.addWidget(self.exif_text)
        
        # 创建识别结果框架
        results_frame = QFrame()
        results_frame.setFrameShape(QFrame.Panel)
        results_frame.setFrameShadow(QFrame.Raised)
        results_layout = QVBoxLayout(results_frame)
        
        # 添加识别结果标题
        results_label = QLabel('识别结果')
        results_label.setStyleSheet('font-weight: bold; padding: 5px; color: #336699; background-color: rgba(255, 255, 255, 0.7); border-radius: 6px;')
        results_layout.addWidget(results_label)
        
        # 创建加载状态标签
        self.loading_label = QLabel('')
        self.loading_label.setVisible(False)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet('color: #0066cc; font-style: italic; padding: 5px; background-color: rgba(255, 255, 255, 0.7); border-radius: 6px;')
        
        # 创建识别结果文本框
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.results_text.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        
        # 创建加载状态标签
        self.loading_label = QLabel('')
        self.loading_label.setVisible(False)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet('color: #0066cc; font-style: italic; padding: 5px; background-color: rgba(255, 255, 255, 0.7); border-radius: 6px;')
        
        # 添加到识别结果布局
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
        """重定向控制台输出到文本框"""
        # 创建自定义输出流类
        class ConsoleRedirector:
            def __init__(self, parent):
                self.parent = parent
                self.buffer = ""
            
            def write(self, text):
                # 确保在主线程更新UI
                QApplication.instance().postEvent(self.parent, 
                    QEvent(QEvent.User), Qt.HighEventPriority)
                self.buffer += text
            
            def flush(self):
                pass
        
        # 重定向标准输出和错误
        self.console = ConsoleRedirector(self)
        sys.stdout = self.console
        sys.stderr = self.console
        
        # 添加事件过滤器来处理重定向的输出
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """处理重定向的控制台输出和图片标签的滚轮事件"""
        if event.type() == QEvent.User and obj is self:
            if hasattr(self.console, 'buffer') and self.console.buffer:
                self.results_text.insertPlainText(self.console.buffer)
                self.results_text.ensureCursorVisible()
                self.console.buffer = ""
            return True
        elif obj is self.image_label and event.type() == QEvent.Wheel:
            # 处理滚轮缩放事件
            if self.original_pixmap:
                # 滚轮向前滚动，放大图片
                if event.angleDelta().y() > 0:
                    self.zoom_factor *= 1.1
                # 滚轮向后滚动，缩小图片
                else:
                    self.zoom_factor *= 0.9
                
                # 设置缩放范围
                self.zoom_factor = max(0.1, min(self.zoom_factor, 3.0))
                
                # 应用缩放 - 缩放图片但保持滚动区域大小固定
                scaled_size = self.original_pixmap.size() * self.zoom_factor
                scaled_pixmap = self.original_pixmap.scaled(
                    scaled_size, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                # 设置pixmap，通过滚动区域来处理大图片的显示
                self.image_label.setPixmap(scaled_pixmap)
                # 确保图片标签根据内容大小调整
                self.image_label.adjustSize()
                
                # 更新图片信息，显示缩放比例
                if self.current_image_path and hasattr(self, 'image_info'):
                    img = cv2.imread(self.current_image_path)
                    if img is not None:
                        h, w = img.shape[:2]
                        scaled_w = int(w * self.zoom_factor)
                        scaled_h = int(h * self.zoom_factor)
                        self.image_info.setText(
                            f"图片尺寸: {w}×{h} | 缩放: {self.zoom_factor:.1%} ({scaled_w}×{scaled_h})"
                        )
                return True
        return super().eventFilter(obj, event)
    
    def redirect_to_results(self):
        """重定向输出到结果文本框"""
        # 这个方法用于确保输出重定向到结果文本框
        pass  # 实际上，重定向已经在初始化时设置好了
    
    def select_model(self):
        """使用默认模型文件"""
        # 直接使用默认模型，不允许用户选择
        QMessageBox.information(self, '提示', '系统已配置为使用默认模型文件，无需手动选择。')
    
    
    def select_image(self):
        """选择图片文件（支持多选）"""
        # 打开文件对话框选择图片（支持多选）
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, '选择图片文件', '', 
            '图片文件 (*.jpg *.jpeg *.png *.bmp *.gif);;所有文件 (*)')
        
        self._update_image_paths(file_paths)
    
    def select_folder(self):
        """选择文件夹，导入其中所有图片"""
        # 打开文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self, '选择图片文件夹', '', 
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        
        if folder_path:
            # 收集文件夹中所有支持的图片文件
            supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
            file_paths = []
            
            try:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if any(file.lower().endswith(fmt) for fmt in supported_formats):
                            file_paths.append(os.path.join(root, file))
                
                # 按文件名排序
                file_paths.sort()
                self._update_image_paths(file_paths)
            except Exception as e:
                QMessageBox.warning(self, '警告', f'读取文件夹失败: {str(e)}')
    
    def _update_image_paths(self, file_paths):
        """更新图片路径列表并刷新UI状态"""
        if file_paths:
            self.image_paths = file_paths
            self.current_image_index = 0
            self.current_image_path = file_paths[0]
            
            # 显示图片预览
            self.display_image_preview(file_paths[0])
            
            # 启用识别按钮和一键识别按钮
            self.recognize_button.setEnabled(True)
            self.batch_recognize_button.setEnabled(True)
            
            # 启用图片切换按钮
            self.prev_button.setEnabled(len(file_paths) > 1)
            self.next_button.setEnabled(len(file_paths) > 1)
            
            # 处理EXIF信息
            self.process_exif_data(file_paths[0])
            
            # 显示选中的图片数量
            self.statusBar().showMessage(f'已选择 {len(file_paths)} 张图片，当前显示第 {self.current_image_index + 1} 张')
        else:
            # 重置状态当没有选择图片时
            self.image_paths = []
            self.current_image_index = -1
            self.current_image_path = None
            self.recognize_button.setEnabled(False)
            self.batch_recognize_button.setEnabled(False)
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.classify_button.setEnabled(False)
            
            # 清除显示内容
            self.results_text.clear()
            self.image_info.clear()
            self.image_label.setText('请选择图片')
            self.loading_label.setVisible(False)
    
    def display_image_preview(self, file_path):
        """显示图片预览"""
        try:
            # 重置缩放因子
            self.zoom_factor = 1.0
            
            # 读取图片信息
            img = cv2.imread(file_path)
            h, w = img.shape[:2]
            
            # 更新图片信息标签
            self.image_info.setText(f"图片尺寸: {w}×{h}")
            
            # 创建QPixmap并保存原始尺寸
            self.original_pixmap = QPixmap(file_path)
            # 初始显示时，根据滚动区域的大小缩放图片
            viewport_size = self.scroll_area.viewport().size()
            scaled_pixmap = self.original_pixmap.scaled(
                viewport_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            # 设置pixmap
            self.image_label.setPixmap(scaled_pixmap)
            # 确保图片标签根据内容大小调整
            self.image_label.adjustSize()
            
        except Exception as e:
            QMessageBox.warning(self, '警告', f'无法显示图片: {str(e)}')
    
    def process_exif_data(self, file_path):
        """处理图片EXIF信息"""
        # 检查是否有正在运行的线程，如果有则停止
        if self.exif_thread is not None and self.exif_thread.isRunning():
            self.exif_thread.terminate()
            self.exif_thread.wait()
        
        # 清空之前的EXIF内容
        self.exif_text.clear()
        
        # 创建并启动EXIF处理线程
        self.exif_thread = ExifProcessThread(self.exif_reader, file_path)
        self.exif_thread.finished.connect(self.on_exif_processed)
        self.exif_thread.error.connect(self.on_exif_error)
        self.exif_thread.start()
    
    def on_exif_processed(self):
        """EXIF处理完成后的回调"""
        try:
            # 组合各种EXIF信息
            device_info = self.exif_reader.get_device_info()
            image_info = self.exif_reader.get_image_info()
            location_info = self.exif_reader.get_location_info()
            
            # 格式化输出
            formatted_info = "===== EXIF信息 =====\n\n"
            
            # 添加设备信息
            if device_info:
                formatted_info += "设备信息:\n"
                for key, value in device_info.items():
                    formatted_info += f"  {key}: {value}\n"
                formatted_info += "\n"
            
            # 添加图像信息
            if image_info:
                formatted_info += "图像信息:\n"
                for key, value in image_info.items():
                    formatted_info += f"  {key}: {value}\n"
                formatted_info += "\n"
            
            # 添加位置信息
            if location_info:
                formatted_info += "位置信息:\n"
                if location_info.get('has_location'):
                    formatted_info += f"  十进制经纬度: {location_info.get('decimal_lat', '未知')}, {location_info.get('decimal_lon', '未知')}\n"
                    formatted_info += f"  地址: {location_info.get('formatted_address', '未知')}\n"
                    
                    # 保存位置信息以便后续更新地址
                    self.current_location_info = location_info
                    
                    # 如果有经纬度但没有地址信息，启动地址查询线程
                    if location_info.get('address_info') is None:
                        self.start_address_lookup(location_info.get('decimal_lat'), 
                                                location_info.get('decimal_lon'))
                else:
                    formatted_info += f"  {location_info.get('error', '未找到位置信息')}\n"
            
            self.exif_text.setPlainText(formatted_info)
        except Exception as e:
            self.exif_text.setPlainText(f"无法获取EXIF信息: {str(e)}")
    
    def start_address_lookup(self, latitude, longitude):
        """启动地址查询线程"""
        # 显示加载标签
        self.loading_label.setVisible(True)
        self.loading_label.setText("正在获取地址信息...")
        
        # 检查是否有正在运行的地址查询线程，如果有则停止
        if hasattr(self, 'address_thread') and self.address_thread is not None and self.address_thread.isRunning():
            self.address_thread.terminate()
            self.address_thread.wait()
        
        # 创建并启动地址查询线程
        from tool.flower_vision_threads import AddressLookupThread
        self.address_thread = AddressLookupThread(self.exif_reader, latitude, longitude)
        self.address_thread.finished.connect(self.on_address_lookup_finished)
        self.address_thread.error.connect(self.on_address_lookup_error)
        self.address_thread.progress.connect(self.update_loading_label)
        self.address_thread.start()
    
    def on_address_lookup_finished(self, address_info):
        """地址查询完成后的回调"""
        try:
            # 更新当前位置信息的地址部分
            if hasattr(self, 'current_location_info'):
                self.current_location_info['address_info'] = address_info
                self.current_location_info['formatted_address'] = self.exif_reader.format_address(address_info) if address_info else "无法获取地址信息"
                
                # 如果当前图片已在processed_images中，更新位置信息
                if self.current_image_path and self.current_image_path in self.processed_images:
                    self.processed_images[self.current_image_path]['location'] = self.current_location_info['formatted_address']
                
                # 更新EXIF文本显示
                self.refresh_exif_display()
        
        # 隐藏加载标签
            self.loading_label.setVisible(False)
        except Exception as e:
            print(f"更新地址信息时出错: {str(e)}")
            self.loading_label.setVisible(False)
    
    def on_address_lookup_error(self, error_msg):
        """地址查询出错的回调"""
        print(f"地址查询错误: {error_msg}")
        # 隐藏加载标签
        self.loading_label.setVisible(False)
    
    def update_loading_label(self, message):
        """更新加载标签的显示"""
        self.loading_label.setText(message)
    
    def refresh_exif_display(self):
        """刷新EXIF信息显示"""
        try:
            # 重新获取最新的EXIF信息
            device_info = self.exif_reader.get_device_info()
            image_info = self.exif_reader.get_image_info()
            location_info = getattr(self, 'current_location_info', self.exif_reader.get_location_info())
            
            # 格式化输出
            formatted_info = "===== EXIF信息 =====\n\n"
            
            # 添加设备信息
            if device_info:
                formatted_info += "设备信息:\n"
                for key, value in device_info.items():
                    formatted_info += f"  {key}: {value}\n"
                formatted_info += "\n"
            
            # 添加图像信息
            if image_info:
                formatted_info += "图像信息:\n"
                for key, value in image_info.items():
                    formatted_info += f"  {key}: {value}\n"
                formatted_info += "\n"
            
            # 添加位置信息
            if location_info:
                formatted_info += "位置信息:\n"
                if location_info.get('has_location'):
                    formatted_info += f"  十进制经纬度: {location_info.get('decimal_lat', '未知')}, {location_info.get('decimal_lon', '未知')}\n"
                    formatted_info += f"  地址: {location_info.get('formatted_address', '未知')}\n"
                else:
                    formatted_info += f"  {location_info.get('error', '未找到位置信息')}\n"
            
            self.exif_text.setPlainText(formatted_info)
        except Exception as e:
            self.exif_text.setPlainText(f"无法获取EXIF信息: {str(e)}")
    
    def on_exif_error(self, error_msg):
        """EXIF处理出错的回调"""
        self.exif_text.setPlainText(f"EXIF处理错误: {error_msg}")
    
    def start_recognition(self):
        """开始识别图片中的花卉"""
        if not self.image_paths or not self.flower_detector.model:
            QMessageBox.warning(self, '警告', '请先选择模型和图片')
            return
        
        # 检查是否有正在运行的线程，如果有则停止
        if self.recognition_thread is not None and self.recognition_thread.isRunning():
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
        
    def next_image(self):
        """显示下一张图片"""
        if not self.image_paths:
            return
        
        # 清除上一张图片的识别结果，但保留状态
        self.results_text.clear()
        self.recognize_button.setEnabled(True)
        self.loading_label.setVisible(False)
        # 不再清除current_image，而是在显示新图片时重新设置
        self.current_location_info = None
        
        # 更新当前图片索引和路径
        self.current_image_index = (self.current_image_index + 1) % len(self.image_paths)
        self.current_image_path = self.image_paths[self.current_image_index]
        
        # 检查图片是否已处理过
        if hasattr(self, 'processed_images') and self.current_image_path in self.processed_images:
            # 如果已处理过，重新显示带有识别框的图片
            self.classify_button.setEnabled(True)
            
            # 重新读取原图并应用识别结果
            img = cv2.imread(self.current_image_path)
            results = self.processed_images[self.current_image_path]['results']
            
            if results:
                # 可视化结果并显示
                vis_img = self.flower_detector.visualize_results(img, results, 
                                                                thickness=20, 
                                                                font_scale=2.0)
                self.display_image_with_results(vis_img)
                self.current_image = img
            else:
                # 如果没有识别结果，显示原始图片
                self.display_image_preview(self.current_image_path)
        else:
            # 如果没有处理过，显示原始图片
            self.display_image_preview(self.current_image_path)
            self.classify_button.setEnabled(False)
        
        # 处理EXIF信息
        self.process_exif_data(self.current_image_path)
        self.statusBar().showMessage(f'已选择 {len(self.image_paths)} 张图片，当前显示第 {self.current_image_index + 1} 张')
        
    def prev_image(self):
        """显示上一张图片"""
        if not self.image_paths:
            return
        
        # 清除上一张图片的识别结果，但保留状态
        self.results_text.clear()
        self.recognize_button.setEnabled(True)
        self.loading_label.setVisible(False)
        # 不再清除current_image，而是在显示新图片时重新设置
        self.current_location_info = None
        
        # 更新当前图片索引和路径
        self.current_image_index = (self.current_image_index - 1) % len(self.image_paths)
        self.current_image_path = self.image_paths[self.current_image_index]
        
        # 检查图片是否已处理过
        if hasattr(self, 'processed_images') and self.current_image_path in self.processed_images:
            # 如果已处理过，重新显示带有识别框的图片
            self.classify_button.setEnabled(True)
            
            # 重新读取原图并应用识别结果
            img = cv2.imread(self.current_image_path)
            results = self.processed_images[self.current_image_path]['results']
            
            if results:
                # 可视化结果并显示
                vis_img = self.flower_detector.visualize_results(img, results, 
                                                                thickness=20, 
                                                                font_scale=2.0)
                self.display_image_with_results(vis_img)
                self.current_image = img
            else:
                # 如果没有识别结果，显示原始图片
                self.display_image_preview(self.current_image_path)
        else:
            # 如果没有处理过，显示原始图片
            self.display_image_preview(self.current_image_path)
            self.classify_button.setEnabled(False)
        
        # 处理EXIF信息
        self.process_exif_data(self.current_image_path)
        self.statusBar().showMessage(f'已选择 {len(self.image_paths)} 张图片，当前显示第 {self.current_image_index + 1} 张')
    
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
        
        # 将识别结果保存到processed_images字典中
        if self.current_image_path:
            # 获取位置信息
            location = "未知位置"
            if hasattr(self, 'current_location_info') and self.current_location_info:
                location = self.current_location_info.get('formatted_address', '未知位置')
            
            # 存储图片处理信息
            self.processed_images[self.current_image_path] = {
                'results': results,
                'location': location,
                'timestamp': os.path.getmtime(self.current_image_path)  # 添加文件修改时间作为时间戳
            }
        
        # 如果有识别结果或处理过的图片，启用分类按钮
        if results or len(self.processed_images) > 0:
            self.classify_button.setEnabled(True)
        
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
            vis_img = self.flower_detector.visualize_results(img, results, 
                                                            thickness=20, 
                                                            font_scale=2.0)
            self.display_image_with_results(vis_img)
        else:
            print(f"⚠️  未检测到任何花卉")
            # 显示原始图片
            self.display_image_preview(self.current_image_path)
    
    def display_image_with_results(self, cv_img):
        """显示带有识别结果的图片
        
        Args:
            cv_img: OpenCV格式的图片（BGR）
        """
        # 重置缩放因子
        self.zoom_factor = 1.0
        
        # 转换OpenCV图片到Qt格式
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # 创建QPixmap并保存原始尺寸
        self.original_pixmap = QPixmap.fromImage(qt_image)
        # 初始显示时，根据滚动区域的大小缩放图片
        viewport_size = self.scroll_area.viewport().size()
        scaled_pixmap = self.original_pixmap.scaled(
            viewport_size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        # 设置pixmap
        self.image_label.setPixmap(scaled_pixmap)
        # 确保图片标签根据内容大小调整
        self.image_label.adjustSize()
        
        # 更新图片信息，显示尺寸
        if hasattr(self, 'image_info'):
            self.image_info.setText(f"图片尺寸: {w}×{h}")
    
    def on_process_error(self, error_msg):
        """处理错误信息"""
        # 隐藏加载状态
        self.loading_label.setVisible(False)
        self.recognize_button.setEnabled(True)

        
        # 显示错误信息
        QMessageBox.critical(self, '错误', f'处理出错: {error_msg}')
        print(f"❌ 处理错误: {error_msg}")
    
    def batch_recognize_all(self):
        """一键识别所有图片"""
        if not self.image_paths or not self.flower_detector.model:
            QMessageBox.warning(self, '警告', '请先选择模型和图片')
            return
        
        # 显示等待提示
        QMessageBox.information(self, '提示', f'开始批量识别 {len(self.image_paths)} 张图片，请稍候...')
        
        # 禁用按钮
        self.recognize_button.setEnabled(False)
        self.batch_recognize_button.setEnabled(False)
        self.select_image_button.setEnabled(False)
        self.select_folder_button.setEnabled(False)
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        
        # 显示加载状态
        self.loading_label.setVisible(True)
        self.loading_label.setText("正在批量识别图片...")
        
        # 开始批量识别（在单独的线程中执行）
        from PyQt5.QtCore import QThread, pyqtSignal
        
        class BatchRecognitionThread(QThread):
            finished = pyqtSignal(dict)
            progress = pyqtSignal(str)
            error = pyqtSignal(str)
            
            def __init__(self, detector, image_paths, conf_thres, iou_thres):
                super().__init__()
                self.detector = detector
                self.image_paths = image_paths
                self.conf_thres = conf_thres
                self.iou_thres = iou_thres
            
            def run(self):
                try:
                    all_results = {}
                    for i, image_path in enumerate(self.image_paths):
                        # 发送进度信息
                        self.progress.emit(f'正在识别第 {i+1}/{len(self.image_paths)} 张图片...')
                        
                        # 使用指定的阈值参数进行识别
                        results, img = self.detector.recognize(
                            image_path,
                            conf_thres=self.conf_thres,
                            iou_thres=self.iou_thres
                        )
                        
                        # 保存识别结果
                        all_results[image_path] = {
                            'results': results,
                            'image': img
                        }
                    self.finished.emit(all_results)
                except Exception as e:
                    self.error.emit(str(e))
                    self.finished.emit({})
        
        # 获取参数
        conf_thres = self.conf_spin.value()
        iou_thres = self.iou_spin.value()
        
        # 创建并启动批量识别线程
        self.batch_thread = BatchRecognitionThread(
            self.flower_detector,
            self.image_paths,
            conf_thres,
            iou_thres
        )
        # 连接信号
        self.batch_thread.finished.connect(self.on_batch_recognition_finished)
        self.batch_thread.progress.connect(self.update_progress)
        self.batch_thread.error.connect(lambda error_msg: QMessageBox.warning(self, '错误', f'批量识别失败: {error_msg}'))
        
        # 启动线程
        self.batch_thread.start()
    
    def on_batch_recognition_finished(self, all_results):
        """批量识别完成处理"""
        # 隐藏加载状态
        self.loading_label.setVisible(False)
        
        # 保存所有识别结果到processed_images字典，并获取每张图片的地理信息
        geo_count = 0
        location_tasks = []  # 存储需要查询地址的任务
        
        for image_path, result_data in all_results.items():
            # 获取EXIF地理信息
            location_info = None
            try:
                # 创建临时的ExifReader实例处理每张图片
                temp_reader = ExifReader()
                if temp_reader.process_image(image_path):
                    location_info = temp_reader.get_location_info()
                    if location_info and location_info.get('has_location', False):
                        geo_count += 1
                        # 对于有地理位置的图片，保存reader和路径信息，稍后查询地址
                        if location_info.get('address_info') is None:
                            location_tasks.append((temp_reader, image_path, location_info))
            except Exception as e:
                print(f"处理 {image_path} 的地理信息时出错: {e}")
            
            # 提取地址字符串，与普通识别时格式保持一致
            location_str = "未知位置"
            if location_info and location_info.get('has_location', False):
                location_str = location_info.get('formatted_address', '地址信息获取中...')
                
            # 保存识别结果和地理信息
            self.processed_images[image_path] = {
                'results': result_data['results'],
                'image': result_data['image'],
                'location': location_str,  # 保存字符串格式的地址信息
                'location_info': location_info  # 保存完整的location_info对象，便于后续更新
            }
        
        # 处理地址查询任务
        if location_tasks:
            # 创建地址查询线程
            class AddressLookupBatchThread(QThread):
                progress = pyqtSignal(str)
                finished = pyqtSignal(list)
                
                def __init__(self, location_tasks):
                    super().__init__()
                    self.location_tasks = location_tasks
                
                def run(self):
                    results = []
                    for i, (reader, img_path, loc_info) in enumerate(self.location_tasks):
                        try:
                            # 发送进度更新
                            self.progress.emit(f"正在获取地址信息 ({i+1}/{len(self.location_tasks)})...")
                            
                            # 执行地址查询
                            address_info = reader.get_address_from_coordinates(
                                loc_info['decimal_lat'], 
                                loc_info['decimal_lon']
                            )
                            
                            # 格式化地址
                            if address_info:
                                formatted_address = reader.format_address(address_info)
                                loc_info['address_info'] = address_info
                                loc_info['formatted_address'] = formatted_address
                                results.append((img_path, formatted_address, loc_info))
                        except Exception as e:
                            print(f"查询 {img_path} 的地址信息时出错: {e}")
                    
                    self.finished.emit(results)
            
            # 更新加载标签，显示地址查询进度
            self.loading_label.setVisible(True)
            self.loading_label.setText("正在获取地址信息...")
            
            # 创建并启动地址查询线程
            self.address_thread = AddressLookupBatchThread(location_tasks)
            self.address_thread.progress.connect(self.update_progress)
            self.address_thread.finished.connect(self.on_address_lookup_batch_finished)
            self.address_thread.start()
        else:
            # 如果没有地址查询任务，直接启用按钮
            self.recognize_button.setEnabled(True)
            self.batch_recognize_button.setEnabled(True)
            self.select_image_button.setEnabled(True)
            self.select_folder_button.setEnabled(True)
            self.prev_button.setEnabled(len(self.image_paths) > 1)
            self.next_button.setEnabled(len(self.image_paths) > 1)
            
            # 如果当前有选中的图片且已处理，启用分类按钮
            if self.current_image_path and self.current_image_path in self.processed_images:
                self.classify_button.setEnabled(True)
        
    def on_address_lookup_batch_finished(self, results):
        """批量地址查询完成后的回调"""
        # 更新地址信息
        for img_path, formatted_address, loc_info in results:
            if img_path in self.processed_images:
                self.processed_images[img_path]['location'] = formatted_address
                self.processed_images[img_path]['location_info'] = loc_info
        
        # 隐藏加载标签
        self.loading_label.setVisible(False)
        
        # 启用按钮
        self.recognize_button.setEnabled(True)
        self.batch_recognize_button.setEnabled(True)
        self.select_image_button.setEnabled(True)
        self.select_folder_button.setEnabled(True)
        self.prev_button.setEnabled(len(self.image_paths) > 1)
        self.next_button.setEnabled(len(self.image_paths) > 1)
        
        # 如果当前有选中的图片且已处理，启用分类按钮
        if self.current_image_path and self.current_image_path in self.processed_images:
            self.classify_button.setEnabled(True)
        
        # 统计地理信息
        geo_count = 0
        address_found_count = len(results)
        for img_path, data in self.processed_images.items():
            if 'location_info' in data and data['location_info']:
                geo_count += 1
        
        # 显示完成提示，包含地理信息统计
        QMessageBox.information(self, '完成', 
                               f'已成功识别 {len(self.processed_images)} 张图片！\n' 
                               f'其中 {geo_count} 张图片包含地理信息，' 
                               f'{address_found_count} 张成功获取到地址信息。')
    
    def reset_all(self):
        """重置所有状态"""
        # 停止所有线程
        if self.recognition_thread and self.recognition_thread.isRunning():
            self.recognition_thread.terminate()
            self.recognition_thread.wait()
            
        if self.exif_thread and self.exif_thread.isRunning():
            self.exif_thread.terminate()
            self.exif_thread.wait()
            
        # 重置模型相关
        if self.flower_detector:
            self.flower_detector.model = None
            
        # 重置按钮状态
        self.select_image_button.setEnabled(False)
        self.recognize_button.setEnabled(False)
        
        # 重置图片显示状态
        self.image_label.clear()
        self.image_label.setText('请选择图片')
        self.image_info.setText('图片尺寸: -')
        self.results_text.clear()
        self.current_image_path = None
        self.current_image = None
        self.current_location_info = None
        self.processed_images = {}
        self.image_paths = []
        self.current_image_index = -1
        
        # 重置缩放相关变量
        self.zoom_factor = 1.0
        self.original_pixmap = None
        self.classify_button.setEnabled(False)
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        
        # 重置变量
        self.image_paths = []
        self.current_image_index = -1
        self.current_image_path = None
        self.current_image = None
        self.current_location_info = None
        self.processed_images = {}  # 清空已处理图片数据
        
        # 重置UI
        self.image_label.setText('请选择图片')
        self.results_text.clear()
        self.exif_text.clear()
        
        # 隐藏加载标签
        self.loading_label.setVisible(False)
        
        # 清空状态栏消息
        self.statusBar().clearMessage()
        
        print("✅ 已重置所有状态")
    
    def closeEvent(self, event):
        """关闭窗口时的处理"""
        # 停止所有可能运行的线程
        if self.recognition_thread and self.recognition_thread.isRunning():
            self.recognition_thread.terminate()
            self.recognition_thread.wait()
        
        if self.exif_thread and self.exif_thread.isRunning():
            self.exif_thread.terminate()
            self.exif_thread.wait()
        
        # 恢复标准输出
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        
        event.accept()
    
    def open_classification_album(self):
        """打开分类相册窗口"""
        try:
            # 确保processed_images属性存在
            if not hasattr(self, 'processed_images'):
                self.processed_images = {}
                QMessageBox.information(self, '提示', '没有可分类的图片数据，请先进行识别。')
                return
            
            # 从processed_images字典中收集所有已处理图片的数据
            classified_data = {}
            
            # 遍历所有已处理的图片
            for img_path, img_data in self.processed_images.items():
                try:
                    results = img_data.get('results', [])
                    location = img_data.get('location', '未知位置')
                    
                    # 如果有识别结果，添加到分类数据中
                    if results:
                        # 使用集合来跟踪每个分类中已经添加的图片路径，避免重复
                        added_images_per_flower = {}
                        
                        for result in results:
                            flower_name = result.get('flower', '未知花卉')
                            # 初始化花卉分类和已添加图片集合
                            if flower_name not in classified_data:
                                classified_data[flower_name] = []
                                added_images_per_flower[flower_name] = set()
                            elif flower_name not in added_images_per_flower:
                                added_images_per_flower[flower_name] = set()
                            
                            # 检查图片是否已添加到该花卉分类中
                            if img_path not in added_images_per_flower[flower_name]:
                                # 添加图片信息到对应花卉类别
                                classified_data[flower_name].append({
                                    'path': img_path,
                                    'location': location,
                                    'confidence': result.get('confidence', 0)
                                })
                                # 记录已添加的图片路径
                                added_images_per_flower[flower_name].add(img_path)
                except Exception as e:
                    print(f"处理图片数据时出错 {img_path}: {str(e)}")
                    continue
            
            # 如果没有分类数据，尝试使用当前图片的结果
            if not classified_data and self.current_image_path and hasattr(self, 'current_image'):
                try:
                    # 从结果文本中提取识别结果
                    results_text = self.results_text.toPlainText()
                    recognized_flowers = []
                    
                    # 简单的文本解析，提取花卉名称
                    for line in results_text.split('\n'):
                        # 查找包含花卉名称的行（通常包含置信度百分比）
                        if ']' in line and '%' in line:
                            # 尝试从行中提取花卉名称
                            parts = line.split(']')
                            if len(parts) > 1:
                                flower_name = parts[1].strip()
                                # 避免添加重复的花卉名称
                                if flower_name not in recognized_flowers:
                                    recognized_flowers.append(flower_name)
                    
                    # 如果有识别到的花卉，添加到分类数据
                    if recognized_flowers:
                        # 从EXIF信息中提取位置信息
                        location_info = self.extract_location_from_exif()
                        
                        for flower in recognized_flowers:
                            if flower not in classified_data:
                                classified_data[flower] = []
                            # 添加图片信息到对应花卉类别
                            classified_data[flower].append({
                                'path': self.current_image_path,
                                'location': location_info
                            })
                except Exception as e:
                    print(f"提取当前图片分类数据时出错: {str(e)}")
                    QMessageBox.warning(self, '警告', f'无法提取当前图片的分类数据: {str(e)}')
            
            # 检查分类数据是否为空
            if not classified_data:
                QMessageBox.information(self, '提示', '没有可分类的图片数据，请先进行识别。')
                return
            
            # 导入ClassificationAlbumDialog类
            try:
                from tool.Flower_Album import ClassificationAlbumDialog
            except ImportError as e:
                QMessageBox.critical(self, '导入错误', f'无法导入分类相册模块: {str(e)}')
                return
            
            # 打开分类相册对话框
            try:
                dialog = ClassificationAlbumDialog(classified_data, self)
                dialog.exec_()
            except Exception as e:
                QMessageBox.critical(self, '错误', f'打开分类相册对话框时出错: {str(e)}')
                print(f"打开分类相册对话框时出错: {str(e)}")
        except Exception as e:
            # 捕获所有可能的异常，确保程序不会崩溃
            QMessageBox.critical(self, '严重错误', f'打开分类相册时发生严重错误: {str(e)}')
            print(f"打开分类相册时发生严重错误: {str(e)}")
    
    def extract_location_from_exif(self):
        """从EXIF文本中提取位置信息"""
        try:
            exif_text = self.exif_text.toPlainText()
            location = "未知位置"
            
            # 简单的文本解析，提取位置信息
            for line in exif_text.split('\n'):
                if '位置:' in line:
                    location = line.split(':', 1)[1].strip()
                    break
                # 也尝试匹配地址行
                elif '地址:' in line:
                    location = line.split(':', 1)[1].strip()
                    break
            
            return location
        except Exception as e:
            print(f"提取位置信息时出错: {str(e)}")
            return "未知位置"


def main():
    """主函数"""
    app = QApplication(sys.argv)
    # 设置中文字体
    font = QFont()
    font.setFamily("SimHei")  # 设置为黑体
    app.setFont(font)
    
    # 创建并显示主窗口
    window = FlowerVisionGUI()
    window.show()
    
    # 启动应用程序的事件循环
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()