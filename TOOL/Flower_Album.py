"""
花卉相册模块
提供图片缩放显示、保存、分类管理等功能.
"""

import datetime
import os
import pathlib
import platform
import shutil

# Windows系统下的路径兼容性处理
if platform.system() == "Windows":
    _original_pure_posix_path = pathlib.PurePosixPath
    _original_posix_path = pathlib.PosixPath
    pathlib.PurePosixPath = pathlib.PureWindowsPath
    pathlib.PosixPath = pathlib.WindowsPath


class FlowerAlbum:
    """花卉相册类 管理分类后的花卉图片，支持缩放显示、保存、回收站等功能.
    """

    def __init__(self, album_root=None):
        """初始化花卉相册.

        Args:
            album_root (str, optional): 相册根目录路径
        """
        self.album_root = album_root or self._get_default_album_path()
        self.recycle_bin = os.path.join(self.album_root, ".recycle_bin")
        self.classified_data = {}
        self.deleted_items = {}

        # 创建必要的目录结构
        self._init_directories()

    def _get_default_album_path(self):
        """获取默认相册路径."""
        # 使用当前脚本所在目录作为根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        default_path = os.path.join(current_dir, "FlowerAlbum")
        # 添加调试信息，确认保存路径
        print(f"默认相册保存路径: {default_path}")
        return default_path

    def _init_directories(self):
        """初始化相册目录结构."""
        # 创建相册根目录
        os.makedirs(self.album_root, exist_ok=True)
        # 创建回收站目录
        os.makedirs(self.recycle_bin, exist_ok=True)

    def set_classified_data(self, classified_data):
        """设置分类数据.

        Args:
            classified_data (dict): 分类后的图片数据
        """
        self.classified_data = classified_data

    def save_classified_images(self, classification_type="flower"):
        """保存分类后的图片.

        Args:
            classification_type (str): 分类类型，'flower'或'location'

        Returns:
            dict: 保存结果统计
        """
        try:
            stats = {"total_saved": 0, "categories": {}, "saved_paths": {}}

            # 创建保存目录
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_root = os.path.join(self.album_root, f"{classification_type}_classification_{timestamp}")
            os.makedirs(save_root, exist_ok=True)

            # 根据分类类型处理
            if classification_type == "flower":
                # 按花卉分类保存
                for flower_name, images in self.classified_data.items():
                    # 创建花卉分类目录
                    category_dir = os.path.join(save_root, flower_name)
                    os.makedirs(category_dir, exist_ok=True)

                    # 统计该分类保存的图片数
                    category_stats = 0

                    # 保存每张图片
                    for img_info in images:
                        # 确保img_info是字典格式
                        if isinstance(img_info, dict):
                            img_path = img_info.get("path", "")
                        else:
                            # 兼容字符串路径格式
                            img_path = img_info

                        if os.path.exists(img_path):
                            img_name = os.path.basename(img_path)
                            save_path = os.path.join(category_dir, img_name)

                            # 避免文件名冲突
                            if os.path.exists(save_path):
                                base_name, ext = os.path.splitext(img_name)
                                timestamp_ms = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                                save_path = os.path.join(category_dir, f"{base_name}_{timestamp_ms}{ext}")

                            # 复制文件
                            shutil.copy2(img_path, save_path)
                            category_stats += 1

                            # 记录保存路径
                            if flower_name not in stats["saved_paths"]:
                                stats["saved_paths"][flower_name] = []
                            stats["saved_paths"][flower_name].append(save_path)

                    stats["categories"][flower_name] = category_stats
                    stats["total_saved"] += category_stats

            return stats
        except Exception as e:
            print(f"保存分类图片失败: {e!s}")
            return {"total_saved": 0, "categories": {}, "saved_paths": {}}

    def delete_image(self, image_path, permanent=False):
        """删除图片（支持临时删除到回收站）.

        Args:
            image_path (str): 图片路径
            permanent (bool): 是否永久删除

        Returns:
            bool: 删除是否成功
        """
        if not os.path.exists(image_path):
            return False

        try:
            if permanent:
                # 永久删除
                os.remove(image_path)
                return True
            else:
                # 临时删除到回收站
                img_name = os.path.basename(image_path)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                recycle_path = os.path.join(self.recycle_bin, f"{timestamp}_{img_name}")

                # 复制文件到回收站
                shutil.copy2(image_path, recycle_path)

                # 记录删除信息
                self.deleted_items[recycle_path] = {"original_path": image_path, "deleted_at": datetime.datetime.now()}

                # 删除原文件
                os.remove(image_path)
                return True
        except Exception as e:
            print(f"删除图片失败 {image_path}: {e!s}")
            return False

    def restore_from_recycle(self, recycle_path=None):
        """从回收站恢复图片.

        Args:
            recycle_path (str, optional): 回收站中的文件路径，如果为None则恢复全部

        Returns:
            dict: 恢复结果统计
        """
        stats = {"restored": 0, "failed": 0, "restored_items": []}

        try:
            # 确定要恢复的项目
            items_to_restore = []
            if recycle_path and recycle_path in self.deleted_items:
                items_to_restore = [(recycle_path, self.deleted_items[recycle_path])]
            else:
                items_to_restore = list(self.deleted_items.items())

            # 执行恢复
            for recycle_file, info in items_to_restore:
                if os.path.exists(recycle_file):
                    try:
                        original_path = info.get("original_path", "")

                        # 确保原始目录存在
                        os.makedirs(os.path.dirname(original_path), exist_ok=True)

                        # 避免文件名冲突
                        if os.path.exists(original_path):
                            base_name, ext = os.path.splitext(original_path)
                            original_path = f"{base_name}_restored{ext}"

                        # 恢复文件
                        shutil.move(recycle_file, original_path)
                        stats["restored"] += 1
                        stats["restored_items"].append({"original": info["original_path"], "restored": original_path})

                        # 从记录中移除
                        if recycle_file in self.deleted_items:
                            del self.deleted_items[recycle_file]
                    except Exception as e:
                        print(f"恢复文件失败 {recycle_file}: {e!s}")
                        stats["failed"] += 1
                else:
                    stats["failed"] += 1
                    # 清理不存在的记录
                    if recycle_file in self.deleted_items:
                        del self.deleted_items[recycle_file]
        except Exception as e:
            print(f"恢复文件过程中出错: {e!s}")
            stats["failed"] += len(items_to_restore)

        return stats

    def clear_recycle_bin(self, days=None):
        """清空回收站.

        Args:
            days (int, optional): 只删除超过指定天数的文件，如果为None则删除全部

        Returns:
            dict: 清理结果统计
        """
        stats = {"deleted": 0, "failed": 0}

        try:
            current_time = datetime.datetime.now()

            # 遍历回收站中的文件
            for recycle_file in os.listdir(self.recycle_bin):
                file_path = os.path.join(self.recycle_bin, recycle_file)
                if os.path.isfile(file_path):
                    # 检查是否需要删除
                    delete_file = True
                    if days and recycle_file in self.deleted_items:
                        deleted_time = self.deleted_items[recycle_file]["deleted_at"]
                        if (current_time - deleted_time).days < days:
                            delete_file = False

                    if delete_file:
                        try:
                            os.remove(file_path)
                            stats["deleted"] += 1
                            # 从记录中移除
                            if recycle_file in self.deleted_items:
                                del self.deleted_items[recycle_file]
                        except Exception as e:
                            print(f"删除回收站文件失败 {file_path}: {e!s}")
                            stats["failed"] += 1
        except Exception as e:
            print(f"清空回收站过程中出错: {e!s}")

        return stats

    def get_album_info(self):
        """获取相册信息.

        Returns:
            dict: 相册信息
        """
        # 统计分类数据
        category_stats = {"total_categories": len(self.classified_data), "total_images": 0, "category_details": {}}

        try:
            for category, images in self.classified_data.items():
                # 处理不同格式的图片数据
                if images and isinstance(images[0], dict):
                    # 字典格式 [{path: '', ...}]
                    valid_images = [img for img in images if os.path.exists(img.get("path", ""))]
                else:
                    # 字符串路径格式 ['path1', 'path2', ...]
                    valid_images = [img for img in images if os.path.exists(img)]

                category_stats["category_details"][category] = len(valid_images)
                category_stats["total_images"] += len(valid_images)

            # 统计回收站信息
            recycle_stats = {"total_items": len(os.listdir(self.recycle_bin)), "tracked_items": len(self.deleted_items)}
        except Exception as e:
            print(f"获取相册信息时出错: {e!s}")
            category_stats = {"total_categories": 0, "total_images": 0, "category_details": {}}
            recycle_stats = {"total_items": 0, "tracked_items": 0}

        return {
            "album_root": self.album_root,
            "recycle_bin": self.recycle_bin,
            "category_stats": category_stats,
            "recycle_stats": recycle_stats,
        }


# 相册操作辅助函数
def create_image_thumbnail(image_path, output_path, size=(200, 200)):
    """创建图片缩略图.

    Args:
        image_path (str): 原图路径
        output_path (str): 缩略图输出路径
        size (tuple): 缩略图尺寸

    Returns:
        str: 缩略图路径，失败返回None
    """
    try:
        from PIL import Image

        with Image.open(image_path) as img:
            img.thumbnail(size, Image.LANCZOS)
            img.save(output_path)

        return output_path
    except Exception as e:
        print(f"创建缩略图失败 {image_path}: {e!s}")
        return None


def resize_image(image_path, output_path, width=None, height=None, maintain_ratio=True):
    """调整图片大小.

    Args:
        image_path (str): 原图路径
        output_path (str): 输出路径
        width (int, optional): 目标宽度
        height (int, optional): 目标高度
        maintain_ratio (bool): 是否保持比例

    Returns:
        str: 调整后图片路径，失败返回None
    """
    try:
        from PIL import Image

        with Image.open(image_path) as img:
            if maintain_ratio:
                img.thumbnail((width or img.width, height or img.height), Image.LANCZOS)
            else:
                img = img.resize((width or img.width, height or img.height), Image.LANCZOS)
            img.save(output_path)

        return output_path
    except Exception as e:
        print(f"调整图片大小失败 {image_path}: {e!s}")
        return None


class ClassificationAlbum:
    """分类相册类 处理分类数据的核心逻辑，包括分类列表生成、图片筛选等功能 作为FlowerVision_GUI.py中ClassificationAlbumDialog的后端支持.
    """

    def __init__(self, flower_album=None):
        """初始化分类相册.

        Args:
            flower_album (FlowerAlbum, optional): 花卉相册实例
        """
        try:
            self.flower_album = flower_album or FlowerAlbum()
            self.classified_data = {}
            self.current_classification_type = "花卉"
            self.original_classified_data = {}  # 保存原始分类数据用于重置
        except Exception as e:
            print(f"ClassificationAlbum初始化失败: {e!s}")
            self.flower_album = FlowerAlbum()
            self.classified_data = {}
            self.current_classification_type = "花卉"
            self.original_classified_data = {}

    def set_classified_data(self, classified_data):
        """设置分类数据.

        Args:
            classified_data (dict): 分类数据，格式为 {花卉名称: [{path: 图片路径, location: 位置信息}, ...]}
        """
        try:
            # 验证数据格式
            if not isinstance(classified_data, dict):
                print("分类数据格式错误，应为字典类型")
                self.classified_data = {}
                return

            # 保存原始数据用于重置
            self.original_classified_data = classified_data.copy()
            # 验证并清理数据
            self.classified_data = {}
            for flower_name, images in classified_data.items():
                if isinstance(images, list):
                    valid_images = []
                    for img_info in images:
                        # 验证图片信息格式和路径存在性
                        if isinstance(img_info, dict) and "path" in img_info:
                            img_info["path"]
                            # 确保location字段存在
                            if "location" not in img_info:
                                img_info["location"] = "未知位置"
                            valid_images.append(img_info)
                    if valid_images:  # 只添加有有效图片的分类
                        self.classified_data[flower_name] = valid_images
        except Exception as e:
            print(f"设置分类数据失败: {e!s}")
            self.classified_data = {}

    def set_classification_type(self, classification_type):
        """设置当前分类类型.

        Args:
            classification_type (str): 分类类型，'花卉'或'地点'
        """
        try:
            if classification_type in ["花卉", "地点"]:
                self.current_classification_type = classification_type
            else:
                print(f"无效的分类类型: {classification_type}，使用默认值'花卉'")
                self.current_classification_type = "花卉"
        except Exception as e:
            print(f"设置分类类型失败: {e!s}")
            self.current_classification_type = "花卉"

    def get_category_list(self):
        """获取分类列表.

        Returns:
            list: 分类名称列表
        """
        try:
            if self.current_classification_type == "花卉":
                # 按花卉分类，返回所有有效的花卉名称
                return [
                    flower for flower in self.classified_data.keys() if self.classified_data[flower]
                ]  # 只返回有图片的花卉
            else:
                # 按地点分类，过滤临时状态
                location_dict = {}

                # 收集所有位置信息，使用子字符串匹配来过滤临时状态
                for flower_data in self.classified_data.values():
                    for img_info in flower_data:
                        if isinstance(img_info, dict) and "location" in img_info:
                            location = img_info["location"]
                            # 使用子字符串匹配，过滤掉所有包含"地址获取中"的临时状态
                            if "地址获取中" not in location:
                                if location not in location_dict:
                                    location_dict[location] = []
                                location_dict[location].append(img_info)

                return sorted(list(location_dict.keys()))  # 返回排序后的地点列表
        except Exception as e:
            print(f"获取分类列表失败: {e!s}")
            return []

    def get_images_for_category(self, category_name):
        """获取指定分类的所有图片路径.

        Args:
            category_name (str): 分类名称

        Returns:
            list: 图片路径列表
        """
        try:
            image_paths = []

            if self.current_classification_type == "花卉":
                # 获取该花卉的所有有效图片
                if category_name in self.classified_data:
                    for img_info in self.classified_data[category_name]:
                        if isinstance(img_info, dict) and "path" in img_info:
                            img_path = img_info["path"]
                            # 验证文件是否存在
                            if os.path.exists(img_path):
                                image_paths.append(img_path)
            else:
                # 获取该地点的所有有效图片
                for flower_data in self.classified_data.values():
                    for img_info in flower_data:
                        if isinstance(img_info, dict) and "location" in img_info and "path" in img_info:
                            if img_info["location"] == category_name:
                                img_path = img_info["path"]
                                # 验证文件是否存在
                                if os.path.exists(img_path):
                                    image_paths.append(img_path)

            return image_paths
        except Exception as e:
            print(f"获取分类图片失败 {category_name}: {e!s}")
            return []

    def save_classification(self, classification_type=None):
        """保存分类结果.

        Args:
            classification_type (str, optional): 分类类型，'flower'或'location'

        Returns:
            dict: 保存结果统计
        """
        try:
            if classification_type is None:
                classification_type = "flower" if self.current_classification_type == "花卉" else "location"

            # 根据当前分类类型准备数据
            if classification_type == "location":
                # 对于地点分类，使用转换后的数据
                location_data = self.get_classified_data_by_location()
                # 将location_data格式转换为FlowerAlbum期望的格式
                formatted_data = {}
                for location, images in location_data.items():
                    formatted_data[location] = images
                # 临时保存当前数据
                original_data = self.flower_album.classified_data
                # 设置转换后的地点分类数据
                self.flower_album.set_classified_data(formatted_data)
                # 保存分类
                result = self.flower_album.save_classified_images(classification_type)
                # 恢复原始数据
                self.flower_album.set_classified_data(original_data)
                return result
            else:
                # 直接调用FlowerAlbum的保存方法
                return self.flower_album.save_classified_images(classification_type)
        except Exception as e:
            print(f"保存分类失败: {e!s}")
            return {"total_saved": 0, "categories": {}, "error": str(e)}

    def delete_image(self, image_path, permanent=False):
        """删除图片.

        Args:
            image_path (str): 图片路径
            permanent (bool): 是否永久删除

        Returns:
            bool: 删除是否成功
        """
        try:
            # 先从分类数据中移除
            for flower_name, flower_data in list(self.classified_data.items()):
                self.classified_data[flower_name] = [
                    img for img in flower_data if not (isinstance(img, dict) and img.get("path") == image_path)
                ]
                # 如果分类为空，移除该分类
                if not self.classified_data[flower_name]:
                    del self.classified_data[flower_name]

            # 再调用FlowerAlbum删除实际文件
            return self.flower_album.delete_image(image_path, permanent)
        except Exception as e:
            print(f"删除图片失败 {image_path}: {e!s}")
            return False

    def get_classified_data_by_location(self):
        """获取按地点分类的数据.

        Returns:
            dict: 按地点分类的数据，格式为 {地点: [{path: 图片路径, flower: 花卉名称}, ...]}
        """
        try:
            location_dict = {}

            for flower_name, flower_data in self.classified_data.items():
                for img_info in flower_data:
                    if isinstance(img_info, dict) and "location" in img_info and "path" in img_info:
                        location = img_info["location"]
                        # 过滤临时状态和无效位置
                        if "地址获取中" not in location and location.strip():
                            if location not in location_dict:
                                location_dict[location] = []
                            location_dict[location].append(
                                {"path": img_info["path"], "flower": flower_name, "location": location}
                            )

            return location_dict
        except Exception as e:
            print(f"按地点获取分类数据失败: {e!s}")
            return {}

    def reset_to_original_data(self):
        """重置到原始分类数据.

        Returns:
            bool: 重置是否成功
        """
        try:
            if self.original_classified_data:
                self.set_classified_data(self.original_classified_data)
                return True
            return False
        except Exception as e:
            print(f"重置分类数据失败: {e!s}")
            return False

    def get_image_info(self, image_path):
        """获取图片的详细信息.

        Args:
            image_path (str): 图片路径

        Returns:
            dict or None: 图片信息字典
        """
        try:
            for flower_name, flower_data in self.classified_data.items():
                for img_info in flower_data:
                    if isinstance(img_info, dict) and img_info.get("path") == image_path:
                        return {
                            "path": image_path,
                            "flower": flower_name,
                            "location": img_info.get("location", "未知位置"),
                            **img_info,  # 包含其他可能的信息
                        }
            return None
        except Exception as e:
            print(f"获取图片信息失败 {image_path}: {e!s}")
            return None


try:
    import math

    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QFont, QImage, QPixmap
    from PyQt5.QtWidgets import (
        QComboBox,
        QDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )

    class ClassificationAlbumDialog(QDialog):
        """分类相册对话框 显示分类后的花卉图片，支持按花卉/地点分类、图片查看、删除等功能.
        """

        def __init__(self, classified_data, parent=None):
            """初始化分类相册对话框.

            Args:
                classified_data (dict): 分类数据
                parent: 父窗口
            """
            super().__init__(parent)
            self.classified_data = classified_data
            self.parent = parent
            # 使用ClassificationAlbum类处理核心逻辑
            self.classification_album = ClassificationAlbum()
            self.classification_album.set_classified_data(classified_data)
            # 确保flower_album也设置了分类数据
            self.classification_album.flower_album.set_classified_data(classified_data)

            # 初始化UI
            self.init_ui()
            # 更新分类列表
            self.update_category_list()

        def init_ui(self):
            """初始化用户界面."""
            # 设置窗口标题和大小
            self.setWindowTitle("花卉分类相册")
            self.setMinimumSize(1200, 800)

            # 设置全局样式 - 应用圆润毛玻璃风格
            self.setStyleSheet("""
                /* 对话框样式 */
                QDialog {
                    background-color: #e6f3ff;
                }
                
                /* 标签样式 */
                QLabel {
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                }
                
                /* 列表样式 */
                QListWidget {
                    background-color: rgba(255, 255, 255, 0.9);
                    border-radius: 10px;
                    border: 1px solid #b3d1e6;
                    padding: 8px;
                    margin: 5px;
                }
                QListWidget::item {
                    padding: 10px;
                    border-radius: 6px;
                    margin: 2px;
                }
                QListWidget::item:hover {
                    background-color: rgba(240, 242, 245, 0.9);
                }
                QListWidget::item:selected {
                    background-color: rgba(227, 242, 253, 0.9);
                    color: #1976d2;
                    border-radius: 6px;
                }
                
                /* 组合框样式 */
                QComboBox {
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 1px solid #b3d1e6;
                    border-radius: 6px;
                    padding: 5px 10px;
                    font-size: 14px;
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                }
                QComboBox:hover {
                    border-color: #4a90e2;
                }
                
                /* 旋转框样式 */
                QSpinBox {
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 1px solid #b3d1e6;
                    border-radius: 6px;
                    padding: 5px 10px;
                    font-size: 14px;
                    min-width: 100px;
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                }
                QSpinBox:hover {
                    border-color: #4a90e2;
                }
                
                /* 按钮样式 */
                QPushButton {
                    background-color: #4a90e2;
                    color: white;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-size: 14px;
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
                
                /* 滚动区域样式 */
                QScrollArea {
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 1px solid #b3d1e6;
                    border-radius: 10px;
                    margin: 5px;
                }
                
                /* 分割器样式 */
                QSplitter::handle {
                    background-color: #b3d1e6;
                    border-radius: 3px;
                }
                QSplitter::handle:hover {
                    background-color: #4a90e2;
                }
                
                /* 毛玻璃效果（Windows系统支持） */
                QWidget {
                    background-color: rgba(255, 255, 255, 0.8);
                }
            """)

            # 创建主布局
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(15, 15, 15, 15)
            main_layout.setSpacing(15)

            # 创建顶部标题
            title_label = QLabel("花卉分类相册")
            title_label.setStyleSheet("""
                font-size: 24px; 
                font-weight: bold; 
                color: #333;
                padding: 10px 0;
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 10px;
                text-align: center;
            """)
            main_layout.addWidget(title_label)

            # 创建分类类型选择器
            type_layout = QHBoxLayout()
            type_layout.setContentsMargins(0, 0, 0, 0)
            type_label = QLabel("分类类型:")
            type_label.setStyleSheet("""
                font-size: 14px; 
                font-weight: bold; 
                color: #4a90e2;
                padding: 5px 10px;
            """)
            type_layout.addWidget(type_label)

            self.classification_type_combo = QComboBox()
            self.classification_type_combo.addItems(["花卉", "地点"])
            self.classification_type_combo.currentTextChanged.connect(self.on_classification_type_changed)
            self.classification_type_combo.setStyleSheet("""
                QComboBox {
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 1px solid #b3d1e6;
                    border-radius: 8px;
                    padding: 8px 12px;
                    min-width: 120px;
                    font-size: 13px;
                }
                QComboBox:hover {
                    border-color: #4a90e2;
                    background-color: rgba(255, 255, 255, 1);
                }
                QComboBox::drop-down {
                    border: none;
                    background-color: rgba(74, 144, 226, 0.1);
                    border-radius: 0 8px 8px 0;
                    width: 25px;
                }
                QComboBox::down-arrow {
                    image: url(:/icons/down_arrow);
                    width: 12px;
                    height: 12px;
                    color: #4a90e2;
                }
            """)
            type_layout.addWidget(self.classification_type_combo)

            # 添加当前分类统计信息
            self.category_stats_label = QLabel("")
            self.category_stats_label.setStyleSheet("""
                color: #666; 
                font-size: 14px;
                padding: 5px 10px;
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 6px;
                border: 1px solid #e0e0e0;
            """)
            type_layout.addWidget(self.category_stats_label)

            type_layout.addStretch()
            main_layout.addLayout(type_layout)

            # 创建主分割器 - 垂直分割，让内容区域成为主体
            main_splitter = QSplitter(Qt.Vertical)
            main_splitter.setHandleWidth(5)
            main_splitter.setStyleSheet("""
                QSplitter::handle {
                    background-color: #e0e0e0;
                }
                QSplitter::handle:hover {
                    background-color: #bdbdbd;
                }
            """)

            # 上部分：内容区域 - 水平分割
            content_splitter = QSplitter(Qt.Horizontal)
            content_splitter.setHandleWidth(5)
            content_splitter.setStyleSheet("""
                QSplitter::handle {
                    background-color: #e0e0e0;
                }
                QSplitter::handle:hover {
                    background-color: #bdbdbd;
                }
            """)

            # 创建左侧分类列表 - 缩小宽度，专注于导航功能
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            left_layout.setContentsMargins(5, 5, 5, 5)
            left_layout.setSpacing(10)

            category_label = QLabel("分类列表")
            category_label.setStyleSheet("""
                font-size: 16px; 
                font-weight: bold; 
                color: #4a90e2;
                padding: 8px 10px;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
                margin-bottom: 5px;
            """)
            left_layout.addWidget(category_label)

            self.category_list = QListWidget()
            self.category_list.setMinimumWidth(180)
            self.category_list.setMaximumWidth(220)  # 缩小最大宽度，让出更多空间给图片
            self.category_list.itemClicked.connect(self.on_category_clicked)
            # 设置字体和颜色
            font = QFont()
            font.setPointSize(13)
            self.category_list.setFont(font)
            # 设置样式表
            self.category_list.setStyleSheet("""
                QListWidget {
                    background-color: rgba(255, 255, 255, 0.9);
                    border-radius: 10px;
                    border: 1px solid #b3d1e6;
                    padding: 8px;
                    margin: 5px;
                    color: #333;
                }
                QListWidget::item {
                    border-radius: 6px;
                    padding: 8px;
                    margin: 2px;
                }
                QListWidget::item:selected {
                    background-color: #4a90e2;
                    color: white;
                }
                QListWidget::item:hover:not(:selected) {
                    background-color: rgba(74, 144, 226, 0.1);
                }
            """)
            left_layout.addWidget(self.category_list)

            content_splitter.addWidget(left_widget)

            # 创建右侧内容区域
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            right_layout.setContentsMargins(0, 0, 0, 0)
            right_layout.setSpacing(10)

            # 创建当前分类标题
            self.current_category_title = QLabel("选择分类查看图片")
            self.current_category_title.setStyleSheet("""
                font-size: 18px; 
                font-weight: bold; 
                color: #333;
                padding: 8px 15px;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
                border-left: 4px solid #4a90e2;
            """)

            # 顶部控制栏 - 包含当前分类和视图控制
            top_control_layout = QHBoxLayout()
            top_control_layout.setContentsMargins(0, 0, 0, 0)
            top_control_layout.setSpacing(10)

            top_control_layout.addWidget(self.current_category_title)
            top_control_layout.addStretch()

            # 视图模式按钮移到顶部
            view_mode_label = QLabel("视图:")
            view_mode_label.setStyleSheet("""
                font-size: 14px; 
                color: #4a90e2;
                padding: 8px 10px;
                font-weight: 500;
            """)
            top_control_layout.addWidget(view_mode_label)

            self.view_mode_combo = QComboBox()
            self.view_mode_combo.addItems(["网格视图", "列表视图"])
            self.view_mode_combo.currentTextChanged.connect(self.on_view_mode_changed)
            self.view_mode_combo.setStyleSheet("""
                QComboBox {
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 1px solid #b3d1e6;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 13px;
                    color: #333;
                }
                QComboBox:hover {
                    border-color: #4a90e2;
                    background-color: rgba(255, 255, 255, 1);
                }
                QComboBox::drop-down {
                    border: none;
                    background-color: rgba(74, 144, 226, 0.1);
                    border-radius: 0 8px 8px 0;
                    width: 25px;
                }
            """)
            top_control_layout.addWidget(self.view_mode_combo)

            right_layout.addLayout(top_control_layout)

            # 创建图片显示区域 - 作为核心，占据最大空间
            self.image_scroll_area = QScrollArea()
            self.image_scroll_area.setWidgetResizable(True)
            self.image_scroll_area.setStyleSheet("""
                QScrollArea {
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 1px solid #b3d1e6;
                    border-radius: 10px;
                    margin: 5px;
                }
                QScrollBar:vertical {
                    width: 12px;
                    background-color: rgba(240, 240, 240, 0.8);
                    border-radius: 6px;
                    margin: 0 2px 0 2px;
                }
                QScrollBar::handle:vertical {
                    background-color: #4a90e2;
                    border-radius: 6px;
                    min-height: 50px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #3a7bc8;
                }
                QScrollBar:horizontal {
                    height: 12px;
                    background-color: rgba(240, 240, 240, 0.8);
                    border-radius: 6px;
                    margin: 2px 0 2px 0;
                }
                QScrollBar::handle:horizontal {
                    background-color: #4a90e2;
                    border-radius: 6px;
                    min-width: 50px;
                }
                QScrollBar::handle:horizontal:hover {
                    background-color: #3a7bc8;
                }
            """)

            # 创建图片容器
            self.image_container = QWidget()
            self.image_container.setStyleSheet(
                "background-color: rgba(255, 255, 255, 0.9); border-radius: 8px; margin: 5px;"
            )
            self.image_grid = QGridLayout(self.image_container)
            self.image_grid.setHorizontalSpacing(20)  # 增加间距
            self.image_grid.setVerticalSpacing(20)
            self.image_grid.setContentsMargins(20, 20, 20, 20)
            self.image_scroll_area.setWidget(self.image_container)

            # 添加图片显示区域到右侧布局 - 设置伸展因子为1，让它占据绝大部分空间
            right_layout.addWidget(self.image_scroll_area, 1)

            # 创建底部控制布局 - 包含缩放和操作按钮
            bottom_control_layout = QHBoxLayout()
            bottom_control_layout.setContentsMargins(0, 0, 0, 0)
            bottom_control_layout.setSpacing(15)

            # 缩放控制
            size_label = QLabel("缩略图大小:")
            size_label.setStyleSheet("""
                font-size: 14px; 
                color: #4a90e2;
                padding: 8px 10px;
                font-weight: 500;
            """)
            bottom_control_layout.addWidget(size_label)

            self.thumbnail_size_spin = QSpinBox()
            self.thumbnail_size_spin.setRange(100, 400)  # 增加最大值，允许更大的缩略图
            self.thumbnail_size_spin.setValue(200)  # 增大默认值
            self.thumbnail_size_spin.setSuffix(" px")
            self.thumbnail_size_spin.valueChanged.connect(self.on_thumbnail_size_changed)
            self.thumbnail_size_spin.setMinimumWidth(120)
            self.thumbnail_size_spin.setStyleSheet("""
                QSpinBox {
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 1px solid #b3d1e6;
                    border-radius: 8px;
                    padding: 8px 10px;
                    font-size: 13px;
                    color: #333;
                }
                QSpinBox:hover {
                    border-color: #4a90e2;
                    background-color: rgba(255, 255, 255, 1);
                }
                QSpinBox::up-button,
                QSpinBox::down-button {
                    background-color: rgba(74, 144, 226, 0.1);
                    border: none;
                    width: 20px;
                }
                QSpinBox::up-arrow,
                QSpinBox::down-arrow {
                    width: 12px;
                    height: 12px;
                    color: #4a90e2;
                }
            """)
            bottom_control_layout.addWidget(self.thumbnail_size_spin)

            # 选择统计信息
            self.selection_stats = QLabel("已选择: 0张图片")
            self.selection_stats.setStyleSheet("""
                font-size: 14px; 
                color: #666;
                padding: 8px 12px;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
                border: 1px solid #b3d1e6;
            """)
            bottom_control_layout.addWidget(self.selection_stats)

            # 添加空白区域
            bottom_control_layout.addStretch()

            # 删除选中图片按钮
            self.delete_button = QPushButton("删除选中图片")
            self.delete_button.clicked.connect(self.delete_selected_image)
            self.delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    border: none;
                    margin: 4px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff6b6b, stop:1 #f44336);
                    border: 2px solid #d32f2f;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:pressed {
                    background-color: #d32f2f;
                }
            """)
            bottom_control_layout.addWidget(self.delete_button)

            # 保存分类按钮
            self.save_button = QPushButton("保存分类")
            self.save_button.clicked.connect(self.save_classification)
            self.save_button.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    border: none;
                    margin: 4px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #66bb6a, stop:1 #4caf50);
                    border: 2px solid #388e3c;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:pressed {
                    background-color: #388e3c;
                }
            """)
            bottom_control_layout.addWidget(self.save_button)

            # 添加底部控制布局到右侧布局
            right_layout.addLayout(bottom_control_layout)

            # 添加右侧内容到内容分割器
            content_splitter.addWidget(right_widget)

            # 设置内容分割器比例 - 左侧分类栏缩小，右侧图片区域扩大
            content_splitter.setSizes([200, 1200])

            # 创建底部状态栏
            status_bar = QWidget()
            status_layout = QHBoxLayout(status_bar)
            status_layout.setContentsMargins(10, 5, 10, 5)

            self.status_label = QLabel("就绪")
            self.status_label.setStyleSheet("""
                font-size: 12px; 
                color: #666;
                padding: 5px 10px;
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 6px;
            """)
            status_layout.addWidget(self.status_label)
            status_layout.addStretch()

            # 添加内容区域和状态栏到主分割器
            main_splitter.addWidget(content_splitter)
            main_splitter.addWidget(status_bar)

            # 设置主分割器比例 - 让内容区域占据绝大部分空间
            main_splitter.setSizes([900, 30])

            # 添加主分割器到主布局
            main_layout.addWidget(main_splitter, 1)  # 设置伸展因子为1，让它占据剩余空间

            # 初始化变量
            self.current_category = None
            self.image_labels = []
            self.selected_images = set()
            self.view_mode = "网格视图"  # 默认为网格视图
            self.image_cache = {}  # 图片缓存，提高性能

        def update_category_list(self):
            """更新分类列表."""
            # 清空现有列表
            self.category_list.clear()

            # 获取分类列表
            categories = self.classification_album.get_category_list()

            # 更新统计信息
            self.category_stats_label.setText(f"共 {len(categories)} 个分类")

            # 添加分类到列表（包含图片数量）
            for category in categories:
                image_count = len(self.classification_album.get_images_for_category(category))
                item_text = f"{category} ({image_count}张)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, category)  # 存储原始分类名称
                # 设置分类项样式
                item.setToolTip(f"点击查看 {category} 的所有图片")
                self.category_list.addItem(item)

            # 自动选择第一个分类（如果有）
            if self.category_list.count() > 0:
                first_item = self.category_list.item(0)
                self.category_list.setCurrentItem(first_item)
                self.on_category_clicked(first_item)

        def on_classification_type_changed(self, classification_type):
            """分类类型改变时的处理."""
            try:
                # 设置分类类型
                self.classification_album.set_classification_type(classification_type)
                # 更新分类列表
                self.update_category_list()
                # 清空当前显示的图片
                self.clear_images()
                # 更新当前分类标题
                self.current_category_title.setText("选择分类查看图片")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"切换分类类型时出错: {e!s}")
                print(f"切换分类类型时出错: {e!s}")

        def on_category_clicked(self, item):
            """点击分类时的处理."""
            try:
                # 获取原始分类名称（不包含计数）
                self.current_category = item.data(Qt.UserRole) if item.data(Qt.UserRole) else item.text().split(" (")[0]
                # 更新当前分类标题
                self.current_category_title.setText(f"{self.current_category}")
                # 显示选中分类的图片
                self.display_images_for_category(self.current_category)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载分类图片时出错: {e!s}")
                print(f"加载分类图片时出错: {e!s}")

        def on_view_mode_changed(self, mode):
            """视图模式改变时的处理."""
            self.view_mode = mode
            if self.current_category:
                self.display_images_for_category(self.current_category)

        def display_images_for_category(self, category_name):
            """显示指定分类的图片."""
            try:
                # 清空现有图片
                self.clear_images()

                # 获取该分类的所有图片路径
                image_paths = self.classification_album.get_images_for_category(category_name)

                # 如果没有图片，显示提示信息
                if not image_paths:
                    empty_label = QLabel(f'分类 "{category_name}" 中没有图片')
                    empty_label.setAlignment(Qt.AlignCenter)
                    empty_label.setStyleSheet("font-size: 18px; color: #666; padding: 50px;")
                    self.image_grid.addWidget(empty_label, 0, 0, Qt.AlignCenter)
                    self.image_labels.append(empty_label)
                    return

                thumbnail_size = self.thumbnail_size_spin.value()

                # 根据视图模式调整布局
                if self.view_mode == "网格视图":
                    # 计算网格布局的列数
                    scroll_area_width = self.image_scroll_area.width() - 50  # 减去滚动条宽度和边距
                    cols = max(1, scroll_area_width // (thumbnail_size + 20))  # 20是间距

                    # 添加图片到网格
                    for i, img_path in enumerate(image_paths):
                        try:
                            self._add_image_to_grid(img_path, i, cols, thumbnail_size)
                        except Exception as e:
                            print(f"加载图片时出错 {img_path}: {e!s}")
                            continue
                else:  # 列表视图
                    # 列表视图中每行只显示一张图片，但显示更多信息
                    for i, img_path in enumerate(image_paths):
                        try:
                            self._add_image_to_list(img_path, i, thumbnail_size)
                        except Exception as e:
                            print(f"加载图片时出错 {img_path}: {e!s}")
                            continue
            except Exception as e:
                QMessageBox.critical(self, "错误", f"显示分类图片时出错: {e!s}")
                print(f"显示分类图片时出错: {e!s}")

        def _add_image_to_grid(self, img_path, index, cols, thumbnail_size):
            """将图片添加到网格视图."""
            row = index // cols
            col = index % cols

            # 创建图片容器
            img_container = QFrame()
            img_container.setFrameShape(QFrame.StyledPanel)
            img_container.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 8px;
                }
                QFrame:hover {
                    border-color: #2196f3;
                    background-color: #f8fbff;
                }
            """)
            img_container.setMinimumSize(thumbnail_size + 16, thumbnail_size + 40)
            img_container.setMaximumSize(thumbnail_size + 16, thumbnail_size + 40)

            # 创建图片布局
            img_layout = QVBoxLayout(img_container)
            img_layout.setContentsMargins(0, 0, 0, 0)
            img_layout.setSpacing(8)

            # 创建图片标签
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)
            img_label.setMinimumSize(thumbnail_size, thumbnail_size)
            img_label.setMaximumSize(thumbnail_size, thumbnail_size)
            img_label.setStyleSheet("background-color: #f8f9fa; border-radius: 4px;")

            # 加载并显示图片（使用缓存提高性能）
            cache_key = f"{img_path}_{thumbnail_size}"
            if cache_key in self.image_cache:
                scaled_pixmap = self.image_cache[cache_key]
                img_label.setPixmap(scaled_pixmap)
            else:
                if os.path.exists(img_path):
                    pixmap = QPixmap(img_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            thumbnail_size, thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                        img_label.setPixmap(scaled_pixmap)
                        # 保存到缓存
                        self.image_cache[cache_key] = scaled_pixmap
                    else:
                        img_label.setText("图片加载失败")
                        img_label.setStyleSheet("background-color: #ffebee; color: #c62828; font-size: 12px;")
                else:
                    img_label.setText("图片不存在")
                    img_label.setStyleSheet("background-color: #ffebee; color: #c62828; font-size: 12px;")

            # 创建文件名标签
            file_name = os.path.basename(img_path)
            name_label = QLabel(file_name)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setWordWrap(True)
            name_label.setMaximumWidth(thumbnail_size)
            name_label.setStyleSheet("font-size: 12px; color: #555;")

            # 添加到布局
            img_layout.addWidget(img_label)
            img_layout.addWidget(name_label)

            # 添加到网格
            self.image_grid.addWidget(img_container, row, col, Qt.AlignCenter)

            # 保存图片标签和路径
            self.image_labels.append((img_container, img_path, img_label))

            # 设置点击事件
            img_container.mousePressEvent = lambda event, path=img_path, label=img_container: self.on_image_clicked(
                event, path, label
            )

        def _add_image_to_list(self, img_path, index, thumbnail_size):
            """将图片添加到列表视图."""
            # 创建列表项容器
            item_container = QFrame()
            item_container.setFrameShape(QFrame.StyledPanel)
            item_container.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 10px;
                    margin-bottom: 8px;
                }
                QFrame:hover {
                    border-color: #2196f3;
                    background-color: #f8fbff;
                }
            """)

            # 创建水平布局
            item_layout = QHBoxLayout(item_container)
            item_layout.setContentsMargins(5, 5, 5, 5)
            item_layout.setSpacing(15)

            # 创建图片标签
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)
            img_label.setMinimumSize(thumbnail_size, thumbnail_size)
            img_label.setMaximumSize(thumbnail_size, thumbnail_size)
            img_label.setStyleSheet("background-color: #f8f9fa; border-radius: 4px;")

            # 加载并显示图片（使用缓存提高性能）
            cache_key = f"{img_path}_{thumbnail_size}"
            if cache_key in self.image_cache:
                scaled_pixmap = self.image_cache[cache_key]
                img_label.setPixmap(scaled_pixmap)
            else:
                if os.path.exists(img_path):
                    pixmap = QPixmap(img_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            thumbnail_size, thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                        img_label.setPixmap(scaled_pixmap)
                        # 保存到缓存
                        self.image_cache[cache_key] = scaled_pixmap
                    else:
                        img_label.setText("图片加载失败")
                        img_label.setStyleSheet("background-color: #ffebee; color: #c62828; font-size: 12px;")
                else:
                    img_label.setText("图片不存在")
                    img_label.setStyleSheet("background-color: #ffebee; color: #c62828; font-size: 12px;")

            # 创建信息容器
            info_container = QWidget()
            info_layout = QVBoxLayout(info_container)
            info_layout.setContentsMargins(0, 0, 0, 0)
            info_layout.setSpacing(5)

            # 文件名
            file_name = os.path.basename(img_path)
            name_label = QLabel(file_name)
            name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")

            # 文件路径（截断显示）
            path_label = QLabel(f"路径: {self._truncate_path(img_path, 80)}")
            path_label.setStyleSheet("font-size: 12px; color: #666;")
            path_label.setToolTip(img_path)

            # 文件信息
            try:
                file_size = os.path.getsize(img_path) / 1024  # KB
                file_time = datetime.datetime.fromtimestamp(os.path.getmtime(img_path)).strftime("%Y-%m-%d %H:%M")
                info_text = f"大小: {file_size:.2f} KB | 修改时间: {file_time}"
                info_label = QLabel(info_text)
                info_label.setStyleSheet("font-size: 12px; color: #888;")
            except:
                info_label = QLabel("无法获取文件信息")
                info_label.setStyleSheet("font-size: 12px; color: #888;")

            # 添加信息到布局
            info_layout.addWidget(name_label)
            info_layout.addWidget(path_label)
            info_layout.addWidget(info_label)
            info_layout.addStretch()

            # 添加到主布局
            item_layout.addWidget(img_label)
            item_layout.addWidget(info_container)
            item_layout.addStretch()

            # 添加到网格（列表视图在网格中每行只放一个）
            self.image_grid.addWidget(item_container, index, 0, 1, 1)

            # 保存图片标签和路径
            self.image_labels.append((item_container, img_path, img_label))

            # 设置点击事件
            item_container.mousePressEvent = lambda event, path=img_path, label=item_container: self.on_image_clicked(
                event, path, label
            )

        def _truncate_path(self, path, max_length):
            """截断路径字符串，保持可读性."""
            if len(path) <= max_length:
                return path

            # 从中间截断，保留文件名
            file_name = os.path.basename(path)
            if len(file_name) > max_length - 3:
                return file_name[: max_length - 3] + "..."

            available_length = max_length - len(file_name) - 3
            return path[: available_length // 2] + "..." + path[-(available_length // 2) :] + file_name

        def on_image_clicked(self, event, img_path, img_container):
            """点击图片时的处理."""
            try:
                # 检测是否是右键点击
                if event.button() == Qt.RightButton:
                    self._show_image_context_menu(event, img_path, img_container)
                    return

                # 切换选中状态
                if img_path in self.selected_images:
                    self.selected_images.remove(img_path)
                    # 根据视图模式设置不同的样式
                    if self.view_mode == "网格视图":
                        img_container.setStyleSheet("""
                            QFrame {
                                background-color: white;
                                border: 1px solid #e0e0e0;
                                border-radius: 8px;
                                padding: 8px;
                            }
                        """)
                    else:
                        img_container.setStyleSheet("""
                            QFrame {
                                background-color: white;
                                border: 1px solid #e0e0e0;
                                border-radius: 8px;
                                padding: 10px;
                                margin-bottom: 8px;
                            }
                        """)
                else:
                    self.selected_images.add(img_path)
                    # 设置选中样式
                    img_container.setStyleSheet("""
                        QFrame {
                            background-color: #e3f2fd;
                            border: 2px solid #1976d2;
                            border-radius: 8px;
                            padding: 8px;
                        }
                    """)
            except Exception as e:
                print(f"处理图片点击事件时出错: {e!s}")

        def _show_image_context_menu(self, event, img_path, img_container):
            """显示图片右键菜单."""
            from PyQt5.QtWidgets import QAction, QMenu

            menu = QMenu(self)

            # 查看大图动作
            view_action = QAction("查看大图", self)
            view_action.triggered.connect(lambda: self._view_image_large(img_path))
            menu.addAction(view_action)

            # 复制路径动作
            copy_path_action = QAction("复制文件路径", self)
            copy_path_action.triggered.connect(lambda: self._copy_to_clipboard(img_path))
            menu.addAction(copy_path_action)

            # 删除动作
            delete_action = QAction("删除图片", self)
            delete_action.triggered.connect(lambda: self._delete_single_image(img_path))
            menu.addAction(delete_action)

            # 显示菜单
            menu.exec_(self.mapToGlobal(event.pos()))

        def _view_image_large(self, img_path):
            """查看大图."""
            from PyQt5.QtWidgets import QDialog, QHBoxLayout, QPushButton, QVBoxLayout

            # 创建大图查看对话框
            dialog = QDialog(self)
            dialog.setWindowTitle(f"查看图片: {os.path.basename(img_path)}")
            dialog.setMinimumSize(800, 600)

            layout = QVBoxLayout(dialog)

            # 创建图片标签
            large_img_label = QLabel()
            large_img_label.setAlignment(Qt.AlignCenter)

            # 加载并显示图片
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                if not pixmap.isNull():
                    # 缩放图片以适应对话框，但保持比例
                    scaled_pixmap = pixmap.scaled(dialog.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    large_img_label.setPixmap(scaled_pixmap)
                else:
                    large_img_label.setText("图片加载失败")
            else:
                large_img_label.setText("图片不存在")

            # 添加关闭按钮
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            close_button = QPushButton("关闭")
            close_button.clicked.connect(dialog.close)
            button_layout.addWidget(close_button)

            layout.addWidget(large_img_label)
            layout.addLayout(button_layout)

            # 显示对话框
            dialog.exec_()

        def _copy_to_clipboard(self, text):
            """复制文本到剪贴板."""
            from PyQt5.QtWidgets import QApplication

            clipboard = QApplication.clipboard()
            clipboard.setText(text)

        def _delete_single_image(self, img_path):
            """删除单个图片."""
            reply = QMessageBox.question(
                self,
                "确认删除",
                f'确定要删除图片 "{os.path.basename(img_path)}" 吗？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                if self.classification_album.delete_image(img_path):
                    QMessageBox.information(self, "删除成功", "图片已成功删除")
                    # 刷新显示
                    if self.current_category:
                        self.display_images_for_category(self.current_category)
                    # 更新分类列表
                    self.update_category_list()
                else:
                    QMessageBox.warning(self, "删除失败", "图片删除失败")

        def on_thumbnail_size_changed(self, size):
            """缩略图大小改变时的处理."""
            try:
                if self.current_category:
                    # 清除缓存中与当前大小相关的图片，强制重新加载
                    size_key = f"_{size}"
                    keys_to_remove = [key for key in self.image_cache.keys() if key.endswith(size_key)]
                    for key in keys_to_remove:
                        self.image_cache.pop(key, None)

                    # 重新显示图片
                    self.display_images_for_category(self.current_category)
            except Exception as e:
                print(f"调整缩略图大小时出错: {e!s}")

        def clear_images(self):
            """清空图片显示区域."""
            try:
                # 清除所有图片标签
                for item in self.image_labels:
                    try:
                        widget = item[0] if isinstance(item, tuple) else item
                        widget.deleteLater()
                    except Exception as e:
                        print(f"删除图片标签时出错: {e!s}")
                self.image_labels.clear()
                # 清空选中图片集合
                self.selected_images.clear()

                # 清理网格布局中的所有项目
                while self.image_grid.count() > 0:
                    item = self.image_grid.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
            except Exception as e:
                print(f"清空图片时出错: {e!s}")

        def delete_selected_image(self):
            """删除选中的图片."""
            if not self.selected_images:
                QMessageBox.warning(self, "警告", "请先选择要删除的图片")
                return

            # 确认删除
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除选中的 {len(self.selected_images)} 张图片吗？\n此操作无法撤销！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                # 记录删除失败的图片数
                failed_count = 0

                # 创建进度对话框
                from PyQt5.QtWidgets import QProgressDialog

                progress = QProgressDialog("正在删除图片...", "取消", 0, len(self.selected_images), self)
                progress.setWindowTitle("删除进度")
                progress.setWindowModality(Qt.WindowModal)
                progress.show()

                # 删除选中的图片
                for i, img_path in enumerate(list(self.selected_images)):
                    if progress.wasCanceled():
                        break

                    progress.setValue(i)
                    if not self.classification_album.delete_image(img_path):
                        failed_count += 1

                progress.setValue(len(self.selected_images))

                # 显示结果
                if failed_count > 0:
                    QMessageBox.information(
                        self,
                        "删除结果",
                        f"部分图片删除失败，共 {len(self.selected_images) - failed_count} 张成功删除，{failed_count} 张删除失败",
                    )
                else:
                    QMessageBox.information(self, "删除成功", f"已成功删除 {len(self.selected_images)} 张图片")

                # 刷新显示
                self.selected_images.clear()
                if self.current_category:
                    self.display_images_for_category(self.current_category)
                # 重新获取分类数据并更新分类列表
                self.update_category_list()

        def save_classification(self):
            """保存分类结果."""
            try:
                # 获取保存目录信息（包含时间戳的具体目录）
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                classification_type = (
                    "flower" if self.classification_album.current_classification_type == "花卉" else "location"
                )
                save_root = os.path.join(
                    self.classification_album.flower_album.album_root,
                    f"{classification_type}_classification_{timestamp}",
                )

                # 保存分类
                stats = self.classification_album.save_classification()

                # 验证目录是否实际创建
                directory_created = os.path.exists(save_root)

                # 显示保存结果
                msg = "分类保存成功！\n"
                msg += f"共保存 {stats['total_saved']} 张图片\n"
                msg += f"分类数量: {len(stats['categories'])}\n"
                # 添加详细的保存路径信息
                msg += f"保存根目录: {self.classification_album.flower_album.album_root}\n"
                msg += f"实际保存位置: {save_root}\n"
                msg += f"目录创建状态: {'成功' if directory_created else '失败'}\n\n"

                if stats["total_saved"] > 0:
                    msg += "分类详情:\n"
                    for category, count in stats["categories"].items():
                        msg += f"- {category}: {count} 张\n"
                else:
                    msg += "注意：未保存任何图片，请检查是否有选中的图片或文件路径是否正确。"

                QMessageBox.information(self, "保存成功", msg)
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存分类时出错: {e!s}")

# 添加导入语句到模块级别
except ImportError:
    # 如果PyQt5未安装，提供一个简单的替代类
    class ClassificationAlbumDialog:
        """PyQt5未安装时的替代类."""

        def __init__(self, *args, **kwargs):
            print("需要安装PyQt5才能使用分类相册功能")

        def exec_(self):
            pass


if __name__ == "__main__":
    # 示例用法
    album = FlowerAlbum()
    print(f"相册初始化完成，根目录: {album.album_root}")
    print(f"相册信息: {album.get_album_info()}")

    # 分类相册示例
    classification_album = ClassificationAlbum(album)
    print("分类相册初始化完成")
