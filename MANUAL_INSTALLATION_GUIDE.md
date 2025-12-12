# 花卉识别系统手动安装和运行指南

## 环境要求

- Python 3.8 或更高版本
- PyTorch 1.8.0 或更高版本（建议安装CPU版本）
- pip 包管理工具

## 手动安装步骤

### 1. 打开命令提示符或PowerShell

在Windows系统中，按下 `Win + R` 键，输入 `cmd` 或 `powershell`，然后按回车键打开命令行窗口。

### 2. 安装主项目依赖

执行以下命令安装主项目依赖：

```bash
pip install -r "d:\BS\源码\My_yolov5-main\myTest\requirements.txt"
```

### 3. 安装前端API依赖

执行以下命令安装前端API依赖：

```bash
pip install -r "d:\BS\源码\My_yolov5-main\myTest\flower_frontend\requirements-frontend.txt"
```

## 启动系统

### 1. 启动后端API服务

在命令行中执行以下命令：

```bash
cd "d:\BS\源码\My_yolov5-main\myTest\flower_frontend"
python app.py
```

### 2. 访问前端页面

在浏览器中打开以下地址：
```
http://127.0.0.1:5000
```

## 系统功能

- ✅ 支持单张和多张图片识别
- ✅ 花卉种类识别（使用YOLOv5模型）
- ✅ 拍摄日期提取
- ✅ GPS位置信息提取和地址转换
- ✅ 相机型号信息提取

## 示例图片

系统包含示例图片，位于：
`d:\BS\源码\My_yolov5-main\myTest\Example_IMG\`

您可以使用这些图片进行测试。

## 常见问题及解决方案

### 问题1：PyTorch导入失败
**错误信息**：无法加载c10.dll或其依赖项

**解决方案**：
1. 下载并安装Visual C++ Redistributable 2019-2022 x64版本
   下载地址：https://aka.ms/vs/17/release/vc_redist.x64.exe
2. 安装完成后重新启动计算机

### 问题2：模型加载失败
**错误信息**：无法加载YOLOv5模型

**解决方案**：
1. 检查`d:\BS\源码\My_yolov5-main\myTest\testflowers.pt`模型文件是否存在
2. 确保PyTorch安装正确

### 问题3：端口5000已被占用
**解决方案**：
1. 查找占用5000端口的进程：
   ```bash
   netstat -ano | findstr :5000
   ```
2. 结束占用端口的进程：
   ```bash
   taskkill /PID <进程ID> /F
   ```

## 依赖列表

### 主项目依赖 (requirements.txt)

```
gitpython>=3.1.30
matplotlib>=3.3
numpy>=1.23.5
opencv-python>=4.1.1
pillow>=10.3.0
psutil
PyYAML>=5.3.1
requests>=2.32.2
scipy>=1.4.1
thop>=0.1.1
torch>=1.8.0
torchvision>=0.9.0
tqdm>=4.66.3
ultralytics>=8.2.64
packaging
setuptools>=70.0.0
urllib3>=2.5.0 ; python_version > "3.8"
pyqt5>=5.15.9
exifread>=2.3.2
geopy>=2.4.1
```

### 前端API依赖 (requirements-frontend.txt)

```
Flask==3.0.0
Flask-CORS==4.0.0
Pillow==10.3.0
numpy==1.26.0
opencv-python==4.8.0.74
torch>=1.8.0
torchvision>=0.9.0
gitpython>=3.1.30
PyYAML>=5.3.1
requests>=2.32.2
scipy>=1.4.1
tqdm>=4.66.3
ultralytics>=8.2.64
exifread>=3.0.0
geopy>=2.4.0
```

## 联系方式

如果您在安装或使用过程中遇到问题，请参考项目文档或联系开发人员。
